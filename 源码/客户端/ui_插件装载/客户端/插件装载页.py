import importlib.resources as 包资源
from nicegui import ui as 界面
from ....基础设施.通用工具 import utf8字节数
from ...ui_基础界面组件.状态点 import 状态点
from .配置账本 import 行配置键#行配置键
from .装载存储 import 是否安装待决,行键#装载工具
from ..异常 import 页面失败文案
from .呈现 import 装载文案,提示文案,包文案#呈现

__all__=['插件装载页','高亮毫秒','行筛选阈值']#仅中文公开名

高亮毫秒=2400#安装启用后列表高亮时长
行筛选阈值=10#超过此数显示筛选框

内置档组合包={#页面排除的内置 profile 组合包
    '@deepseek-ai/dsh-base',
    '@deepseek-ai/dsh-web-app',
    '@deepseek-ai/dsh-headless',
    '@deepseek-ai/dsh-sdk-app',
    '@deepseek-ai/dsh-acp-app',
    '@deepseek-ai/dsh-sdk-minimal',
}#内置结束

阶段键={#fiber 阶段 → 文案键
    'pending':'rowPhasePending',
    'loading':'rowPhaseLoading',
    'active':'rowPhaseActive',
    'failed':'rowPhaseFailed',
    'unloading':'rowPhaseUnloading',
}#阶段结束

阶段点={#阶段 → 状态点
    'pending':'idle',
    'loading':'ongoing',
    'active':'done',
    'failed':'error',
    'unloading':'idle',
}#点结束

输入问题键={#检查拒因 → 文案键
    'invalid-spec':'installProblemInvalid',
    'already-installed':'installProblemInstalled',
    'not-found':'installProblemNotFound',
    'not-a-package':'installProblemNotPackage',
    'not-a-bundle':'installProblemNotBundle',
    'network':'installProblemNetwork',
    'unknown':'installProblemUnknown',
}#输入结束

失败种类键={#pnpm 失败种类 → 文案键
    'pnpm-missing':'installFailurePnpmMissing',
    'timeout':'installFailureTimeout',
    'not-found':'installFailureNotFound',
    'no-matching-version':'installFailureNoMatchingVersion',
    'network':'installFailureNetwork',
    'disk-full':'installFailureDiskFull',
    'permission':'installFailurePermission',
    'build-blocked':'installFailureBuildBlocked',
    'integrity':'installFailureIntegrity',
    'unknown':'installFailureGeneric',
}#失败种类结束

屏标题键={#安装阶段 → 标题
    'starting':'installStarting',
    'running':'installingTitle',
    'cancelling':'installCancelling',
    'applying':'installApplying',
    'done':'installedTitle',
    'failed':'installFailedTitle',
}#屏标题结束

主体种类键={#主体种类 → 文案键
    'registry':None,
    'path':'installSubjectPath',
    'git':'installSubjectGit',
    'tarball':'installSubjectTarball',
}#主体结束

引导示例=(#安装引导三例
    {'key':'id','titleKey':'installGuideIdTitle','exampleKey':'installGuideIdExample','hintKey':'installGuideIdHint'},
    {'key':'git','titleKey':'installGuideGitTitle','exampleKey':'installGuideGitExample','hintKey':'installGuideGitHint'},
    {'key':'path','titleKey':'installGuidePathTitle','exampleKey':'installGuidePathExample','hintKey':'installGuidePathHint'},
)#引导结束

def _读样式(文件名):
    '读当前包内样式。失败时异常文案只有样式读不到，不含路径'
    try:
        return 包资源.files(__package__).joinpath(文件名).read_text(encoding='utf-8')
    except OSError:
        raise OSError('样式读不到') from None

def _去注释(原文):
    '去掉块注释，避免注释里的花括号打断规则'
    出=[]
    下标=0
    长度=len(原文)
    while 下标<长度:
        if 原文.startswith('/*',下标):
            止=原文.find('*/',下标+2)
            if 止<0:
                break
            下标=止+2
            continue
        出.append(原文[下标])
        下标+=1
    return ''.join(出)

def _前缀一片(片,根):
    '同一元素与后代都能命中'
    片=片.strip()
    if 片=='':
        return ''
    return '.'+根+' '+片+', .'+根+片

def _前缀选择器(选择器,根):
    '逗号分隔的每一段都挂上根'
    条=[]
    for 片 in 选择器.split(','):
        已=_前缀一片(片,根)
        if 已!='':
            条.append(已)
    return ', '.join(条)

def _挂规则(文,根):
    '普通规则挂根；媒体查询递归；关键帧保持原样'
    出=[]
    下标=0
    长度=len(文)
    while 下标<长度:
        while 下标<长度 and 文[下标].isspace():
            下标+=1
        if 下标>=长度:
            break
        起=下标
        while 下标<长度 and 文[下标]!='{':
            下标+=1
        if 下标>=长度:
            break
        选择器=文[起:下标].strip()
        下标+=1
        深度=1
        体起=下标
        while 下标<长度 and 深度>0:
            if 文[下标]=='{':
                深度+=1
            elif 文[下标]=='}':
                深度-=1
            下标+=1
        体=文[体起:下标-1]
        if 选择器.startswith('@keyframes') or 选择器.startswith('@font-face'):
            出.append(选择器+'{'+体+'}')
        elif 选择器.startswith('@media') or 选择器.startswith('@container') or 选择器.startswith('@supports'):
            出.append(选择器+'{'+_挂规则(体,根)+'}')
        elif 选择器!='':
            出.append(_前缀选择器(选择器,根)+'{'+体+'}')
    return '\n'.join(出)

def _挂到根(原文,根):
    '共享样式只作用在本组件根下'
    return _挂规则(_去注释(原文),根)

界面.add_css(_挂到根(_读样式('插件装载页.module.css'),'插件装载页根'),shared=True)

def 轻提示毫秒(文本):
    'toast 停留时长'
    return min(8000,max(3000,utf8字节数(文本)*80))#按字节预算

def 部件摘要(行表,翻译):
    '组件计数行'
    失败=len([行 for 行 in 行表 if 行.get('phase')=='failed'])#失败数
    关闭=len([行 for 行 in 行表 if not 行['enabled']])#关闭数
    运行=len([行 for 行 in 行表 if 行['enabled'] and 行.get('phase')=='active'])#运行数
    段=[翻译('partsCountTotal',{'count':str(len(行表))})]#段
    if 运行>0:段.append(翻译('partsCountRunning',{'count':str(运行)}))#运行
    if 关闭>0:段.append(翻译('partsCountOff',{'count':str(关闭)}))#关闭
    if 失败>0:段.append(翻译('partsCountFailed',{'count':str(失败)}))#失败
    return ' · '.join(段)#连接

def 包状态(包):
    '卡片状态：运行/关闭/异常'
    if 'error' in 包 and 包['error'] is not None:
        return 'problem'#异常
    return 'running' if 包['enabled'] else 'disabled'#启停

def 行状态文案(行,翻译):
    '行状态句'
    if not 行['enabled']:
        return 翻译('partOff')#关闭
    阶段=行.get('phase')#阶段
    return 翻译('rowStateIdle') if 阶段 is None else 翻译(阶段键[阶段])#阶段

def 行点状态(行):
    '行旁状态点'
    if not 行['enabled'] or 'phase' not in 行:
        return 'idle'#空闲
    return 阶段点[行['phase']]#点

def 失败文案(失败,翻译):
    '失败屏一句'
    if 失败 is None:
        return 翻译('installFailureGeneric')#通用
    待=失败['pendingBuilds'] if 'pendingBuilds' in 失败 else None#待允许
    if 失败.get('kind')=='build-blocked' and (待 is None or len(待)==0):
        return 翻译('installFailureBuildBlockedManual')#手动
    if 'kind' in 失败 and 失败['kind'] is not None:
        return 翻译(失败种类键[失败['kind']])#种类
    if 'code' in 失败 and 失败['code'] is not None:
        return 装载文案({'code':失败['code'],'diagnostic':失败.get('reason')},翻译)#码
    原因=失败.get('reason') or ''#原因
    if 原因=='':
        return 翻译('installFailureGeneric')#通用
    return 页面失败文案(原因)

class 插件装载页:#插件装载页视图模型
    '官方与已安装组合包、详情、安装对话框与卸载确认'
    def __init__(自身,属性):
        '记下合成 props。槽位只调用构造，键齐了就画。'
        自身.属性=属性 if isinstance(属性,dict) else {}#props
        自身.页态={'kind':'list'}#当前页
        自身.行筛选=''#行筛选
        自身.引导开=False#安装引导
        自身.已确保=False#已首读
        自身.激活名=None#刚启用的包
        自身.添加开=False#添加菜单
        if 't' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新合成 props'
        自身.属性=属性#最新

    def _写视图(自身,视图):
        '写入导航存储；没有存储时只记在页面上'
        自身.页态=视图#本地副本
        动作=自身.属性['actions'] if 'actions' in 自身.属性 and isinstance(自身.属性['actions'],dict) else None#动作
        写=动作['setView'] if 动作 is not None and 'setView' in 动作 else None#写视图
        if callable(写):
            写(视图)#存储

    def _读视图(自身):
        '优先读导航存储，缺席时用页面自己的页态'
        用=自身.属性['useStore'] if 'useStore' in 自身.属性 else None#选择器
        if callable(用):
            态=用(lambda 值:值)#整份
            if isinstance(态,dict) and isinstance(态.get('view'),dict):
                return 态['view']#存储
        return 自身.页态#本地

    def _解析文案(自身,文本):
        '包内文案；解析失败只留下去掉路径后的说明'
        解析=自身.属性['resolveText'] if 'resolveText' in 自身.属性 else None#解析器
        if callable(解析):
            try:
                return 解析(文本)#解析
            except Exception as 错误:
                return 页面失败文案(错误)#说明
        if isinstance(文本,str):
            return 文本#原样
        return ''#空

    def _行说明(自身,行):
        '行元数据里的说明；没有则留给 summary 槽'
        元=行['meta'] if 'meta' in 行 and isinstance(行['meta'],dict) else None#元数据
        if 元 is None or 'description' not in 元 or 元['description'] is None:
            return None#没有说明
        文=自身._解析文案(元['description'])#解析
        if isinstance(文,str) and 文.strip()!='':
            return 文#说明
        return None#空说明当没有

    def 开包(自身,名):
        '打开组合包页'
        自身._写视图({'kind':'package','name':名})#包页

    def 开条目(自身,身份):
        '打开官方插件页'
        自身._写视图({'kind':'item','id':身份})#条目页

    def 开行(自身,名,行标识):
        '打开行配置页'
        自身._写视图({'kind':'row','name':名,'rowId':行标识})#行页

    def 回列表(自身):
        '回卡片列表'
        自身._写视图({'kind':'list'})#列表

    def 回包(自身,名):
        '回组合包页'
        自身._写视图({'kind':'package','name':名})#包页

    def 设行筛选(自身,文本):
        '改行筛选'
        自身.行筛选=文本#筛选

    def 切换引导(自身):
        '翻转安装引导'
        自身.引导开=not 自身.引导开#翻转

    def _读钩(自身,钩名):
        'use* 选择器，或尚未绑定的对象源'
        用名='use'+钩名[0].upper()+钩名[1:]#座位名
        用=自身.属性[用名] if 用名 in 自身.属性 else None#选择器
        if callable(用):#已绑定
            return 用(lambda 值:值)#整份
        钩=自身.属性['hooks'] if 'hooks' in 自身.属性 and isinstance(自身.属性['hooks'],dict) else None#旧面
        if 钩 is None or 钩名 not in 钩 or 钩[钩名] is None:#无源
            return None#缺
        源=钩[钩名]#源
        if hasattr(源,'getSnapshot'):#对象
            return 源.getSnapshot()#快照
        return None#不能读

    def _已装(自身,包):
        '显式已安装；缺键不是已装'
        return 'installed' in 包 and 包['installed'] is True#已装

    def _可选(自身,包):
        '显式可选官方包；缺键不是可选'
        return 'optional' in 包 and 包['optional'] is True#可选

    def 视图(自身):
        '投影整页视图模型'
        属性=自身.属性#props
        翻译=属性['t']#文案
        确保=属性['ensure'] if 'ensure' in 属性 else None#首读
        if not 自身.已确保 and callable(确保):#首读
            确保()#确保
            自身.已确保=True#已
        状态=自身._读钩('pluginManager')#装载态
        账本=自身._读钩('configLedger')#账本
        if not isinstance(状态,dict) or not isinstance(账本,dict):#还没绑上
            return None#交给渲染画加载
        提示=状态['notice'] if 'notice' in 状态 else None#提示
        if isinstance(提示,dict) and 提示.get('kind')=='refresh-failed':
            提示行=None#刷新失败由罩层提示画
        elif 提示 is None:
            提示行=None#没有提示
        else:
            提示行=提示文案(提示,翻译)#提示句
        包表=状态['packages'] if 'packages' in 状态 and isinstance(状态['packages'],list) else []#包表；空列表保留
        忙碌=状态['busy'] if 'busy' in 状态 and isinstance(状态['busy'],list) else []#忙碌
        状态={**状态,'packages':包表,'busy':忙碌,'notice':提示}#补齐
        列出=[包 for 包 in 包表 if 'name' in 包 and 包['name'] not in 内置档组合包 and (自身._已装(包) or 自身._可选(包) or ('error' in 包 and 包['error'] is not None))]#列出
        我的=[包 for 包 in 列出 if 自身._已装(包) or not 自身._可选(包)]#已装
        官方=[包 for 包 in 列出 if 自身._可选(包) and not 自身._已装(包)]#官方
        已载=状态['status'] in ('ready','error')#已载
        视=自身._读视图()#当前页态
        开包=None#开的包
        开条目=None#开的条目
        开行=None#开的行
        if 视['kind'] in ('package','row'):#包或行
            for 包 in 列出:#查找
                if 包['name']==视['name']:#命中
                    开包=包
                    break
        if 视['kind']=='item':#条目
            for 项 in 账本['items']:#查找
                if 项['id']==视['id']:#命中
                    开条目=项
                    break
        if 视['kind']=='row' and 开包 is not None:#行
            for 行 in 开包['rows']:#查找
                if 行['rowId']==视['rowId']:#命中
                    开行=行
                    break
        显示卡片=开包 is None and 开条目 is None#卡片态
        结果={#基础
            'kind':'plugin-manager-page',#种类
            'cssModule':'插件装载页.module.css',#样式
            'status':状态['status'],#状态
            'busy':状态['busy'],#忙碌
            'notice':状态['notice'],#提示
            'noticeLine':提示行,#提示句
            'noticeHoldMs':轻提示毫秒(提示行) if 提示行 is not None else 0,
            'install':自身._安装视图(状态['install'],翻译),#安装
            'confirm':自身._确认视图(状态['confirm'],翻译),#确认
            'highlight':状态['highlight'],#高亮
            'highlightMs':高亮毫秒,#高亮时长
            'showsCards':显示卡片,#卡片
            'loaded':已载,#已载
            'labels':{#页文案
                'title':翻译('title'),
                'intro':翻译('intro'),
                'refresh':翻译('refresh'),
                'addPlugin':翻译('addPlugin'),
                'loading':翻译('loading'),
                'unavailable':翻译('unavailable'),
                'error':翻译('error'),
                'retry':翻译('retry'),
                'empty':翻译('empty'),
                'officialTitle':翻译('officialTitle'),
                'bundlesTitle':翻译('bundlesTitle'),
            },#文案结束
            'actions':{#动作
                'refresh':属性['refresh'],
                'openInstall':属性['openInstall'],
                'dismissNotice':属性['dismissNotice'],
                'clearHighlight':属性['clearHighlight'],
                'backToList':自身.回列表,
            },#动作结束
        }#基础结束
        if 显示卡片 and 已载:#卡片列表
            官方卡=[自身._包卡(包,翻译,状态) for 包 in 官方]#官方包卡
            for 项 in 账本['items']:#官方条目
                官方卡.append(自身._条目卡(项,翻译,属性))#条目卡
            结果['officialCards']=官方卡#官方
            结果['bundleCards']=[自身._包卡(包,翻译,状态) for 包 in 我的]#已装
        if 已载 and 开包 is not None and 开行 is not None:#行详情
            结果['rowDetail']=自身._行详情(开包,开行,翻译,属性)#行
        elif 已载 and 开包 is not None:#包详情
            结果['packageDetail']=自身._包详情(开包,翻译,状态,账本,属性)#包
        elif 已载 and 开条目 is not None:#条目详情
            结果['itemDetail']=自身._条目详情(开条目,翻译,属性)#条目
        return 结果#视图

    def _包卡(自身,包,翻译,状态):
        '组合包卡片'
        文=包文案(包,翻译)#文案
        return {#卡
            'kind':'package-card',#种类
            'name':包['name'],#名
            'title':文['title'],#标题
            'description':文['description'],#描述
            'beta':文['beta'],#beta
            'statusBeta':翻译('statusBeta'),#Beta 标
            'statusProblem':翻译('statusProblem'),#异常标
            'versionTag':翻译('versionTag',{'version':包['version']}) if 'version' in 包 and 包['version'] is not None else None,#版本
            'status':包状态(包),#状态
            'enabled':包['enabled'],#启用
            'busy':包['name'] in 状态['busy'],#忙碌
            'highlighted':状态['highlight']==包['name'],#高亮
            'readOnlyReason':包.get('readOnlyReason'),#只读
            'error':包.get('error'),#错误
            'actions':{#动作
                'open':lambda 名=包['name']:自身.开包(名),
                'setEnabled':lambda 启,名=包['name']:自身.属性['setEnabled'](名,启),#启停
            },#动作结束
        }#卡结束

    def _条目卡(自身,项,翻译,属性):
        '官方插件卡片'
        return {#卡
            'kind':'item-card',#种类
            'id':项['id'],#id
            'label':项['label'],#标签
            'summarySlot':{'name':'plugins.item','view':'summary','only':项['id']},#摘要槽
            'actions':{'open':lambda 身份=项['id']:自身.开条目(身份)},
        }#卡结束

    def _包详情(自身,包,翻译,状态,账本,属性):
        '组合包详情页'
        文=包文案(包,翻译)#文案
        查询=自身.行筛选.strip().lower()#筛选
        行表=包['rows'] if 查询=='' else [行 for 行 in 包['rows'] if 查询 in 行['rowId'].lower()]#过滤
        行视图=[]#行
        for 行 in 行表:#每行
            键=行配置键(包['name'],行['rowId'])#配置键
            有配置=键 in 账本['rows']
            行视图.append({#行
                'rowId':行['rowId'],#id
                'moduleName':行['moduleName'],#模块
                'entryId':行.get('entryId'),#入口
                'enabled':行['enabled'],#启用
                'phase':行.get('phase'),#阶段
                'stateText':行状态文案(行,翻译),#状态句
                'dotState':行点状态(行),#点
                'busy':行.get('entryId') is not None and 行键(行['entryId']) in 状态['busy'],#忙碌
                'locked':'readOnlyReason' in 行 or 'entryId' not in 行,#锁定
                'readOnlyReason':行.get('readOnlyReason'),#只读
                'hasConfig':有配置,#配置
                'configureLabel':翻译('configureRow',{'name':行['moduleName']}),#配置钮
                'actions':{#动作
                    'setEnabled':lambda 启,入口=行.get('entryId'):属性['setRowEnabled'](入口,启) if 入口 is not None else None,
                    'openConfig':lambda 名=包['name'],行标识=行['rowId']:自身.开行(名,行标识) if 有配置 else None,
                },#动作结束
            })#行结束
        return {#详情
            'kind':'package-detail',#种类
            'name':包['name'],#名
            'title':文['title'],#标题
            'description':文['description'] if isinstance(文.get('description'),str) and 文['description']!='' else None,#描述；没有则不另写一句
            'beta':文['beta'],#beta
            'version':包.get('version'),#版本
            'status':包状态(包),#状态
            'installed':包['installed'],#已装
            'enabled':包['enabled'],#启用
            'busy':包['name'] in 状态['busy'],#忙碌
            'readOnlyReason':包.get('readOnlyReason'),#只读
            'error':包.get('error'),#错误
            'errorText':装载文案(包['error'],翻译) if 包.get('error') is not None else None,#错误句
            'readOnlyText':装载文案({'code':包['readOnlyReason']},翻译) if 包.get('readOnlyReason') is not None else None,#只读句
            'configured':包['name'] in 账本['bundles'],#自有配置
            'bundleConfigSlot':{'name':'plugins.bundle.config','view':'page','entryKey':包['name']},#配置槽
            'partsSummary':部件摘要(包['rows'],翻译) if len(包['rows'])>0 else None,#摘要
            'showFilter':len(包['rows'])>行筛选阈值,#筛选
            'filter':自身.行筛选,#筛选值
            'rows':行视图,#行
            'filterEmpty':len(包['rows'])>0 and len(行视图)==0,#无匹配
            'labels':{#文案
                'backToList':翻译('backToList'),
                'crumbRoot':翻译('crumbRoot'),
                'uninstall':翻译('uninstall'),
                'uninstallLabel':翻译('uninstallLabel',{'name':文['title']}),
                'enableToggle':翻译('enableToggle',{'name':文['title']}),
                'partsLabel':翻译('partsLabel'),
                'partsEmpty':翻译('partsEmpty'),
                'partsFilter':翻译('partsFilter'),
                'partsFilterEmpty':翻译('partsFilterEmpty'),
                'reasonLabel':翻译('reasonLabel'),
                'versionTag':翻译('versionTag',{'version':包['version']}) if 包.get('version') is not None else None,
                'statusBeta':翻译('statusBeta'),
                'statusProblem':翻译('statusProblem'),
                'configureRow':翻译('configureRow'),
            },#文案结束
            'actions':{#动作
                'back':自身.回列表,#回
                'setEnabled':lambda 启:属性['setEnabled'](包['name'],启),#启停
                'uninstall':lambda:属性['uninstall'](包['name']),#卸载
                'setFilter':自身.设行筛选,#筛选
            },#动作结束
            'subject':{'kind':'bundle','pkg':{'name':包['name'],'installed':自身._已装(包),'enabled':包['enabled'] is True if 'enabled' in 包 else False}},#详情槽主体
        }#详情结束

    def _行详情(自身,包,行,翻译,属性):
        '行配置详情'
        文=包文案(包,翻译)#文案
        键=行配置键(包['name'],行['rowId'])#键
        return {#详情
            'kind':'row-detail',#种类
            'key':键,#键
            'rowId':行['rowId'],#行 id
            'moduleName':行['moduleName'],#模块
            'description':自身._行说明(行),#说明；没有则回退 summary 槽
            'summarySlot':{'name':'plugins.row.config','view':'summary','entryKey':键},#摘要
            'pageSlot':{'name':'plugins.row.config','view':'page','entryKey':键},#页面
            'labels':{#文案
                'back':翻译('backToPackage',{'name':文['title']}),
                'crumb':文['title'],
            },#文案结束
            'actions':{'back':lambda 名=包['name']:自身.回包(名)},#回
            'subject':{'kind':'row','row':{'rowId':行['rowId'],'moduleName':行['moduleName'],'enabled':行['enabled'] is True if 'enabled' in 行 else False}},#详情槽主体
        }#详情结束

    def _条目详情(自身,项,翻译,属性):
        '官方插件详情'
        return {#详情
            'kind':'item-detail',#种类
            'id':项['id'],#id
            'label':项['label'],#标签
            'summarySlot':{'name':'plugins.item','view':'summary','only':项['id']},#摘要
            'pageSlot':{'name':'plugins.item','view':'page','only':项['id']},#页面
            'labels':{'backToList':翻译('backToList'),'crumbRoot':翻译('crumbRoot')},#文案
            'actions':{'back':自身.回列表},#回
            'subject':{'kind':'item','id':项['id']},#详情槽主体
        }#详情结束

    def _安装视图(自身,安装,翻译):
        '安装对话框视图'
        阶段=安装['phase']#阶段
        结果={#基础
            'open':安装['open'],
            'phase':阶段,#阶段
            'spec':安装['spec'],#规格
            'guideOpen':自身.引导开,#引导
            'detailsOpen':安装['detailsOpen'],#详情
            'runs':安装['runs'],#运行
            'subject':安装['subject'],#主体
            'enabling':安装['enabling'],#启用中
            'installed':安装['installed'],#已装名
            'restartRequired':安装['restartRequired'],#需重启
            'approvedBuilds':安装['approvedBuilds'],#已允许
            'failure':安装['failure'],#失败
            'inputError':安装['inputError'],#输入错
            'pending':是否安装待决(阶段),#待决
            'guideExamples':[{#引导例
                'key':例['key'],
                'title':翻译(例['titleKey']),
                'example':翻译(例['exampleKey']),
                'hint':翻译(例['hintKey']),
            } for 例 in 引导示例],
        }#基础结束
        if 安装['inputError'] is not None:#输入错
            错=安装['inputError']#错
            结果['inputErrorText']=翻译(输入问题键[错['problem']],{'reason':错['reason']})#句
        if 阶段 not in ('idle','checking'):#后续屏
            结果['heading']=翻译(屏标题键[阶段])#标题
            结果['failureText']=失败文案(安装['failure'],翻译) if 阶段=='failed' else None#失败句
            if 安装['subject'] is not None:#主体卡
                主体=安装['subject']#主体
                种键=主体种类键.get(主体['kind'])#种类键
                结果['subjectCard']={#卡
                    'title':主体['name'] if 'name' in 主体 and 主体['name'] is not None else 主体['spec'],#标题
                    'description':主体['description'] if 'description' in 主体 and 主体['description'] is not None else (翻译(种键) if 种键 is not None else None),#描述
                    'version':翻译('installVersion',{'version':主体['version']}) if 'version' in 主体 and 主体['version'] is not None else None,#版本
                }#卡结束
            待=安装['failure']['pendingBuilds'] if 阶段=='failed' and 安装['failure'] is not None and 'pendingBuilds' in 安装['failure'] else []#待允许
            结果['pendingBuilds']=待 if 待 is not None else []#待
            结果['approvable']=len(结果['pendingBuilds'])>0#可批准
        属性=自身.属性#props
        结果['actions']={#动作
            'close':属性['closeInstall'],
            'editSpec':属性['editInstallSpec'],
            'run':属性['runInstall'],
            'cancel':属性['cancelInstall'],
            'cancelAndClose':属性['cancelInstallAndClose'],
            'toggleDetails':属性['toggleInstallDetails'],
            'enableNow':属性['enableInstalled'],
            'approveBuilds':属性['approveBuildsAndRetry'],
            'toggleGuide':自身.切换引导,
        }#动作结束
        结果['labels']={#文案键投影（常用）
            'installTitle':翻译('installTitle'),
            'installDescription':翻译('installDescription'),
            'installSpecLabel':翻译('installSpecLabel'),
            'installSpecPlaceholder':翻译('installSpecPlaceholder'),
            'installRun':翻译('installRun'),
            'installChecking':翻译('installChecking'),
            'installGuideToggle':翻译('installGuideToggle'),
            'installGuideHide':翻译('installGuideHide'),
            'installGuideIntro':翻译('installGuideIntro'),
            'installGuideIdNote':翻译('installGuideIdNote'),
            'installGuideExampleLabel':翻译('installGuideExampleLabel'),
            'installGuideFill':翻译('installGuideFill'),
            'installGuideSafety':翻译('installGuideSafety'),
            'close':翻译('close'),
            'installEdit':翻译('installEdit'),
            'installCancel':翻译('installCancel'),
            'installCancelling':翻译('installCancelling'),
            'installCloseCancels':翻译('installCloseCancels'),
            'installDetailsShow':翻译('installDetailsShow'),
            'installDetailsHide':翻译('installDetailsHide'),
            'installRetry':翻译('installRetry'),
            'installEnableNow':翻译('installEnableNow'),
            'installClose':翻译('installClose'),
            'installApprovalTitle':翻译('installApprovalTitle'),
            'installApprovalDescription':翻译('installApprovalDescription'),
            'installApprovalConsequence':翻译('installApprovalConsequence'),
            'installApprovalCaution':翻译('installApprovalCaution'),
            'installApproveAndRetry':翻译('installApproveAndRetry'),
            'installDoneNothing':翻译('installDoneNothing'),
            'installDoneRestart':翻译('installDoneRestart'),
            'installLocation':翻译('installLocation'),
            'terminalNoOutput':翻译('terminalNoOutput'),
        }#文案结束
        return 结果#安装视图

    def _确认视图(自身,确认,翻译):
        '卸载确认视图'
        if 确认 is None:
            return None#无
        文=包文案({'name':确认['packageName']},翻译)#文案
        return {#确认
            'action':确认['action'],#动作
            'packageName':确认['packageName'],#包名
            'title':翻译('confirmUninstallTitle',{'name':文['title']}),#标题
            'description':翻译('confirmUninstallDescription'),#说明
            'confirmLabel':翻译('confirmUninstall'),#确认
            'cancelLabel':翻译('cancel'),#取消
            'closeLabel':翻译('close'),#关闭
            'actions':{#动作
                'confirm':自身.属性['confirm'],
                'cancel':自身.属性['cancelConfirm'],
            },#动作结束
        }#确认结束

    def _安放(自身,界面):
        '复用根列'
        旧=getattr(自身,'根',None)
        if 旧 is not None:
            try:
                旧.clear()
                return 旧
            except Exception as 错误:
                自身.根=None
                自身.画面失败=页面失败文案(错误)
        自身.根=界面.column().classes('插件装载页根 page')
        return 自身.根

    def _画开关(自身,界面,启用,禁用,回调):
        '启停开关；值未变则不重画'
        def 改(事件,写=回调):
            '写入启停'
            下一=事件.value is True
            if 下一==启用:
                return
            写(下一)
            自身.渲染()
        开关=界面.switch(value=启用 is True,on_change=改)
        if 禁用 is True:
            开关.disable()

    def _画槽(自身,槽):
        '声明过的配置席由宿主画；没有 renderSlot 时跳过'
        渲=自身.属性['renderSlot'] if 'renderSlot' in 自身.属性 else None
        if 渲 is None or not isinstance(槽,dict) or 'name' not in 槽:
            return
        拥有={}
        if 'view' in 槽:
            拥有['view']=槽['view']
        选项={}
        if 'entryKey' in 槽 and 槽['entryKey'] is not None:
            选项['entryKey']=槽['entryKey']
        if 'only' in 槽 and 槽['only'] is not None:
            选项['only']=槽['only']
        渲(槽['name'],拥有,选项 if len(选项)>0 else None)

    def _画拥有槽(自身,名,拥有,选项=None):
        '直接把拥有方属性交给已声明的槽'
        渲=自身.属性['renderSlot'] if 'renderSlot' in 自身.属性 else None
        if 渲 is None:#没装
            return#跳过
        渲(名,拥有 if isinstance(拥有,dict) else {},选项)#画

    def _画点(自身,界面,态):
        '行或失败旁的状态点'
        if 态 in ('ongoing','error','done','warning'):#四态
            状态点({'state':态,'size':10}).渲染()#点
            return#已画
        if 态=='idle':#空闲；状态点类会把未知态画成完成
            界面.html('<span aria-hidden="true" class="状态点 点" data-state="idle" style="width:10px;height:10px"></span>',sanitize=False)#闲点

    def _画卡(自身,界面,卡):
        '组合包或官方条目卡'
        def 点开():
            '进入详情'
            卡['actions']['open']()
            自身.渲染()
        界面.button(卡['title'] if 'title' in 卡 else 卡['label'],on_click=点开).props('flat no-caps align=left')
        描述=卡['description'] if 'description' in 卡 else None
        if isinstance(描述,str) and 描述!='':
            界面.label(描述)
        if 'summarySlot' in 卡:
            自身._画槽(卡['summarySlot'])
        if 卡.get('beta') is True:
            界面.label(卡['statusBeta'] if 'statusBeta' in 卡 and isinstance(卡['statusBeta'],str) else 'Beta')
        if 卡.get('status')=='problem':
            界面.label(卡['statusProblem'] if 'statusProblem' in 卡 and isinstance(卡['statusProblem'],str) else '')
        版本=卡['versionTag'] if 'versionTag' in 卡 else None
        if isinstance(版本,str) and 版本!='':
            界面.label(版本)
        if 卡['kind']=='package-card':
            def 写启停(启,名=卡['name'],写=卡['actions']['setEnabled']):
                '记下刚启用的包，供启用后槽使用'
                if 启 is True:
                    自身.激活名=名
                elif 自身.激活名==名:
                    自身.激活名=None
                写(启)
            自身._画开关(界面,卡['enabled'],卡['busy'] is True or 卡.get('readOnlyReason') is not None,写启停)

    def _画安装(自身,界面,安装):
        '安装对话框'
        if not isinstance(安装,dict) or 安装.get('open') is not True:
            return
        文=安装['labels']
        动作=安装['actions']
        with 界面.dialog() as 对话框:
            with 界面.card():
                界面.label(文['installTitle'])
                界面.label(文['installDescription'])
                if 安装['phase'] in ('idle','checking'):
                    def 改规格(事件):
                        '写入安装规格'
                        动作['editSpec'](事件.value)
                    界面.input(文['installSpecLabel'],value=安装['spec'],placeholder=文['installSpecPlaceholder'],on_change=改规格)
                    if isinstance(安装.get('inputErrorText'),str) and 安装['inputErrorText']!='':
                        界面.label(安装['inputErrorText'])
                    def 点引导():
                        '展开或收起安装引导'
                        动作['toggleGuide']()
                        自身.渲染()
                    界面.button(文['installGuideHide'] if 安装['guideOpen'] is True else 文['installGuideToggle'],on_click=点引导).props('flat no-caps')
                    if 安装['guideOpen'] is True:
                        界面.label(文['installGuideIntro'])
                        for 例 in 安装['guideExamples']:
                            界面.label(例['title'])
                            界面.label(例['example'])
                            界面.label(例['hint'])
                            def 点填(_事件=None,文本=例['example']):
                                '把示例填进规格'
                                动作['editSpec'](文本)
                                自身.渲染()
                            界面.button(文['installGuideFill'],on_click=点填).props('flat no-caps')
                        界面.label(文['installGuideSafety'])
                    def 点安装():
                        '开始安装'
                        动作['run']()
                        自身.渲染()
                    跑=界面.button(文['installChecking'] if 安装['phase']=='checking' else 文['installRun'],on_click=点安装)
                    if 安装['pending'] is True or (isinstance(安装['spec'],str) and 安装['spec'].strip()==''):
                        跑.disable()
                else:
                    if isinstance(安装.get('heading'),str) and 安装['heading']!='':
                        界面.label(安装['heading'])
                    主体=安装.get('subjectCard')
                    if isinstance(主体,dict):
                        界面.label(主体['title'])
                        if isinstance(主体['description'],str) and 主体['description']!='':
                            界面.label(主体['description'])
                        if isinstance(主体['version'],str) and 主体['version']!='':
                            界面.label(主体['version'])
                    if isinstance(安装.get('failureText'),str) and 安装['failureText']!='':
                        界面.label(安装['failureText'])
                    待建=安装['pendingBuilds'] if 'pendingBuilds' in 安装 and 安装['pendingBuilds'] is not None else []
                    if len(待建)>0:
                        界面.label(文['installApprovalTitle'])
                        界面.label(文['installApprovalDescription'])
                        for 名 in 待建:
                            界面.label(名 if isinstance(名,str) else str(名))
                        def 点批准():
                            '允许构建并重试'
                            动作['approveBuilds']()
                            自身.渲染()
                        界面.button(文['installApproveAndRetry'],on_click=点批准)
                    if 安装['phase']=='done':
                        界面.label(文['installDoneRestart'] if 安装['restartRequired'] is True else 文['installDoneNothing'])
                        if isinstance(安装['installed'],str) and 安装['installed']!='':
                            def 点启用():
                                '立刻启用'
                                动作['enableNow']()
                                自身.渲染()
                            界面.button(文['installEnableNow'],on_click=点启用)
                    def 点详情():
                        '展开或收起输出'
                        动作['toggleDetails']()
                        自身.渲染()
                    界面.button(文['installDetailsHide'] if 安装['detailsOpen'] is True else 文['installDetailsShow'],on_click=点详情).props('flat no-caps')
                    if 安装['detailsOpen'] is True:
                        运行=安装['runs'] if 安装['runs'] is not None else []
                        if len(运行)==0:
                            界面.label(文['terminalNoOutput'])
                        else:
                            for 段 in 运行:
                                if isinstance(段,dict):
                                    命令=段['command'] if 'command' in 段 else ''
                                    输出=段['output'] if 'output' in 段 and 段['output'] is not None else ''
                                    if 命令!='':
                                        界面.label(命令)
                                    if 输出!='':
                                        界面.label(输出).style('white-space:pre-wrap')
                                    elif 命令=='':
                                        界面.label(文['terminalNoOutput'])
                                elif isinstance(段,str) and 段!='':
                                    界面.label(段).style('white-space:pre-wrap')
                    def 点取消安装():
                        '取消安装'
                        动作['cancel']()
                        自身.渲染()
                    界面.button(文['installCancelling'] if 安装['phase']=='cancelling' else 文['installCancel'],on_click=点取消安装).props('flat no-caps')
                def 点关():
                    '关闭安装；进行中则取消并关闭'
                    if 安装['pending'] is True and 安装['phase'] not in ('idle','checking'):
                        动作['cancelAndClose']()
                    else:
                        动作['close']()
                    自身.渲染()
                界面.button(文['close'],on_click=点关).props('flat no-caps')
        对话框.open()

    def _画确认(自身,界面,确认):
        '卸载确认'
        if 确认 is None:
            return
        with 界面.dialog() as 对话框:
            with 界面.card():
                界面.label(确认['title'])
                界面.label(确认['description'])
                def 点确认():
                    '确认卸载'
                    确认['actions']['confirm']()
                    自身.渲染()
                def 点取消():
                    '取消卸载'
                    确认['actions']['cancel']()
                    自身.渲染()
                界面.button(确认['confirmLabel'],on_click=点确认)
                界面.button(确认['cancelLabel'],on_click=点取消).props('flat no-caps')
        对话框.open()

    def 渲染(自身):
        '列表、详情、安装对话框与卸载确认'
        if 't' not in 自身.属性:#槽位还没给文案
            return#不画
        视=自身.视图()
        with 自身._安放(界面):
            失败句=getattr(自身,'画面失败',None)
            if isinstance(失败句,str) and 失败句!='':
                自身.画面失败=None
                界面.label(失败句)
            if 视 is None:#钩子还没绑上
                界面.label(自身.属性['t']('loading'))
                return#先画再停
            文=视['labels']
            界面.label(文['title'])
            界面.label(文['intro'])
            忙=isinstance(视['busy'],list) and len(视['busy'])>0
            with 界面.row():
                def 点刷新():
                    '重读清单'
                    视['actions']['refresh']()
                    自身.渲染()
                刷=界面.button(文['refresh'],on_click=点刷新).props('flat no-caps')
                def 点添加():
                    '打开安装并收起菜单'
                    自身.添加开=False
                    视['actions']['openInstall']()
                    自身.渲染()
                加=界面.button(文['addPlugin'],on_click=点添加)
                def 点更多():
                    '展开添加方式'
                    自身.添加开=not 自身.添加开
                    自身.渲染()
                界面.button(on_click=点更多).props('icon=expand_more flat')
                if 忙:
                    刷.disable()
                    加.disable()
            if 自身.添加开:
                with 界面.column().classes('plugin-add-menu'):
                    界面.button(自身.属性['t']('installTitle'),on_click=点添加).props('flat no-caps align=left')
                    def 关菜单():
                        '收起添加菜单'
                        自身.添加开=False
                        自身.渲染()
                    自身._画拥有槽('plugins.add.actions',{'onDismiss':关菜单})
            if isinstance(视['noticeLine'],str) and 视['noticeLine']!='':
                界面.label(视['noticeLine'])
                def 点关提示():
                    '关掉提示'
                    视['actions']['dismissNotice']()
                    自身.渲染()
                界面.button(on_click=点关提示).props('icon=close flat round')
            if 视['status']=='loading' or 视['loaded'] is not True:
                if 视['status']=='error':
                    自身._画点(界面,'error')
                    界面.label(文['error'])
                    def 点重试():
                        '再读'
                        视['actions']['refresh']()
                        自身.渲染()
                    界面.button(文['retry'],on_click=点重试).props('flat no-caps')
                elif 视['status']=='unavailable':
                    界面.label(文['unavailable'])
                else:
                    界面.label(文['loading'])
            elif 'rowDetail' in 视:
                详情=视['rowDetail']
                def 点回():
                    '回到组合包'
                    详情['actions']['back']()
                    自身.渲染()
                界面.button(详情['labels']['back'],on_click=点回).props('flat no-caps')
                自身._画拥有槽('plugins.detail.actions',{'subject':详情['subject']})
                界面.label(详情['moduleName'])
                界面.label(详情['rowId'])
                自身._画拥有槽('plugins.detail.badge',{'subject':详情['subject']})
                if isinstance(详情.get('description'),str) and 详情['description']!='':
                    界面.label(详情['description'])
                else:
                    自身._画槽(详情['summarySlot'])
                自身._画槽(详情['pageSlot'])
                自身._画拥有槽('plugins.detail.section',{'subject':详情['subject']})
            elif 'packageDetail' in 视:
                详情=视['packageDetail']
                def 点回():
                    '回到列表'
                    详情['actions']['back']()
                    自身.渲染()
                界面.button(详情['labels']['backToList'],on_click=点回).props('flat no-caps')
                自身._画拥有槽('plugins.detail.actions',{'subject':详情['subject']})
                界面.label(详情['title'])
                自身._画拥有槽('plugins.detail.badge',{'subject':详情['subject']})
                if isinstance(详情['description'],str) and 详情['description']!='':
                    界面.label(详情['description'])
                if 详情.get('configured') is True:
                    自身._画槽(详情['bundleConfigSlot'])
                if isinstance(详情['labels']['versionTag'],str) and 详情['labels']['versionTag']!='':
                    界面.label(详情['labels']['versionTag'])
                if isinstance(详情['errorText'],str) and 详情['errorText']!='':
                    界面.label(详情['errorText'])
                if isinstance(详情['readOnlyText'],str) and 详情['readOnlyText']!='':
                    界面.label(详情['readOnlyText'])
                自身._画开关(界面,详情['enabled'],详情['busy'] is True or 详情.get('readOnlyReason') is not None,详情['actions']['setEnabled'])
                if 详情['installed'] is True:
                    def 点卸():
                        '请求卸载'
                        详情['actions']['uninstall']()
                        自身.渲染()
                    界面.button(详情['labels']['uninstall'],on_click=点卸).props('flat no-caps')
                界面.label(详情['labels']['partsLabel'])
                if isinstance(详情['partsSummary'],str) and 详情['partsSummary']!='':
                    界面.label(详情['partsSummary'])
                if 详情['showFilter'] is True:
                    def 改筛选(事件):
                        '过滤行'
                        if 事件.value==自身.行筛选:
                            return
                        自身.设行筛选(事件.value)
                        自身.渲染()
                    界面.input(详情['labels']['partsFilter'],value=详情['filter'],on_change=改筛选)
                if 详情['filterEmpty'] is True:
                    界面.label(详情['labels']['partsFilterEmpty'])
                elif len(详情['rows'])==0:
                    界面.label(详情['labels']['partsEmpty'])
                for 行 in 详情['rows']:
                    自身._画点(界面,行['dotState'] if 'dotState' in 行 else 'idle')
                    界面.label(行['moduleName'])
                    界面.label(行['stateText'])
                    自身._画开关(界面,行['enabled'],行['busy'] is True or 行['locked'] is True,行['actions']['setEnabled'])
                    if 行['hasConfig'] is True:
                        钮文=行['configureLabel'] if 'configureLabel' in 行 else 详情['labels']['configureRow']
                        def 点配置(_事件=None,回调=行['actions']['openConfig']):
                            '打开行配置'
                            回调()
                            自身.渲染()
                        界面.button(钮文,on_click=点配置).props('flat no-caps')
                自身._画拥有槽('plugins.detail.section',{'subject':详情['subject']})
            elif 'itemDetail' in 视:
                详情=视['itemDetail']
                def 点回():
                    '回到列表'
                    详情['actions']['back']()
                    自身.渲染()
                界面.button(详情['labels']['backToList'],on_click=点回).props('flat no-caps')
                自身._画拥有槽('plugins.detail.actions',{'subject':详情['subject']})
                界面.label(详情['label'])
                自身._画拥有槽('plugins.detail.badge',{'subject':详情['subject']})
                自身._画槽(详情['summarySlot'])
                自身._画槽(详情['pageSlot'])
                自身._画拥有槽('plugins.detail.section',{'subject':详情['subject']})
            elif 视['showsCards'] is True:
                官方=视['officialCards'] if 'officialCards' in 视 else []
                已装=视['bundleCards'] if 'bundleCards' in 视 else []
                if len(官方)==0 and len(已装)==0 and 视['status']!='error':
                    界面.label(文['empty']).classes('empty')
                if len(官方)>0:
                    界面.label(文['officialTitle'])
                    for 卡 in 官方:
                        自身._画卡(界面,卡)
                if len(已装)>0:
                    界面.label(文['bundlesTitle'])
                    for 卡 in 已装:
                        自身._画卡(界面,卡)
                if 视['status']=='error':
                    自身._画点(界面,'error')
                    界面.label(文['error'])
                    def 点列表重试():
                        '再读'
                        视['actions']['refresh']()
                        自身.渲染()
                    界面.button(文['retry'],on_click=点列表重试).props('flat no-caps')
                if isinstance(自身.激活名,str) and 自身.激活名!='':
                    def 关激活():
                        '关掉启用后提示'
                        自身.激活名=None
                        自身.渲染()
                    def 开激活详情(名=自身.激活名):
                        '进入刚启用的包'
                        自身.激活名=None
                        自身.开包(名)
                        自身.渲染()
                    自身._画拥有槽('plugins.bundle.activation',{
                        'packageName':自身.激活名,
                        'onDismiss':关激活,
                        'onOpenDetails':开激活详情,
                    },{'entryKey':自身.激活名})
            自身._画安装(界面,视['install'])
            自身._画确认(界面,视['confirm'])

    def __call__(自身,属性=None):
        '对齐 React 调用'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
