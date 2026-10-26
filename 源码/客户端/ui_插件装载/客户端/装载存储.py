'经 pluginManager 读写 profile 里的插件，并记下安装对话框'
import re
import time
from ....客户端.存储 import 创建快照存储
from uuid import uuid4
from ....启动.插件装载.注册表 import (
    官方npm注册表,
    npmmirror注册表,
    注册表网址,
    规范化注册表,
)
from ..异常 import 远程应答错误
from .净化安装输入 import 净化安装输入

__all__=[
    '注册表键','提供的注册表','镜像恢复注册表','已问镜像','是否安装待决','行键','插件装载控制',
]

官方选择={'kind':'offered','registry':None}
空闲安装={
    'open':False,
    'spec':'',
    'registries':None,
    'registry':官方选择,
    'registryOpen':False,
    'registryError':False,
    'attempts':None,
    'phase':'idle',
    'inputError':None,
    'subject':None,
    'runs':[],
    'detailsOpen':False,
    'installed':None,
    'installedVersion':None,
    'restartRequired':False,
    'failure':None,
    'approvedBuilds':[],
    'enabling':False,
}
刷新最短秒=0.4
短名前缀=re.compile(r'^dsh-(?:host-|client-)?')

def 注册表键(注册表,已解析):
    '比较用的注册表键。pnpm 自有配置代表它所命名的地址'
    网址=已解析 if 注册表 is None else 注册表
    if 网址 is None:
        return ''
    try:
        return 规范化注册表(网址)
    except Exception:
        return 网址

def 提供的注册表(注册表组):
    '对话框列出的源：Host 的第一源、回退，以及 pnpm 自有，各一次'
    提供=[]
    键列=[]
    列=[]
    if 注册表组 is not None:
        列.append(注册表组['registry'])
        for 项 in 注册表组['fallbackRegistries']:
            列.append(项)
    列.append(None)
    已解析=None if 注册表组 is None else 注册表组.get('resolved')
    for 注册表 in 列:
        键=注册表键(注册表,已解析)
        if 键 in 键列:
            continue
        提供.append(注册表)
        键列.append(键)
    return 提供

def 是否安装待决(阶段):
    '安装是否仍由 Host 拥有'
    return 阶段 in ('starting','running','cancelling','applying','unconfirmed')

def 镜像恢复注册表(安装):
    '确认过的 GitHub 连接失败后，给出已配置的大陆镜像。没有这项恢复时返回缺席'
    if 'confirmed' in 安装 and 安装['confirmed'] is not None:
        return '缺席'
    if 安装['phase']!='failed':
        return '缺席'
    失败=安装.get('failure')
    if 失败 is None or 失败.get('failedAt')!='spec-host':
        return '缺席'
    if 失败.get('kind') not in ('network','timeout'):
        return '缺席'
    主体=安装.get('subject')
    主机=None if 主体 is None else 主体.get('host')
    if not isinstance(主机,str):
        return '缺席'
    主机=主机.lower().split(':')[0]
    if 主机!='github.com' and not 主机.endswith('.github.com'):
        return '缺席'
    已解析=None if 安装.get('registries') is None else 安装['registries'].get('resolved')
    for 注册表 in 提供的注册表(安装.get('registries')):
        if 注册表键(注册表,已解析)==npmmirror注册表:
            return 注册表
    return '缺席'

def 已问镜像(安装):
    '当前选择是否已经先问 npmmirror'
    选择=安装['registry']
    网址=选择['url'].strip() if 选择['kind']=='custom' else 选择['registry']
    已解析=None if 安装.get('registries') is None else 安装['registries'].get('resolved')
    return 注册表键(网址,已解析)==npmmirror注册表

def 行键(入口标识):
    '忙碌表里一行占用的键'
    return 'row:'+入口标识

def 排序键(包):
    '人读短名，卡片不因启停改位置'
    名称=包['name']
    if 名称.startswith('@'):
        无作用域=名称[名称.find('/')+1:]
    else:
        无作用域=名称
    return 短名前缀.sub('',无作用域)

def 失败提示(错误,主体,序号):
    '抛出的失败变成提示。拒绝保留码，其余保留原文'
    if isinstance(错误,远程应答错误):
        码=错误.码
        不兼容=错误.不兼容
        原因=错误.原因
    elif isinstance(错误,Exception):
        码=None
        不兼容=None
        原因=str(错误)
    else:
        码=None
        不兼容=None
        原因=str(错误)
    提示={'kind':'failed','reason':原因,'action':主体['action'],'seq':序号}
    if 码 is not None:
        提示['code']=码
    if 不兼容 is not None:
        提示['incompatible']=不兼容
    if 'packageName' in 主体:
        提示['packageName']=主体['packageName']
    return 提示

def 结算运行表(运行表,退出码):
    '仍开放的运行记上退出码'
    结果=[]
    for 运行 in 运行表:
        if 'exitCode' in 运行:
            结果.append(运行)
        else:
            结果.append({**运行,'exitCode':退出码})
    return 结果

def 新空闲():
    '一份不与模板共享列表的空闲安装'
    下一=dict(空闲安装)
    下一['runs']=[]
    下一['approvedBuilds']=[]
    return 下一

def 再规格(安装):
    '回到规格输入。规格和注册表留下，运行结果丢掉'
    下一={
        **新空闲(),
        'open':安装['open'],
        'spec':安装['spec'],
        'registries':安装['registries'],
        'registry':安装['registry'],
    }
    主体=安装.get('subject')
    if 主体 is not None and 'selection' in 主体:
        下一['subject']=主体
    if 'mirrorRecovery' in 安装:
        下一['mirrorRecovery']=安装['mirrorRecovery']
    if 'confirmed' in 安装:
        下一['confirmed']=安装['confirmed']
    return 下一

class 插件装载控制:
    '经 pluginManager 读写 profile 的插件'
    def __init__(自身,上下文):
        '上下文提供 remote.pluginManager 与 remote.pluginInventory'
        自身.上下文=上下文
        自身.存储=创建快照存储({
            'status':'idle',
            'refreshStatus':'idle',
            'packages':[],
            'busy':[],
            'notice':None,
            'install':新空闲(),
            'confirm':None,
            'highlight':None,
        })
        自身.飞行中=False
        自身.再跑=False
        自身.代次=0
        自身.已拆除=False
        自身.有缓存=False
        自身.待确认=None
        自身.检查中止=None
        自身.请求=None
        自身.提示序号=0
        自身.分析尝试=None
        自身.注册表读取=None
        自身.临时注册表=False
        自身.注册表记忆=创建快照存储(None,{'persist':{'name':'dsh.plugin-manager.install-registry'}})

    def 取快照(自身):
        '读当前状态'
        return 自身.存储.getSnapshot()

    def 拆除(自身):
        '停止发布，并丢掉晚到的结算'
        自身.已拆除=True
        自身.注册表读取=None
        自身.请求=None
        自身.代次=自身.代次+1

    def 下一提示(自身):
        '下一条提示的序号'
        自身.提示序号=自身.提示序号+1
        return 自身.提示序号

    def 取分析(自身):
        '可选的产品埋点。没有服务时不记'
        return 自身.上下文.反射.获取服务('productAnalytics',False)

    def 注入(自身,配置账本,插件标签,解析文本):
        '构造席位登记注入的面'
        return {
            'resolveText':解析文本,
            'hooks':{
                'pluginManager':自身.存储,
                'configLedger':配置账本,
                'pluginTabs':插件标签,
                'configurations':自身.上下文.configForms.describe(),
            },
            'configForm':自身.取配置表单,
            'ensure':自身.确保,
            'refresh':自身.刷新,
            'openInstall':自身.打开安装,
            'installFrom':自身.从标签安装,
            'closeInstall':自身.关闭安装,
            'editInstallSpec':自身.编辑安装规格,
            'runInstall':自身.跑安装,
            'toggleRegistryOptions':自身.切换注册表选项,
            'chooseRegistry':自身.选择注册表,
            'changeRegistry':自身.更换注册表,
            'useGithubMirror':自身.改用镜像,
            'approveBuildsAndRetry':自身.允许构建并重试,
            'cancelInstall':自身.取消安装,
            'reconcileInstall':自身.核对安装,
            'toggleInstallDetails':自身.切换安装详情,
            'enableInstalled':自身.启用已安装,
            'clearHighlight':自身.清高亮,
            'setEnabled':自身.设启用,
            'update':自身.更新,
            'uninstall':自身.卸载,
            'confirm':自身.确认,
            'cancelConfirm':自身.取消确认,
            'setRowEnabled':自身.设行启用,
            'dismissNotice':自身.关掉提示,
        }

    def 取配置表单(自身,入口标识):
        '按 Host 入口取配置表单'
        return 自身.上下文.configForms.get(入口标识)

    def 确保(自身):
        '标签首次渲染时读 Host'
        if 自身.取快照()['status']=='idle':
            自身.加载()

    def 刷新(自身):
        '手动再读。转圈至少停 400 毫秒，不清已有卡片'
        if 自身.已拆除 or 自身.取快照()['refreshStatus']=='refreshing':
            return
        开始=time.time()
        补丁={'refreshStatus':'refreshing'}
        提示=自身.取快照().get('notice')
        if 提示 is not None and 提示.get('kind')=='refresh-failed':
            补丁['notice']=None
        自身.补丁(补丁)
        try:
            自身.加载()
        except Exception:
            自身.补丁({'status':'error'})
        finally:
            剩余=刷新最短秒-(time.time()-开始)
            if 剩余>0:
                time.sleep(剩余)
            自身.结算刷新()

    def 打开安装(自身):
        '记下添加按钮，并打开安装对话框'
        分析=自身.取分析()
        if 分析 is not None:
            分析.track('plugin_add_button_click',{})
        自身.打开对话框()

    def 从标签安装(自身,目标):
        '用别处确认过的版本打开对话框并开始检查。这次的源不记住'
        if 自身.打开对话框() is not True:
            return
        自身.临时注册表='registry' in 目标 and 目标['registry'] is not None
        补丁={'spec':目标['spec'],'confirmed':{'title':目标['title'],'version':目标['version']}}
        if 'registry' in 目标 and 目标['registry'] is not None:
            补丁['registry']={'kind':'custom','url':目标['registry']}
        自身.补丁安装(补丁)
        自身.跑安装()

    def 关闭安装(自身):
        '立刻藏起。检查中则丢掉。Host 拥有的安装改为取消'
        阶段=自身.取快照()['install']['phase']
        if 是否安装待决(阶段):
            自身.补丁安装({'open':False})
            自身.取消安装()
            return
        if 阶段=='checking':
            自身.结束分析('cancelled')
        自身.中止检查()
        自身.注册表读取=None
        自身.补丁({'install':新空闲()})

    def 编辑安装规格(自身,文本):
        '检查或安装中不能改。有结果之后改字等于重新开始'
        安装=自身.取快照()['install']
        if 安装['phase']=='checking' or 是否安装待决(安装['phase']):
            return
        if 安装['phase']=='idle':
            自身.补丁安装({'spec':文本,'inputError':None,'subject':None})
            return
        下一=再规格(安装)
        下一['spec']=文本
        下一['subject']=None
        自身.补丁({'install':下一})

    def 切换注册表选项(自身):
        '折叠或展开注册表选项'
        安装=自身.取快照()['install']
        自身.补丁安装({'registryOpen':安装['registryOpen'] is not True})

    def 选择注册表(自身,选择):
        '指定这次先问的源，或自己填一个'
        if 自身.取快照()['install']['phase']!='idle':
            return
        自身.临时注册表=False
        自身.补丁安装({'registry':选择,'registryError':False})

    def 更换注册表(自身):
        '失败屏回到规格，并展开注册表选项'
        安装=自身.取快照()['install']
        if 安装['phase']=='failed':
            下一=再规格(安装)
            下一['registryOpen']=True
            自身.补丁({'install':下一})

    def 改用镜像(自身):
        'GitHub 连不上时回到空规格，并改问提供的大陆镜像'
        安装=自身.取快照()['install']
        镜像=镜像恢复注册表(安装)
        if 镜像=='缺席':
            return
        恢复={**再规格(安装),'spec':'','mirrorRecovery':True}
        if 已问镜像(安装):
            自身.补丁({'install':恢复})
            return
        注册表={'kind':'offered','registry':镜像}
        自身.注册表记忆.set(注册表)
        自身.补丁({'install':{**恢复,'registry':注册表}})

    def 清高亮(自身):
        '丢掉列表高亮'
        if 自身.取快照()['highlight'] is not None:
            自身.补丁({'highlight':None})

    def 设启用(自身,包名,启用):
        '把组合包放入或移出层列表。缺文件且有目标时改为安装'
        包=None
        for 项 in 自身.取快照()['packages']:
            if 项['name']==包名:
                包=项
                break
        if 启用 is True and 包 is not None and 包.get('availability')=='missing' and 包.get('installTarget') is not None:
            自身.打开目录安装(包,包['installTarget'],True)
            return
        def 动作():
            '把启停交给 Host'
            结果=自身.上下文.remote.pluginManager.setBundleEnabled(包名,启用)
            自身.已应用(结果,包名)
            if 结果.get('ok') is True and 结果['value']['application'] in ('applied','restart-required'):
                自身.记录切换(包名,启用,False)
        自身.跑(包名,{'packageName':包名,'action':'enable' if 启用 else 'disable'},动作)

    def 更新(自身,包名):
        '卸掉已安装的包，再装目录给出的版本。未安装则直接装'
        包=None
        for 项 in 自身.取快照()['packages']:
            if 项['name']==包名:
                包=项
                break
        目标=None if 包 is None else 包.get('installTarget')
        if 包 is None or 目标 is None or 包.get('availability')=='installation':
            return
        if 包.get('installed') is not True:
            自身.打开目录安装(包,目标,包['enabled'])
            return
        def 动作():
            '先卸再装。没有 HMR 时卸下会等重启'
            卸下=自身.上下文.remote.pluginManager.removeBundle(包名)
            if 卸下.get('ok') is True and 卸下['value'].get('error') is not None and 卸下['value']['error'].get('code')=='stop-profile':
                自身.打开目录安装(包,目标,包['enabled'])
                return
            自身.已应用(卸下,包名)
            自身.打开目录安装(包,目标,包['enabled'])
        自身.跑(包名,{'packageName':包名,'action':'uninstall'},动作)

    def 卸载(自身,包名):
        '先请人确认，再从 profile 移除'
        def 待做():
            '确认后执行卸载'
            def 动作():
                '记下确认并移除'
                分析=自身.取分析()
                if 分析 is not None:
                    分析.track('confirm_uninstall_plugin',{'plugin_name':包名})
                自身.已应用(自身.上下文.remote.pluginManager.removeBundle(包名),包名)
            自身.跑(包名,{'packageName':包名,'action':'uninstall'},动作)
        自身.待确认=待做
        自身.补丁({'confirm':{'action':'uninstall','packageName':包名}})

    def 确认(自身):
        '执行待确认动作'
        待做=自身.待确认
        自身.待确认=None
        自身.补丁({'confirm':None})
        if 待做 is not None:
            待做()

    def 取消确认(自身):
        '取消确认'
        自身.待确认=None
        自身.补丁({'confirm':None})

    def 设行启用(自身,入口标识,启用):
        '启停组合包的一行'
        def 动作():
            '把行的启停交给 Host'
            结果=自身.上下文.remote.pluginManager.setPluginEnabled(入口标识,启用)
            自身.已应用(结果,入口标识)
            if 结果.get('ok') is True and 结果['value']['application'] in ('applied','restart-required'):
                自身.记录切换(入口标识,启用,True)
        自身.跑(行键(入口标识),{'packageName':入口标识,'action':'rowEnable' if 启用 else 'rowDisable'},动作)

    def 关掉提示(自身):
        '关掉提示'
        自身.补丁({'notice':None})

    def 打开对话框(自身):
        '新对话框从上次用过的源开始，并读取 Host 提供的源。藏起的安装原样打开'
        开始=自身.取快照()['install'].get('requestId') is None
        if 开始:
            自身.临时注册表=False
            记得=自身.注册表记忆.getSnapshot()
            选择=官方选择 if 记得 is None else 记得
            自身.补丁({'install':{**新空闲(),'open':True,'registry':选择}})
            读取={'choice':自身.取快照()['install']['registry']}
            自身.注册表读取=读取
            自身.读注册表(读取)
        else:
            自身.补丁安装({'open':True})
        自身.核对安装()
        return 开始

    def 安装进度(自身,进度):
        '跟随 Host 对本对话框安装的取消窗口'
        安装=自身.取快照()['install']
        if 安装.get('requestId')!=进度['requestId'] or not 是否安装待决(安装['phase']):
            return
        请求=自身.请求
        if 请求 is None:
            return
        请求['acknowledged']=True
        if 安装['phase']=='applying':
            return
        if 进度['phase']=='installing' and 请求.get('cancellation') is not None:
            if 请求['cancellation'].get('waitingForStart') is True:
                自身.发送取消(请求,请求['cancellation'])
            return
        补丁={'phase':'running' if 进度['phase']=='installing' else 进度['phase']}
        尝试=进度.get('attempt')
        if 尝试 is not None:
            已有=[] if 安装.get('attempts') is None else list(安装['attempts']['registries'])
            补丁['attempts']={'registries':已有+[尝试['registry']],'total':尝试['total']}
        自身.补丁安装(补丁)

    def 当前注册表读取(自身,读取):
        '这份读取是否仍属于当前对话框'
        return 自身.已拆除 is not True and 自身.注册表读取 is 读取

    def 读注册表(自身,读取):
        '读 Host 提供的源。人没改过选择时，空的官方源可以改成更快的镜像'
        应答=自身.上下文.remote.pluginManager.registries()
        安装=自身.取快照()['install']
        if not 自身.当前注册表读取(读取) or 安装['open'] is not True or 应答.get('ok') is not True:
            return
        记得=自身.注册表记忆.getSnapshot()
        未动=安装['registry'] is 读取['choice'] and 安装['phase'] in ('idle','checking')
        if 未动:
            if 记得 is None:
                读取['choice']={'kind':'offered','registry':应答['value']['registry']}
            elif 记得['kind']=='custom' or 记得['registry'] is None:
                读取['choice']=记得
            else:
                键=注册表键(记得['registry'],应答['value'].get('resolved'))
                命中=None
                for 注册表 in 提供的注册表(应答['value']):
                    if 注册表键(注册表,应答['value'].get('resolved'))==键:
                        命中=注册表
                        break
                if 命中 is None:
                    读取['choice']={'kind':'custom','url':记得['registry']}
                else:
                    读取['choice']={'kind':'offered','registry':命中}
        补丁={'registries':应答['value']}
        if 未动:
            补丁['registry']=读取['choice']
        自身.补丁安装(补丁)
        值=应答['value']
        镜像=None
        if 值['registry'] is None and 值.get('resolved') is not None:
            try:
                规范=规范化注册表(值['resolved'])
            except Exception:
                规范=None
            if 规范==官方npm注册表:
                for 注册表 in 值['fallbackRegistries']:
                    if 注册表==npmmirror注册表:
                        镜像=注册表
                        break
        if not 未动 or 记得 is not None or 镜像 is None:
            return
        最快=自身.上下文.remote.pluginRegistryProbe.fastest()
        当前=自身.取快照()['install']
        if not 自身.当前注册表读取(读取) or 当前['open'] is not True:
            return
        if 当前['phase'] not in ('idle','checking') or 当前['registry'] is not 读取['choice']:
            return
        if not isinstance(最快,dict) or 最快.get('ok') is not True or 最快.get('value')!=镜像:
            return
        读取['choice']={'kind':'offered','registry':镜像}
        自身.补丁安装({'registry':读取['choice']})

    def 追加日志(自身,块):
        '把属于这次安装的日志折进 pnpm 命令。结束后的最后一块仍更新已有运行'
        安装=自身.取快照()['install']
        if 块['requestId']!=安装.get('requestId'):
            return
        if 安装.get('requestId') is not None and 安装['phase'] in ('starting','cancelling','unconfirmed'):
            自身.安装进度({'requestId':安装['requestId'],'phase':'installing'})
            安装=自身.取快照()['install']
        下标=-1
        序=0
        for 运行 in 安装['runs']:
            if 运行['jobId']==块['jobId']:
                下标=序
                break
            序=序+1
        if 下标==-1 and not 是否安装待决(安装['phase']):
            return
        结算={}
        if 'exitCode' in 块:
            结算['exitCode']=块['exitCode']
        if 下标==-1:
            运行表=list(安装['runs'])
            运行表.append({
                'jobId':块['jobId'],
                'command':' '.join(块['argv']),
                'cwd':块['cwd'],
                'output':块['text'],
                **结算,
            })
        else:
            运行表=[]
            序=0
            for 运行 in 安装['runs']:
                if 序==下标:
                    运行表.append({**运行,'output':运行['output']+块['text'],**结算})
                else:
                    运行表.append(运行)
                序=序+1
        自身.补丁安装({'runs':运行表})

    def 加载(自身):
        '读组合包和行。正在读时记一次结束后再跑'
        if 自身.已拆除:
            return
        自身.核对安装()
        if 自身.飞行中:
            自身.再跑=True
            return
        自身.飞行中=True
        try:
            自身.读取()
        finally:
            自身.飞行中=False

    def 结算刷新(自身):
        '只在拆除前发布刷新结果'
        if 自身.已拆除:
            return
        失败=自身.取快照()['status']=='error'
        if 失败 and 自身.有缓存:
            自身.补丁({
                'status':'ready',
                'refreshStatus':'idle',
                'notice':{'kind':'refresh-failed','seq':自身.下一提示()},
            })
            return
        自身.补丁({'refreshStatus':'failed' if 失败 else 'idle'})

    def 读取(自身):
        '合并重叠的读取'
        while True:
            自身.再跑=False
            自身.代次=自身.代次+1
            代次=自身.代次
            if 自身.取快照()['status']=='idle':
                自身.补丁({'status':'loading'})
            清单=自身.上下文.remote.pluginInventory.list()
            if 代次!=自身.代次:
                return
            if 清单.get('ok') is not True:
                自身.补丁({'status':'error'})
                if 自身.再跑:
                    continue
                return
            if 清单['value'].get('managementAvailable') is not True:
                自身.有缓存=False
                自身.补丁({'status':'unavailable','packages':[]})
                if 自身.再跑:
                    continue
                return
            组合=自身.上下文.remote.pluginManager.listBundles()
            插件=自身.上下文.remote.pluginManager.listPlugins()
            if 代次!=自身.代次:
                return
            if 组合.get('ok') is not True or 插件.get('ok') is not True:
                自身.补丁({'status':'error'})
                if 自身.再跑:
                    continue
                return
            包表=[]
            for 组合包 in 组合['value']:
                行表=[]
                for 行 in 组合包['rows']:
                    活=None
                    if 行.get('entryId') is not None:
                        for 插件项 in 插件['value']:
                            if 插件项['entryId']==行['entryId']:
                                活=插件项
                                break
                    行视图={
                        'rowId':行['rowId'],
                        'moduleName':行['moduleName'],
                        'enabled':False if 活 is None else 活.get('enabled') is True,
                        'phase':None if 活 is None else 活.get('fiberPhase'),
                    }
                    if 行.get('meta') is not None:
                        行视图['meta']=行['meta']
                    if 行.get('entryId') is not None:
                        行视图['entryId']=行['entryId']
                    if 活 is not None and 活.get('readOnlyReason') is not None:
                        行视图['readOnlyReason']=活['readOnlyReason']
                    行表.append(行视图)
                视图={
                    'name':组合包['name'],
                    'official':组合包['official'],
                    'availability':组合包['availability'],
                    'installed':组合包['installed'],
                    'optional':组合包['optional'],
                    'removable':组合包['removable'],
                    'enabled':组合包['enabled'],
                    'rows':行表,
                }
                for 键 in ('installTarget','version','source','description','meta','readOnlyReason','error'):
                    if 组合包.get(键) is not None:
                        视图[键]=组合包[键]
                包表.append(视图)
            自身.有缓存=True
            刷新态=自身.取快照()['refreshStatus']
            自身.补丁({
                'status':'ready',
                'refreshStatus':'refreshing' if 刷新态=='refreshing' else 'idle',
                'packages':sorted(包表,key=排序键),
            })
            if not 自身.再跑:
                return

    def 中止检查(自身):
        '丢掉飞行中的检查，它的应答不再采用'
        if 自身.检查中止 is not None:
            自身.检查中止['aborted']=True
        自身.检查中止=None

    def 已过时(自身,信号):
        '结算是否太晚'
        return 自身.已拆除 or 信号['aborted'] is True

    def 打开目录安装(自身,包,目标,启用):
        '用目录里的精确目标重开安装对话框'
        if 自身.已拆除:
            return
        阶段=自身.取快照()['install']['phase']
        if 阶段=='checking' or 是否安装待决(阶段):
            自身.补丁安装({'open':True})
            return
        自身.中止检查()
        记得=自身.注册表记忆.getSnapshot()
        注册表=官方选择 if 记得 is None else 记得
        本地=目标['spec'].startswith('link:')
        主体={
            'status':'accepted',
            'kind':'path' if 本地 else 'registry',
            'name':包['name'],
            'version':目标['version'],
            'bundle':True,
            'spec':目标['spec'],
            'registry':注册表['url'] if 注册表['kind']=='custom' else 注册表['registry'],
            'selection':启用,
        }
        if not 本地:
            主体['saveExact']=True
        自身.补丁({'install':{**新空闲(),'open':True,'spec':主体['spec'],'registry':注册表,'subject':主体}})
        读取={'choice':注册表}
        自身.注册表读取=读取
        自身.读注册表(读取)
        自身.跑安装()

    def 跑安装(自身):
        '先让 Host 读规格，接受后再安装。失败屏上再跑一次'
        状态=自身.取快照()
        安装=状态['install']
        规格=安装['spec'].strip()
        if 安装['phase']=='checking' or 是否安装待决(安装['phase']) or 规格=='':
            return
        分析=自身.取分析()
        if 分析 is not None and 分析.enabled:
            自身.分析尝试={'input':净化安装输入(规格),'started':time.time()}
            分析.track('plugin_install_click',{'input_value':净化安装输入(规格)})
        已列=None
        for 包 in 状态['packages']:
            if 包['name']==规格:
                已列=包
                break
        目录主体=None
        主体=安装.get('subject')
        if 主体 is not None and 'selection' in 主体 and 主体.get('spec')==规格:
            目录主体=主体
        if 已列 is not None and 已列.get('availability')!='missing' and 目录主体 is None:
            自身.结束分析('failed','already-installed')
            问题='shipped' if 已列.get('availability')=='installation' else 'already-installed'
            自身.补丁安装({'phase':'idle','inputError':{'problem':问题,'reason':规格}})
            return
        选择=安装['registry']
        手填=选择['url'].strip() if 选择['kind']=='custom' else None
        if 手填 is not None and 注册表网址.match(手填) is None:
            自身.结束分析('failed','invalid-registry')
            自身.补丁安装({'phase':'idle','registryError':True,'registryOpen':True})
            return
        自身.中止检查()
        信号={'aborted':False}
        自身.检查中止=信号
        自身.补丁安装({
            'phase':'checking',
            'inputError':None,
            'subject':目录主体,
            'runs':[],
            'detailsOpen':False,
            'attempts':None,
            'registryOpen':False,
            'installed':None,
            'installedVersion':None,
            'restartRequired':False,
            'failure':None,
            'approvedBuilds':[],
        })
        读取=自身.注册表读取
        if 读取 is not None and 选择 is 读取['choice'] and 读取.get('done') is True:
            if 自身.已过时(信号) or 自身.注册表读取 is not 读取:
                return
        当前选择=自身.取快照()['install']['registry']
        if 当前选择['kind']=='custom':
            选定={**当前选择,'url':当前选择['url'].strip()}
        else:
            选定=当前选择
        注册表=选定['url'] if 选定['kind']=='custom' else 选定['registry']
        if 自身.临时注册表 is not True:
            自身.注册表记忆.set(选定)
        if 目录主体 is not None:
            自身.检查中止=None
            自身.开始安装({**目录主体,'registry':注册表})
            return
        检查=自身.上下文.remote.pluginManager.inspect(规格,{'registry':注册表},信号)
        if 自身.已过时(信号):
            return
        自身.检查中止=None
        if 检查.get('ok') is not True:
            自身.结束分析('failed',检查['error']['code'])
            自身.补丁安装({'phase':'idle','inputError':{'problem':'unknown','reason':检查['error']['message']}})
            return
        if 检查['value']['status']=='refused':
            问题=检查['value']['problem']
            原因=检查['value']['reason']
            自身.结束分析('failed',问题)
            输入错误={'problem':问题,'reason':原因}
            if 检查['value'].get('registries') is not None:
                输入错误['registries']=检查['value']['registries']
            自身.补丁安装({'phase':'idle','inputError':输入错误})
            return
        自身.开始安装({'spec':规格,**检查['value']})

    def 开始安装(自身,主体,已允许=None):
        '把已检查的规格交给 Host'
        请求标识=str(uuid4())
        请求={'requestId':请求标识,'acknowledged':False,'replyLost':False,'recovering':False}
        自身.请求=请求
        自身.补丁安装({
            'phase':'starting',
            'requestId':请求标识,
            'subject':主体,
            'runs':[],
            'attempts':None,
            'failure':None,
            'installed':None,
            'installedVersion':None,
            'approvedBuilds':[],
        })
        选项={'enabled':主体['selection'] if 'selection' in 主体 else False,'requestId':请求标识,'registry':主体.get('registry')}
        if 'saveExact' in 主体:
            选项['saveExact']=主体['saveExact']
        if 已允许 is not None:
            选项['approvedBuilds']=list(已允许)
        结果=自身.上下文.remote.pluginManager.installBundle(主体['spec'],选项)
        if 自身.已拆除 or 自身.请求 is not 请求:
            return
        if 结果.get('ok') is not True:
            请求['replyLost']=True
            自身.安装不确定('result',结果['error']['message'])
            自身.核对安装()
            return
        自身.结算安装(结果['value'])

    def 核对安装(自身):
        '丢失的应答向 Host 再要一次。没有活动任务就是未知'
        请求=自身.请求
        if 请求 is None or 请求['replyLost'] is not True or 请求['recovering'] is True:
            return
        请求['recovering']=True
        结果=自身.上下文.remote.pluginManager.waitForInstall(请求['requestId'])
        if 自身.已拆除 or 自身.请求 is not 请求:
            return
        请求['recovering']=False
        if 结果.get('ok') is not True:
            自身.安装不确定('result',结果['error']['message'])
            return
        if 结果['value'] is not None:
            自身.结算安装(结果['value'])
            return
        自身.请求=None
        自身.结束分析('unknown')
        自身.补丁安装({
            'phase':'unknown',
            'failure':None,
            'runs':结算运行表(自身.取快照()['install']['runs'],None),
        })
        自身.通知隐藏安装('unknown')
        自身.加载()

    def 结算安装(自身,结果):
        '按 Host 的应答收起对话框'
        if 结果['application']=='failed':
            状态='failed'
            原因=None if 结果.get('error') is None else 结果['error'].get('code')
        elif 结果['application']=='cancelled':
            状态='cancelled'
            原因=None
        else:
            状态='success'
            原因=None
        自身.结束分析(状态,原因,结果.get('bundle'))
        安装=自身.取快照()['install']
        自身.请求=None
        问过={}
        if 结果.get('registries') is not None:
            总数=0 if 安装.get('attempts') is None else 安装['attempts']['total']
            if len(结果['registries'])>总数:
                总数=len(结果['registries'])
            问过={'attempts':{'registries':结果['registries'],'total':总数}}
        if 结果['application']=='cancelled':
            自身.再给规格({'kind':'cancelled','seq':自身.下一提示()})
        elif 结果['application']=='failed':
            包结果=结果.get('packageResult')
            退出=None if 包结果 is None else 包结果.get('exitCode')
            失败={'reason':'' if 结果.get('error') is None else 结果['error'].get('diagnostic') or ''}
            if 结果.get('error') is not None and 结果['error'].get('code') is not None:
                失败['code']=结果['error']['code']
            if 结果.get('error') is not None and 结果['error'].get('incompatible') is not None:
                失败['incompatible']=结果['error']['incompatible']
            if 包结果 is not None and 包结果.get('kind') is not None:
                失败['kind']=包结果['kind']
            if 结果.get('failedAt') is not None:
                失败['failedAt']=结果['failedAt']
            if 结果.get('pendingBuilds') is not None and len(结果['pendingBuilds'])>0:
                失败['pendingBuilds']=结果['pendingBuilds']
            自身.补丁安装({
                'phase':'failed',
                'runs':结算运行表(安装['runs'],退出),
                'failure':失败,
                **问过,
            })
        else:
            补丁={
                'phase':'done',
                'runs':结算运行表(安装['runs'],0),
                'failure':None,
                'installed':结果.get('bundle'),
                'installedVersion':结果.get('version'),
                'restartRequired':结果['application']=='restart-required',
                'approvedBuilds':结果['approvedBuilds'] if 结果.get('approvedBuilds') is not None else [],
                **问过,
            }
            if 结果.get('restartReason') is not None:
                补丁['restartReason']=结果['restartReason']
            自身.补丁安装(补丁)
        完成=自身.取快照()['install']
        if 完成['phase']=='done' and 完成.get('subject') is not None and 'selection' in 完成['subject'] and 结果.get('bundle') is not None:
            自身.已应用({'ok':True,'value':结果},结果['bundle'])
            自身.补丁({'highlight':结果['bundle']})
            if 完成['subject']['selection']:
                自身.记录切换(结果['bundle'],True,False)
        阶段=自身.取快照()['install']['phase']
        if 阶段 in ('done','failed'):
            自身.通知隐藏安装(阶段)
        自身.加载()

    def 安装不确定(自身,不确定,原因):
        '丢失应答、取消未确认，或还在等 Host 接受'
        阶段=自身.取快照()['install']['phase']
        自身.补丁安装({
            'phase':'applying' if 阶段=='applying' else 'unconfirmed',
            'failure':{'reason':原因,'uncertainty':不确定},
        })
        自身.通知隐藏安装('unconfirmed')

    def 允许构建并重试(自身):
        '允许失败运行留下的脚本，并再跑同一规格'
        安装=自身.取快照()['install']
        待允许=None if 安装.get('failure') is None else 安装['failure'].get('pendingBuilds')
        if 安装['phase']!='failed' or 安装.get('subject') is None or 待允许 is None or len(待允许)==0:
            return
        分析=自身.取分析()
        if 分析 is not None and 分析.enabled:
            自身.分析尝试={'input':净化安装输入(安装['subject']['spec']),'started':time.time()}
        自身.开始安装(安装['subject'],待允许)

    def 取消安装(自身):
        '检查或失败立刻回到规格。Host 拥有的运行要等它自己停'
        安装=自身.取快照()['install']
        if 安装['phase'] in ('checking','failed','unknown'):
            if 安装['phase']=='checking':
                自身.结束分析('cancelled')
            自身.中止检查()
            自身.再给规格()
            return
        请求=自身.请求
        if 安装['phase'] not in ('starting','running','unconfirmed') or 请求 is None:
            return
        if 请求.get('cancellation') is not None and 请求['cancellation'].get('waitingForStart') is not True:
            return
        取消={'waitingForStart':False}
        请求['cancellation']=取消
        自身.发送取消(请求,取消)

    def 发送取消(自身,请求,取消):
        '抢在安装开始前的取消，等 Host 确认这次请求后再试'
        已确认=请求['acknowledged']
        取消['waitingForStart']=False
        自身.补丁安装({'phase':'cancelling','failure':None})
        结果=自身.上下文.remote.pluginManager.cancelInstall(请求['requestId'])
        if 自身.已拆除 or 自身.请求 is not 请求 or 请求.get('cancellation') is not 取消:
            return
        if 结果.get('ok') is not True:
            取消['waitingForStart']=请求['acknowledged'] is not True
            if 请求['acknowledged'] is True:
                请求['cancellation']=None
            自身.安装不确定('result' if 请求['replyLost'] else 'cancellation',结果['error']['message'])
            return
        if 结果['value']['status']=='cancelled':
            自身.结束分析('cancelled')
            自身.再给规格({'kind':'cancelled','seq':自身.下一提示()})
            自身.加载()
            return
        if 结果['value']['status']=='too-late':
            请求['acknowledged']=True
            请求['cancellation']=None
            自身.补丁安装({'phase':'applying'})
            自身.通知隐藏安装('applying')
            自身.核对安装()
            return
        if 请求['replyLost'] is True:
            请求['cancellation']=None
            自身.安装不确定('result','')
            自身.核对安装()
            return
        if not 已确认 and 自身.取快照()['install']['phase']!='applying':
            if 请求['acknowledged'] is True:
                自身.发送取消(请求,取消)
            else:
                取消['waitingForStart']=True
                自身.安装不确定('acceptance','')
            return
        请求['cancellation']=None
        自身.安装不确定('cancellation','')

    def 通知隐藏安装(自身,结果):
        '对话框已藏起时，用提示说出安装结果'
        if 自身.取快照()['install']['open'] is not True:
            自身.补丁({'notice':{'kind':'install','outcome':结果,'seq':自身.下一提示()}})

    def 再给规格(自身,提示=None):
        '放开这次请求，回到编辑，规格留下'
        自身.请求=None
        补丁={'install':再规格(自身.取快照()['install'])}
        if 提示 is not None:
            补丁['notice']=提示
        自身.补丁(补丁)

    def 启用已安装(自身):
        '启用刚装上的组合包，然后关掉对话框并在列表里标出'
        安装=自身.取快照()['install']
        if 安装['phase']!='done' or 安装['enabling'] is True:
            return
        名=安装['installed']
        自身.补丁安装({'enabling':True})
        if 名 is not None:
            结果=自身.上下文.remote.pluginManager.setBundleEnabled(名,True)
            if 自身.已拆除:
                return
            try:
                自身.已应用(结果,名)
                if 结果.get('ok') is True and 结果['value']['application'] in ('applied','restart-required'):
                    自身.记录切换(名,True,False)
            except Exception as 错误:
                自身.补丁({'notice':失败提示(错误,{'packageName':名,'action':'enable'},自身.下一提示())})
        自身.补丁({'install':新空闲(),'highlight':名})
        自身.加载()

    def 跑(自身,键,主体,动作):
        '在忙碌键下跑动作。失败变提示，事后重读'
        if 自身.已拆除 or 键 in 自身.取快照()['busy']:
            return
        自身.补丁({'busy':list(自身.取快照()['busy'])+[键],'notice':None})
        try:
            动作()
        except Exception as 错误:
            自身.补丁({'notice':失败提示(错误,主体,自身.下一提示())})
        finally:
            自身.补丁({'busy':[项 for 项 in 自身.取快照()['busy'] if 项!=键]})
        自身.加载()

    def 已应用(自身,应答,包名):
        '发布变更结果。拒绝或未能应用则抛出，由跑去报'
        if 应答.get('ok') is not True:
            raise 远程应答错误(应答['error']['message'])
        结果=应答['value']
        应用=结果['application']
        if 应用=='failed':
            错误=结果.get('error')
            诊断='' if 错误 is None else 错误.get('diagnostic') or ''
            码=None if 错误 is None else 错误.get('code')
            不兼容=None if 错误 is None else 错误.get('incompatible')
            raise 远程应答错误(诊断,码,不兼容)
        if 应用=='cancelled':
            自身.补丁({'notice':{'kind':'cancelled','seq':自身.下一提示()}})
            return
        if 应用=='restart-required':
            自身.补丁({'notice':{'kind':'restart','packageName':包名,'reason':结果.get('restartReason'),'seq':自身.下一提示()}})
            return
        if 应用=='overridden':
            自身.补丁({'notice':{'kind':'overridden','packageName':包名,'seq':自身.下一提示()}})
            return

    def 记录切换(自身,名称,启用,是行=False):
        '记下组合包或组件的启停'
        组合=None
        for 包 in 自身.取快照()['packages']:
            if 是行:
                for 行 in 包['rows']:
                    if 行.get('entryId')==名称:
                        组合=包
                        break
            elif 包['name']==名称:
                组合=包
            if 组合 is not None:
                break
        if 是行:
            插件名=None
            if 组合 is not None:
                for 行 in 组合['rows']:
                    if 行.get('entryId')==名称:
                        插件名=行.get('moduleName')
                        break
        else:
            插件名=名称
        if 组合 is None or 插件名 is None:
            return
        分析=自身.取分析()
        if 分析 is None:
            return
        分析.track('plugin_toggle',{
            'plugin_name':插件名,
            'plugin_type':'plugin' if 是行 else 'bundle',
            'is_enabled':启用,
            'is_builtin':组合.get('availability')=='installation',
        })

    def 结束分析(自身,状态,原因=None,名称=None):
        '把这次安装尝试记成结果'
        尝试=自身.分析尝试
        自身.分析尝试=None
        if 尝试 is None or 自身.已拆除:
            return
        if 状态=='cancelled':
            错误原因='user_cancelled'
        elif 状态=='unknown':
            错误原因='unknown_result'
        else:
            错误原因=原因
        属性={
            'input_value':尝试['input'],
            'is_success':状态=='success',
            'duration':max(0,int((time.time()-尝试['started'])*1000)),
        }
        if 错误原因 is not None:
            属性['error_reason']=错误原因
        if 名称 is not None:
            属性['plugin_name']=名称
        分析=自身.取分析()
        if 分析 is not None:
            分析.track('install_plugin_result',属性)

    def 补丁(自身,下一):
        '合并状态。拆除后不再发布'
        if 自身.已拆除:
            return
        自身.存储.set({**自身.取快照(),**下一})

    def 补丁安装(自身,下一):
        '合并安装态'
        自身.补丁({'install':{**自身.取快照()['install'],**下一}})
