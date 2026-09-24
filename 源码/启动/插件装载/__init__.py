"""当前配置档的插件与组合包装载，复用共享 dsh 插件包操作。"""
import os,re,json,copy,threading
from uuid import uuid4 as 生成uuid4
from ...依赖.schemastery import 字符串字段,自然数字段,正整数字段,列表字段
from .注册表 import 规范化注册表,注册表计划,归因失败,npmmirror注册表
from ...工具.原子写入 import 带文件锁,原子写文件
from ...工具.超时 import 中止控制器,合成信号,若已中止则抛出,已中止
from ...typert.协议 import 远程服务,远程
from ..app启动 import (
    读配置清单,
    解析组合包目录,
    加载覆盖补丁,
    组合条目,
    加载可选补丁,
    加载配置目录,
    启动包含表,
    未激活条目,
    激活诊断,
)
from ..app启动.配置档 import 配置补丁文件名
from .操作 import 组合包清单,跑配置档pnpm,保存清单,查看配置档包,读配置档注册表
from .安装失败 import 分类安装失败
from .安装规格 import 非法安装规格错误,解析安装规格
from .补丁 import 写插件启用
from .失败 import 装载失败
from .构建审批 import 批准构建,读待决构建
from . import 类型
from . import 安装失败 as 安装失败模块
from . import 安装规格 as 安装规格模块

__all__=[
    '装载服务','配置','分类安装失败','非法安装规格错误','解析安装规格',
    '类型','安装失败模块','安装规格模块',
]

#常量
受保护模块=set([#装载自身依赖的模块，不可经配置档补丁改
    '@deepseek-ai/dsh-plugin-manager','@deepseek-ai/cordis-plugin-loader',
    '@deepseek-ai/cordis-plugin-include','@deepseek-ai/dsh-api-gateway',
    '@deepseek-ai/dsh-host-webserver','@deepseek-ai/dsh-client-modules',
    '@deepseek-ai/dsh-client-ui-settings-plugin-inventory','@deepseek-ai/dsh-client-ui-plugin-manager',
    '@deepseek-ai/dsh-host-plugin-inventory','@deepseek-ai/dsh-typert-registry',
    '@deepseek-ai/dsh-api-remotes',
    '@deepseek-ai/cordis-plugin-timer','@deepseek-ai/dsh-client-connection',
    '@deepseek-ai/dsh-host-frontend-static','@deepseek-ai/dsh-tools',
    '@deepseek-ai/dsh-hmr',
])
恢复文件=('package.json','pnpm-lock.yaml')#安装失败时恢复的文件
ANSI序列=re.compile(r'\x1b\[[0-9;]*m',re.ASCII)#pnpm 色码
#app启动尚未迁入时本包装同源字面量
可选组合包=[
    '@deepseek-ai/dsh-experimental-agent-team-profile',
    '@deepseek-ai/dsh-experimental-agent-team-web-profile',
]
遥测行编号='session-telemetry-otel'

配置={
    'pnpmCommand':字符串字段(默认值='pnpm'),
    'outputBytes':正整数字段(默认值=16384),
    'lockWaitMs':自然数字段(默认值=120000),
    'inspectTimeoutMs':正整数字段(默认值=20000,最小=1000),
    'githubConnectionTimeoutMs':正整数字段(默认值=5000,最小=1000),
    'idleTimeoutMs':正整数字段(默认值=600000,最小=1000),
    'registry':字符串字段(可空=True),
    'fallbackRegistries':列表字段(字符串字段(),默认值=[npmmirror注册表]),
}

#工具
def 展平行表(行表):
    """只展平配置档补丁组合器可寻址的组。"""
    结果=[]#扁平行
    for 行 in 行表:#逐行
        结果.append(行)#自身
        if 行.get('group') and isinstance(行.get('config'),list):#组且 config 为列表
            结果.extend(展平行表(行['config']))#递归
    return 结果#扁平

def 错误消息(错误):
    """保留确切诊断，含非 Exception 失败。"""
    return 错误.args[0] if isinstance(错误,Exception) and len(错误.args)>0 else str(错误)#消息

def 装载错误(错误):
    """预期拒绝保留码；其它变为 operation-error 并携带确切诊断。"""
    if isinstance(错误,装载失败):#预期
        return {'code':错误.code}#仅码
    return {'code':'operation-error','diagnostic':错误消息(错误)}#操作错误

def 字符串字段值(清单,字段):
    """清单上的字符串字段，有则返回。"""
    值=清单.get(字段) if isinstance(清单,dict) else None#取值
    return 值 if isinstance(值,str) else None#仅字符串

def 检查结果自清单(种类,清单,注册表):
    """包清单所说：身份、一句话、是否组合包。"""
    dsh=清单.get('dsh') if isinstance(清单,dict) else None#dsh
    声明=dsh if isinstance(dsh,dict) else None#对象
    组合包=声明 is not None and isinstance(声明.get('bundle'),dict)#是否声明组合包
    名称=字符串字段值(清单,'name')#名
    版本=字符串字段值(清单,'version')#版本
    描述=字符串字段值(清单,'description')#描述
    结果={'status':'accepted','kind':种类,'bundle':组合包,'registry':注册表}#基结果
    if 名称 is not None:#有名
        结果['name']=名称#写入
    if 版本 is not None:#有版本
        结果['version']=版本#写入
    if 描述 is not None and 描述!='':#有描述
        结果['description']=描述#写入
    return 结果#检查结果

def 印刷错误(印刷):
    """pnpm 印在 stdout 的 {error:{code,message}} 合成一行。"""
    try:
        解析=json.loads(印刷 or 'null')
    except Exception:
        return ''
    错误=解析.get('error') if isinstance(解析,dict) else None
    if not isinstance(错误,dict):
        return ''
    段=[项 for 项 in (错误.get('code'),错误.get('message')) if isinstance(项,str)]
    return '  '.join(段)

def 拒绝检查(问题,理由):
    """构造拒绝检查。"""
    return {'status':'refused','problem':问题,'reason':理由}#拒绝

def 插件条目标识(值):
    """Loader 树条目 id 在清单边界的品牌（恒等）。"""
    return 值#原样

def 读插件清单(上下文):
    """直接读 Loader 当前非组条目；对齐宿主插件清单投影。"""
    加载器=上下文.loader#加载器服务
    列举=getattr(加载器,'列出插件配置',None)#中文列举
    条目表=[]#条目
    源=列举() if 列举 is not None else []#迭代源
    for 配置 in 源:#逐条
        选项=配置.选项 if hasattr(配置,'选项') else {}#选项
        if 选项.get('group'):#组
            continue#跳过
        编号=配置.编号 if hasattr(配置,'编号') else 选项.get('id')#编号
        纤程=配置.纤程 if hasattr(配置,'纤程') else None#纤程
        已禁用=配置.已禁用 if hasattr(配置,'已禁用') else bool(选项.get('disabled'))#禁用
        相位=None#纤程相位
        if 纤程 is not None:#有纤程
            状态=纤程.状态#状态
            相位对照={0:'pending',1:'loading',2:'active',3:'failed',5:'unloading'}#对照
            相位=相位对照.get(状态)#相位；DISPOSED→null
        条目表.append({#清单条目
            'entryId':插件条目标识(编号),#条目标识
            'moduleName':选项.get('name'),#模块名
            'enabled':not 已禁用,#启用
            'fiberPhase':相位,#相位
        })#条目结束
    结果={'entries':条目表}#快照
    if getattr(上下文,'pluginManager',None) is not None:#装载可用
        结果['managementAvailable']=True#标记
    return 结果#快照

def 解析遥测补丁(禁用环境,有行):
    """遥测退出开关→启动补丁。"""
    if (禁用环境 or '')=='' or not 有行:#无需
        return None#无补丁
    return {'id':遥测行编号,'disabled':True}#禁用遥测行

def 读配置补丁(二进制名,配置档,初始配置=None):
    """读当前组合包与用户层并叠启动时 overlay。"""
    if 初始配置 is not None:#已加载
        配置=初始配置#用给定
    else:#读盘
        配置=加载配置目录(二进制名,配置档['dir'],配置档['installAnchor'],{'userLayer':False})#加载
    层补丁=[]#层补丁
    for 层 in 配置.get('layers') or []:#各层
        层补丁.extend(层.get('patches') or [])#展开
    用户补丁=配置.get('patches') if 初始配置 is not None else (加载可选补丁(二进制名,配置档['patchPath']) or [])#用户层
    主目录补丁=加载可选补丁(二进制名,os.path.join(配置档['home'],配置补丁文件名)) or []#主目录层
    补丁=copy.deepcopy(层补丁+用户补丁+主目录补丁+list(配置档.get('overlays') or []))#脱离
    有遥测=any(行.get('id')==遥测行编号 for 行 in 组合条目([补丁]))#是否有遥测行
    遥测=解析遥测补丁(配置档.get('telemetryDisabledEnv'),有遥测)#遥测补丁
    if 遥测 is not None:#需要
        补丁.append(遥测)#追加
    return 补丁#有序补丁

def 未激活诊断(失败项):
    """单条未激活诊断文本。"""
    return 失败项['diagnostic']#诊断

def 调和配置补丁(根上下文,补丁,二进制名,必需编号=None):
    """应用一整代补丁并等待 Loader 激活诊断。"""
    if 必需编号 is None:#缺省
        必需编号=[]#空
    if id(根上下文) not in 启动包含表:#缺失
        raise Exception(二进制名+': 配置档重载需要根 Include 条目')
    条目=启动包含表[id(根上下文)]#根 Include
    先前失败=[]#先前失败快照
    for 失败 in 未激活条目(根上下文):#收集
        纤程=失败['entry'].纤程#纤程
        先前失败.append({#快照
            'entry':失败['entry'],#条目
            'diagnostic':未激活诊断(失败),#诊断
            'fiber':纤程,#纤程
            'options':json.dumps(失败['entry'].选项,ensure_ascii=False,separators=(',',':'),allow_nan=False),#选项
        })#快照结束
    先前纤程=[]#先前纤程
    for 配置 in 根上下文.loader.列出插件配置():#逐条
        if 配置.纤程 is not None:#有纤程
            先前纤程.append({'fiber':配置.纤程,'failed':配置.纤程.状态 in (3,4)})#FAILED/DISPOSED
    旧配置=条目.选项.get('config') if hasattr(条目,'选项') else {}#Include 配置
    新配置=dict(旧配置) if isinstance(旧配置,dict) else {}#拷贝
    新配置['patches']=补丁#写入补丁
    条目.更新({'config':新配置})#更新 Include
    拒绝原因=[]#新抛出
    for 项 in 先前纤程:#等旧纤程
        try:#等待
            项['fiber'].等待()#等待
        except Exception as 错误:#失败
            if not 项['failed']:#先前未失败
                拒绝原因.append(错误)#记下
    根上下文.loader.等待()#等树
    失败=未激活条目(根上下文)#新失败
    引入=[]#新引入失败
    for 失败项 in 失败:#逐条
        编号=失败项['entry'].选项.get('id')#id
        必需=编号 in 必需编号#必需目标
        旧同=False#是否旧有
        for 先前 in 先前失败:#比对
            if (先前['entry'] is 失败项['entry'] and 先前['fiber'] is 失败项['entry'].纤程
                    and 先前['options']==json.dumps(失败项['entry'].选项,ensure_ascii=False,separators=(',',':'),allow_nan=False)
                    and 先前['diagnostic']==未激活诊断(失败项)):#同失败
                旧同=True#旧有
                break#停
        if 必需 or not 旧同:#新失败
            引入.append(失败项)#收下
    if len(引入)>0:#有新失败
        raise Exception(激活诊断(二进制名,'warning',引入).rstrip())#与上游 activationDiagnostic 字面一致
    if len(拒绝原因)>0:#旧纤程新抛
        raise 拒绝原因[0]#抛首条
    return [未激活诊断(项) for 项 in 失败]#警告列表

class 安装已取消错误(Exception):
    """调用方停止安装；文件已恢复后抛出。"""
    def __init__(自身):
        """固定消息。"""
        super().__init__('安装已取消')
        自身.name='InstallCancelledError'#错误名

class 装载服务(远程服务):
    """管理配置档文件并应用其声明的重载生命周期。"""
    inject=['loader','profileContext']#框架依赖槽
    Config=配置#框架配置槽

    def __init__(自身,上下文,配置值):
        """登记 pluginManager 远程服务并记下配置档事实。"""
        super().__init__(上下文,'pluginManager')#服务键线协议
        纤程=上下文.纤程#所属纤程
        插件配置=纤程.插件配置 if 纤程 is not None else None#插件配置
        自身.拥有条目标识=插件配置.编号 if 插件配置 is not None else None#拥有条目
        自身.拥有上下文=上下文#拥有上下文
        自身.配置档=上下文.profileContext#配置档事实（跨包 dict）
        自身.输出字节=配置值['outputBytes']#诊断上限
        自身.锁等待毫秒=配置值['lockWaitMs']#锁等待
        自身.检查超时毫秒=配置值['inspectTimeoutMs']#检查超时
        自身.github连接超时毫秒=配置值['githubConnectionTimeoutMs']#GitHub 探测超时
        自身.空闲超时毫秒=配置值['idleTimeoutMs']#包操作静默超时
        自身.pnpm命令=配置值['pnpmCommand']#pnpm
        注册表值=配置值['registry'] if 'registry' in 配置值 else None#首选注册表
        回退=配置值['fallbackRegistries'] if 'fallbackRegistries' in 配置值 else [npmmirror注册表]#回退
        自身.已配置注册表={
            'registry':None if 注册表值 is None else 规范化注册表(注册表值),
            'fallbackRegistries':[规范化注册表(项) for 项 in 回退],
        }
        自身.中止=中止控制器()#整服务中止
        自身.包操作集=set()#进行中的包操作事件
        自身.安装表={}#请求 id → 安装控制
        def 拆除工厂():
            """包取消拆除工厂。"""
            def 拆除():
                """中止并等包操作结束。"""
                自身.中止.中止()#中止
                for 事件 in list(自身.包操作集):#逐个
                    事件.wait()#等待结束
            return 拆除#拆除器
        上下文.副作用(拆除工厂,'plugin-manager: package cancellation')#登记

    @远程
    def 列出插件(自身):
        """读当前插件，含为何不能经配置档补丁改动。"""
        行表=展平行表(组合条目([读配置补丁('dsh',自身.配置档)]))#补丁行
        快照=读插件清单(自身.ctx)#清单
        结果=[]#插件信息
        for 条目 in 快照['entries']:#逐条
            实际=None#活条目
            for 配置 in 自身.ctx.loader.列出插件配置():#查找
                if 配置.编号==条目['entryId']:#命中
                    实际=配置#记下
                    break#停
            候选=[行 for 行 in 行表 if 行.get('id')==(实际.选项.get('id') if 实际 is not None else None)]#候选
            一条=候选[0] if len(候选)>0 else None#首候选
            if 条目['moduleName'] in 受保护模块 or 条目['entryId']==自身.拥有条目标识:#受保护
                项=dict(条目)#拷贝
                项['readOnlyReason']='management-required'#只读
                结果.append(项)#收下
                continue#下一条
            拥有编号=None#Include 检查
            if 实际 is not None:#有活条目
                父树=实际.父组.所属树 if hasattr(实际,'父组') and 实际.父组 is not None else None#父树
                if 父树 is not None:#有树
                    树纤程=父树.所属上下文.纤程#树纤程
                    拥有=树纤程.插件配置 if 树纤程 is not None else None#拥有配置
                    拥有编号=拥有.编号 if 拥有 is not None else None#编号
            if (一条 is None or len(候选)>1 or 一条.get('name')!=条目['moduleName']
                    or 拥有编号!='include'):#不可寻址
                项=dict(条目)#拷贝
                项['readOnlyReason']='unaddressable'#只读
                结果.append(项)#收下
                continue#下一条
            项=dict(条目)#拷贝
            项['patchId']=一条['id']#补丁 id
            结果.append(项)#收下
        return 结果#插件列表

    @远程
    def 列出组合包(自身):
        """读已装组合包、安装提供的组合包，及已选却非组合包的名字。"""
        清单=读配置清单('dsh',自身.配置档['dir'])#配置档清单
        已选=list(((清单.get('dsh') or {}).get('profile') or {}).get('bundles') or [])#已选
        依赖=list((清单.get('dependencies') or {}).keys())#依赖
        安装文件=open(自身.配置档['installAnchor'],'r',encoding='utf-8')#安装清单
        try:#读
            安装清单=json.loads(安装文件.read())#解析
        finally:#关
            安装文件.close()#关闭
        安装依赖=安装清单.get('dependencies') or {}#安装依赖
        名称集=list(dict.fromkeys(已选+依赖+list(安装依赖.keys())))#去重保序
        组合包表=[]#结果
        for 名称 in 名称集:#逐名
            已装=名称 in 依赖#已装
            可选=名称 in 可选组合包#可选
            可卸=已装 and 名称 not in 安装依赖#可卸
            启用=名称 in 已选#启用
            try:#读元数据
                信息=组合包清单(名称,自身.配置档['dir'],自身.配置档['installAnchor'])#元数据
                if 信息 is None:#非组合包
                    if 启用:#仅已选才列
                        组合包表.append({'name':名称,'enabled':启用,'installed':已装,'optional':可选,'removable':可卸,'error':{'code':'not-bundle'},'rows':[],'overrides':[]})#问题行
                    continue#下一名
                只读= 'management-required' if 自身.保护装载(名称) else None#只读
                行={'name':名称,'enabled':启用,'installed':已装,'optional':可选,'removable':可卸 and 只读 is None}#基行
                版本=字符串字段值(信息,'version')#版本
                描述=字符串字段值(信息,'description')#描述
                if 版本 is not None:#有版本
                    行['version']=版本#写入
                if 描述 is not None and 描述!='':#有描述
                    行['description']=描述#写入
                if 只读 is not None:#只读
                    行['readOnlyReason']=只读#写入
                行.update(自身.声明行(名称,信息))#rows/overrides
                组合包表.append(行)#收下
            except Exception as 错误:#读失败
                if 启用 or 已装:#可见
                    组合包表.append({'name':名称,'enabled':启用,'installed':已装,'optional':可选,'removable':可卸,'error':装载错误(错误),'rows':[],'overrides':[]})#错误行
        return 组合包表#列表

    @远程
    def 列出注册表(自身):
        """读本装载询问的注册表：配置首选、回退、以及 pnpm 自己配置命名的那份。"""
        包管理=自身.配置档.get('packageManager') or {'command':自身.pnpm命令}#包管理
        查看选项=dict(包管理)#选项
        查看选项['timeoutMs']=自身.检查超时毫秒#超时
        return {
            'registry':自身.已配置注册表['registry'],
            'fallbackRegistries':list(自身.已配置注册表['fallbackRegistries']),
            'resolved':读配置档注册表(自身.配置档['dir'],查看选项),
        }

    @远程
    def 检查规格(自身,规格,选项=None,信号=None):
        """安装前读出规格指向什么。"""
        if 选项 is None:
            选项={}
        try:
            解析=解析安装规格(规格)
        except 非法安装规格错误 as 错误:
            return 拒绝检查('invalid-spec',错误.reason)
        清单=读配置清单('dsh',自身.配置档['dir'])
        安装文件=open(自身.配置档['installAnchor'],'r',encoding='utf-8')
        try:
            安装清单=json.loads(安装文件.read())
        finally:
            安装文件.close()
        已知=set(list(((清单.get('dsh') or {}).get('profile') or {}).get('bundles') or [])+list((清单.get('dependencies') or {}).keys())+list((安装清单.get('dependencies') or {}).keys()))
        计划=注册表计划(选项.get('registry'),自身.列出注册表())
        注册表=计划[0]
        种类=解析['kind']
        if 种类=='git':
            出={'status':'accepted','kind':'git','bundle':None,'registry':注册表}
            if 'host' in 解析:
                出['host']=解析['host']
            return 出
        if 种类=='tarball':
            路径=解析.get('path')
            if 路径 is not None and not os.path.exists(路径):
                return 拒绝检查('not-a-package','压缩包不存在')
            出={'status':'accepted','kind':'tarball','bundle':None,'registry':注册表}
            if 'host' in 解析:
                出['host']=解析['host']
            return 出
        if 种类=='path':
            if not os.path.exists(解析['path']):
                return 拒绝检查('not-a-package','路径不存在')
            try:
                包文件=open(os.path.join(解析['path'],'package.json'),'r',encoding='utf-8')
                try:
                    读出=json.loads(包文件.read())
                finally:
                    包文件.close()
            except Exception as 错误:
                return 拒绝检查('not-a-package','该路径没有可读的 package.json: '+错误消息(错误))
            检查=检查结果自清单('path',读出,注册表)
            if 'name' not in 检查:
                return 拒绝检查('not-a-package','package.json 没有包名')
            if 检查['name'] in 已知:
                return 拒绝检查('already-installed',检查['name']+' 已安装')
            if not 检查['bundle']:
                return 拒绝检查('not-a-bundle',检查['name']+' 未声明 dsh.bundle')
            return 检查
        if 种类=='registry':
            if 解析['name'] in 已知:
                return 拒绝检查('already-installed',解析['name']+' 已安装')
            已问=[]
            def 带表拒绝(问题,理由):
                """拒绝并带上已问注册表。"""
                出=拒绝检查(问题,理由)
                出['registries']=list(已问)
                return 出
            for 当前 in 计划:
                已问.append(当前)
                包管理=自身.配置档.get('packageManager') or {'command':自身.pnpm命令}
                查看选项=dict(包管理)
                查看选项['timeoutMs']=自身.检查超时毫秒
                查看选项['registry']=当前
                if 信号 is not None:
                    查看选项['signal']=信号
                查看=查看配置档包(自身.配置档['dir'],规格.strip(),查看选项)
                印刷=ANSI序列.sub('',(查看.get('stdout') or '')).strip()
                if 查看.get('exitCode')!=0 or 'cause' in 查看 or 查看.get('timedOut'):
                    日志='\n'.join([项 for 项 in ((查看.get('stderr') or '').strip(),印刷错误(印刷),(错误消息(查看['cause']) if 'cause' in 查看 else '')) if 项])
                    事实={'log':日志,'timedOut':bool(查看.get('timedOut'))}
                    if 'cause' in 查看:
                        事实['cause']=查看['cause']
                    失败种=分类安装失败(事实)
                    if len(已问)<len(计划) and not 已中止(信号) and 归因失败(失败种,日志,解析)=='registry':
                        continue
                    理由=('pnpm view 超时，毫秒 '+str(自身.检查超时毫秒)) if 查看.get('timedOut') else (日志 or 印刷 or ('pnpm view 退出码 '+str(查看.get('exitCode'))))
                    if 失败种 in ('not-found','no-matching-version'):
                        return 带表拒绝('not-found',理由)
                    if 失败种 in ('network','timeout'):
                        return 带表拒绝('network',理由)
                    return 带表拒绝('unknown',理由)
                try:
                    原文=印刷 or 'null'
                    答复=json.loads(原文)
                except Exception as 错误:
                    return 带表拒绝('unknown','无法阅读 pnpm view 输出: '+错误消息(错误))
                最新=答复[-1] if isinstance(答复,list) else 答复
                if not isinstance(最新,dict) or 最新 is None:
                    return 带表拒绝('unknown','pnpm view 没有返回包')
                检查=检查结果自清单('registry',最新,当前)
                if 'name' not in 检查:
                    命名=dict(检查)
                    命名['name']=解析['name']
                else:
                    命名=检查
                if not 命名['bundle']:
                    return 带表拒绝('not-a-bundle',命名['name']+' 未声明 dsh.bundle')
                return 命名
        raise Exception('不可达的安装规格种类')

    @远程
    def 设置插件启用(自身,标识,启用):
        """持久化插件条目启停并在现场配置档上应用。"""
        def 作业(结果):
            """变更体。"""
            def 操作():
                """配置事务体。"""
                行=None#当前行
                for 项 in 自身.列出插件():#查找
                    if 项['entryId']==标识:#命中
                        行=项#记下
                        break#停
                if 行 is None:#未知
                    raise 装载失败('unknown-plugin')#拒绝
                if 'readOnlyReason' in 行 and 行['readOnlyReason'] is not None:#只读
                    raise 装载失败(行['readOnlyReason'])#拒绝
                写插件启用(自身.配置档['patchPath'],行['patchId'],行['moduleName'],启用)#写补丁
                结果['warnings']=自身.重载([行['patchId']] if 启用 else [])#重载
                当前=None#重读
                for 项 in 自身.列出插件():#查找
                    if 项['entryId']==标识:#命中
                        当前=项#记下
                        break#停
                if 当前 is not None and 当前.get('enabled')!=启用 and getattr(自身.拥有上下文,'hmr',None) is not None:#被覆盖
                    return 'overridden'#覆盖
                return None#默认应用态
            return 自身.配置事务(操作)#经 HMR 串行
        return 自身.变更(作业,{'stage':'enable','target':标识,'enabled':启用},'plugin')#变更

    @远程
    def 设置组合包启用(自身,名称,启用):
        """选择或去掉组合包层，保留已装依赖。"""
        def 作业(结果):
            """变更体。"""
            def 操作():
                """配置事务体。"""
                自身.选择组合包(名称,启用)#选入/去掉
                结果['warnings']=自身.重载([行.get('id') for 行 in 自身.组合包行(名称)] if 启用 else [])#重载
            return 自身.配置事务(操作)#经 HMR
        return 自身.变更(作业,{'stage':'enable','target':名称,'enabled':启用},'bundle')#变更

    @远程
    def 安装组合包(自身,规格,选项=None):
        """用与 dsh plugin 相同的 pnpm 路径安装包；失败或取消恢复 package.json 与 pnpm-lock.yaml。"""
        if 选项 is None:#缺省
            选项={}#空
        请求标识=选项.get('requestId')#请求 id
        控制={'abort':中止控制器(),'phase':'installing','settled':threading.Event()}#安装控制
        def 已停():
            """是否已取消。"""
            return 控制['abort'].信号.已中止()#已中止
        if 请求标识 is not None:#有 id
            自身.安装表[请求标识]=控制#登记
        def 通告(阶段):
            """通告安装阶段。"""
            if 请求标识 is not None:#有 id
                自身.拥有上下文.广播('plugin-manager/install-state',{'requestId':请求标识,'phase':阶段})#事件
        def 作业(结果):
            """安装变更体。"""
            if 规格.strip()=='' or 规格.startswith('-'):#非法规格
                raise 装载失败('invalid-spec')#拒绝
            if 已停():#已取消
                raise 安装已取消错误()#取消
            if 'approvedBuilds' in 选项 and 选项['approvedBuilds'] is not None:#批准构建
                批准构建(自身.配置档['dir'],选项['approvedBuilds'])#持久化
                结果['approvedBuilds']=选项['approvedBuilds']#记下
            文件=自身.读恢复文件()#快照
            之前=(读配置清单('dsh',自身.配置档['dir']).get('dependencies') or {})#装前依赖
            通告('installing')#阶段
            名称=None#装入名
            try:#pnpm add
                结果['packageResult']=自身.跑pnpm(['add',规格],控制['abort'].信号,请求标识)#跑
                if 已停():#取消
                    raise 安装已取消错误()#取消
                if 结果['packageResult']['exitCode']!=0:#失败
                    try:#读待决
                        结果['pendingBuilds']=读待决构建(自身.配置档['dir'])#待决
                    except Exception as 错误:#读失败
                        自身.拥有上下文.日志.警告('pnpm 失败后无法读取待决构建审批',错误)
                    raise Exception(结果['packageResult']['output'])#带输出失败
                之后=(读配置清单('dsh',自身.配置档['dir']).get('dependencies') or {})#装后
                已装=[名 for 名 in 之后.keys() if 之前.get(名)!=之后[名]]#变化名
                if len(已装)==0:#无变化则按规格猜
                    已装=[名 for 名 in 之后.keys() if 规格==名 or 规格.startswith(名+'@')]#保留范围
                if len(已装)!=1:#歧义
                    raise 装载失败('ambiguous-install')#拒绝
                名称=已装[0]#目标名
                目录=解析组合包目录('dsh',名称,自身.配置档['installAnchor'],自身.配置档['dir'])#包目录
                清单=组合包清单(名称,自身.配置档['dir'],自身.配置档['installAnchor'])#元数据
                if 'patch' not in (((清单 or {}).get('dsh') or {}).get('bundle') or {}):#无补丁
                    raise 装载失败('not-bundle')#拒绝
                加载覆盖补丁('dsh',os.path.join(目录,清单['dsh']['bundle']['patch']))#加载
            except Exception as 错误:#恢复
                自身.恢复文件(文件)#恢复
                raise 错误#再抛
            控制['phase']='applying'#进入应用
            通告('applying')#通告
            结果['bundle']=名称#记下
            结果['target']=名称#目标
            结果['stage']='enable'#阶段
            def 启用操作():
                """选入并重载。"""
                if 选项.get('enabled') is not False:#默认启用
                    自身.选择组合包(名称,True)#选入
                if 名称 in 之前:#替换已有
                    return 'restart-required'#需重启
                if 选项.get('enabled') is not False:#启用则重载
                    结果['warnings']=自身.重载()#重载
                return None#默认
            return 自身.配置事务(启用操作)#配置事务
        try:#跑变更
            return 自身.变更(作业,{'stage':'install','target':规格,'enabled':选项.get('enabled') is not False},'install')#变更
        finally:
            控制['settled'].set()#已结算
            if 请求标识 is not None:#有 id
                自身.安装表.pop(请求标识,None)#摘掉

    @远程
    def 取消安装(自身,请求标识):
        """停止本服务拥有的安装并等到文件恢复。"""
        if 请求标识 not in 自身.安装表:#无此 id
            return {'status':'not-running'}#未运行
        控制=自身.安装表[请求标识]#控制
        if 控制['phase']=='applying':#已应用
            return {'status':'too-late'}#太晚
        自身.拥有上下文.广播('plugin-manager/install-state',{'requestId':请求标识,'phase':'cancelling'})#通告
        控制['abort'].中止()#中止
        控制['settled'].wait()#等结算
        return {'status':'cancelled'}#已取消

    @远程
    def 移除组合包(自身,名称):
        """经 dsh plugin 的 pnpm 路径卸载并移除配置档拥有的组合包依赖。"""
        def 作业(结果):
            """移除变更体。"""
            def 操作():
                """配置事务体。"""
                组合=None#目标
                for 项 in 自身.列出组合包():#查找
                    if 项['name']==名称:#命中
                        组合=项#记下
                        break#停
                if 组合 is None or not 组合.get('removable'):#不可卸
                    raise 装载失败('not-removable')#拒绝
                if getattr(自身.拥有上下文,'hmr',None) is None:#无 HMR
                    启动中=名称 in list(自身.配置档.get('startedBundles') or [])#启动用过
                    活着=False#是否仍活
                    for 行 in 自身.组合包行(名称):#行
                        for 配置 in 自身.ctx.loader.列出插件配置():#活条目
                            if 配置.选项.get('id')==行.get('id') and 配置.纤程 is not None:#仍活
                                活着=True#标记
                    if 启动中 or 活着:#需停进程
                        raise 装载失败('stop-profile')#拒绝
                贡献=自身.组合包行(名称) if 'error' not in 组合 or 组合.get('error') is None else []#贡献行
                if 组合.get('enabled'):#已启用
                    自身.选择组合包(名称,False)#去掉
                    结果['warnings']=自身.重载()#重载
                for 配置 in 自身.ctx.loader.列出插件配置():#仍占用？
                    if 配置.纤程 is not None and getattr(配置.纤程,'编号',None) is not None:#有 uid
                        for 行 in 贡献:#贡献
                            if 行.get('id')==配置.选项.get('id') and 行.get('name')==配置.选项.get('name'):#命中
                                raise 装载失败('bundle-in-use')#占用
            自身.配置事务(操作)#先卸运行时
            结果['packageResult']=自身.跑pnpm(['remove',名称])#pnpm remove
            if 结果['packageResult']['exitCode']!=0:#失败
                raise Exception(结果['packageResult']['output'])#带输出
        return 自身.变更(作业,{'stage':'remove','target':名称},'remove')#变更

    def 声明行(自身,名称,信息):
        """组合包补丁插入的行与其改写的已有行；不可读补丁则抛。"""
        补丁路径=((信息.get('dsh') or {}).get('bundle') or {}).get('patch')#补丁相对路径
        if 补丁路径 is None:#无
            return {'rows':[],'overrides':[]}#空
        目录=解析组合包目录('dsh',名称,自身.配置档['installAnchor'],自身.配置档['dir'])#包目录
        补丁列表=加载覆盖补丁('dsh',os.path.join(目录,补丁路径))#补丁
        存活={}#行 id → 条目标识
        for 配置 in 自身.ctx.loader.列出插件配置():#活条目
            编号=配置.选项.get('id')#id
            if isinstance(编号,str):#有 id
                存活[编号]=插件条目标识(配置.编号)#记下
        行表=[]#声明行
        for 行 in 展平行表(组合条目([[项 for 项 in 补丁列表 if 项.get('insert') is not None]])):#插入行
            if not isinstance(行.get('id'),str) or not isinstance(行.get('name'),str):#缺字段
                continue#跳过
            项={'rowId':行['id'],'moduleName':行['name']}#基行
            if 行['id'] in 存活:#有活条目
                项['entryId']=存活[行['id']]#挂上
            行表.append(项)#收下
        已声明=set(行['rowId'] for 行 in 行表)#已声明 id
        覆盖=[]#覆盖 id
        for 项 in 补丁列表:#逐补丁
            if 'insert' not in 项 and isinstance(项.get('id'),str) and 项['id'] not in 已声明:#改写
                if 项['id'] not in 覆盖:#去重
                    覆盖.append(项['id'])#收下
        return {'rows':行表,'overrides':覆盖}#声明

    def 跑pnpm(自身,参数列表,信号=None,请求标识=None):
        """在配置档内跑一条 pnpm，并把输出流式发为 install-log 块。"""
        作业标识=str(生成uuid4())#作业 id
        参数行=['pnpm']+list(参数列表)#argv
        工作目录=自身.配置档['dir']#cwd
        身份={} if 请求标识 is None else {'requestId':请求标识}#身份
        完成=threading.Event()#完成事件
        自身.包操作集.add(完成)#登记
        包管理=自身.配置档.get('packageManager') or {'command':自身.pnpm命令}#包管理
        选项=dict(包管理)#选项
        选项['execution']='service'#服务执行
        选项['outputBytes']=自身.输出字节#字节上限
        选项['idleTimeoutMs']=自身.空闲超时毫秒#静默超时
        选项['activateNewBundles']=False#不在此激活
        if 信号 is None:#无调用方信号
            选项['signal']=自身.中止.信号#仅服务中止
        else:#融合
            选项['signal']=合成信号(自身.中止.信号,信号)#合成
        def 输出回调(文本,流名):
            """转发日志块。"""
            块=dict(身份)#基
            块.update({'jobId':作业标识,'argv':参数行,'cwd':工作目录,'stream':流名,'text':文本})#字段
            自身.拥有上下文.广播('plugin-manager/install-log',块)#事件
        选项['onOutput']=输出回调#回调
        上下文={#操作上下文
            'profile':自身.配置档.get('name'),#名
            'dir':自身.配置档['dir'],#目录
            'installAnchor':自身.配置档['installAnchor'],#锚点
            'cwd':自身.配置档.get('cwd') or 自身.配置档['dir'],#调用 cwd
            'home':自身.配置档.get('home'),#主目录
        }#上下文结束
        try:#跑
            结果=跑配置档pnpm(上下文,参数列表,选项)#跑
            退出=None if (信号 is not None and 信号.is_set()) else 结果['exitCode']#退出码
            尾=dict(身份)#尾块
            尾.update({'jobId':作业标识,'argv':参数行,'cwd':工作目录,'stream':'stdout','text':'','exitCode':退出})#字段
            自身.拥有上下文.广播('plugin-manager/install-log',尾)#尾事件
            if 结果['exitCode']==0:#成功
                return 结果#原样
            分类=dict(结果)#失败
            分类['kind']=分类安装失败({'log':结果['output']})#种类
            return 分类#带种类
        except Exception as 错误:#失败
            错块=dict(身份)#错块
            错块.update({'jobId':作业标识,'argv':参数行,'cwd':工作目录,'stream':'stderr','text':错误消息(错误),'exitCode':None})#字段
            自身.拥有上下文.广播('plugin-manager/install-log',错块)#事件
            raise#再抛
        finally:#摘掉
            完成.set()#完成
            自身.包操作集.discard(完成)#摘掉

    def 读恢复文件(自身):
        """安装可能改写的配置档文件当前内容；缺失为 None。"""
        文件表={}#路径→内容
        for 名 in 恢复文件:#逐文件
            路径=os.path.join(自身.配置档['dir'],名)#路径
            if os.path.exists(路径):#存在
                句柄=open(路径,'r',encoding='utf-8')#打开
                try:#读
                    文件表[路径]=句柄.read()#内容
                finally:#关
                    句柄.close()#关闭
            else:#缺失
                文件表[路径]=None#无内容
        return 文件表#快照

    def 恢复文件(自身,文件表):
        """把配置档文件放回；pnpm 已退出后调用。"""
        for 路径,内容 in 文件表.items():#逐文件
            if 内容 is None:#本不存在
                try:#删
                    os.remove(路径)#删除
                except FileNotFoundError:#已无
                    pass#忽略
            else:#写回
                原子写文件(路径,内容,{'mode':0o600})#原子写

    def 选择组合包(自身,名称,启用):
        """改写 dsh.profile.bundles 有序列表。"""
        清单=读配置清单('dsh',自身.配置档['dir'])#清单
        先前=list(((清单.get('dsh') or {}).get('profile') or {}).get('bundles') or [])#先前
        if (启用 or 名称 not in 先前) and 组合包清单(名称,自身.配置档['dir'],自身.配置档['installAnchor']) is None:#须是组合包
            raise 装载失败('not-bundle')#拒绝
        if (not 启用) and 名称 in 先前:#关闭
            if 自身.保护装载(名称):#受保护
                raise 装载失败('management-required')#拒绝
        if 启用:#开启
            组合包=先前 if 名称 in 先前 else 先前+[名称]#追加
        else:#关闭
            组合包=[项 for 项 in 先前 if 项!=名称]#过滤
        if json.dumps(先前,ensure_ascii=False,separators=(',',':'),allow_nan=False)==json.dumps(组合包,ensure_ascii=False,separators=(',',':'),allow_nan=False):#无变化
            return#跳过
        dsh=dict(清单.get('dsh') or {})#dsh
        配置段=dict(dsh.get('profile') or {})#profile
        配置段['bundles']=组合包#写回
        dsh['profile']=配置段#写回
        清单=dict(清单)#拷贝
        清单['dsh']=dsh#写回
        保存清单(自身.配置档['dir'],清单)#保存

    def 组合包行(自身,名称):
        """组合包补丁展平后的条目选项行。"""
        信息=组合包清单(名称,自身.配置档['dir'],自身.配置档['installAnchor'])#元数据
        if 信息 is None or 'bundle' not in (信息.get('dsh') or {}):#无
            return []#空
        目录=解析组合包目录('dsh',名称,自身.配置档['installAnchor'],自身.配置档['dir'])#目录
        return 展平行表(组合条目([加载覆盖补丁('dsh',os.path.join(目录,信息['dsh']['bundle']['patch']))]))#行

    def 保护装载(自身,名称):
        """该组合包是否贡献受保护模块或拥有条目。"""
        for 行 in 自身.组合包行(名称):#逐行
            if 行.get('name') in 受保护模块 or ('include:'+str(行.get('id')))==自身.拥有条目标识:#保护
                return True
        return False#否

    def 配置事务(自身,操作):
        """有 HMR 则经独占队列跑配置变更。"""
        热=getattr(自身.拥有上下文,'hmr',None)#HMR
        def 执行():
            """跑前检查中止。"""
            若已中止则抛出(自身.中止.信号)#中止则抛
            return 操作()#跑
        if 热 is None:#无 HMR
            return 执行()#直接
        独占=getattr(热,'独占运行',None) or getattr(热,'runExclusive',None)#独占
        if 独占 is None:#尚未迁入
            return 执行()#直接
        return 独占(执行)#串行

    def 重载(自身,必需编号=None):
        """调和配置档补丁；无 HMR 则空警告。"""
        if 必需编号 is None:#缺省
            必需编号=[]#空
        if getattr(自身.拥有上下文,'hmr',None) is None:#无 HMR
            return []#空
        return 调和配置补丁(自身.拥有上下文.根,读配置补丁('dsh',自身.配置档),'dsh',必需编号)#调和

    def 变更(自身,操作,请求,原因):
        """持配置档清单锁跑一次变更并发 plugin-manager/changed。"""
        def 持锁():
            """持锁体。"""
            若已中止则抛出(自身.中止.信号)#中止则抛
            之前=自身.磁盘状态()#装前磁盘
            结果=dict(请求)#基结果
            结果['changed']=False#默认
            结果['application']='applied' if getattr(自身.拥有上下文,'hmr',None) is not None else 'restart-required'#应用态
            try:#跑操作
                应用=操作(结果)#可能改 application
                if 应用 is not None:#显式
                    结果['application']=应用#写入
            except 安装已取消错误:#取消
                结果['application']='cancelled'#取消
            except Exception as 错误:#失败
                结果['application']='failed'#失败
                结果['error']=装载错误(错误)#错误
            结果['changed']=之前!=自身.磁盘状态()#磁盘是否变
            自身.拥有上下文.广播('plugin-manager/changed',{'reason':原因})#事件
            return 结果#结果
        return 带文件锁(os.path.join(自身.配置档['dir'],'package.json'),持锁)#持锁

    def 磁盘状态(自身):
        """配置档关键文件拼接快照。"""
        块表=[]#块
        for 文件 in ('package.json','cordis.patch.yml','pnpm-workspace.yaml'):#逐文件
            路径=os.path.join(自身.配置档['dir'],文件)#路径
            try:#读
                句柄=open(路径,'r',encoding='utf-8')#打开
                try:#读
                    块表.append(句柄.read())#内容
                finally:#关
                    句柄.close()#关闭
            except FileNotFoundError:#缺失
                块表.append('')#空
        return '\0'.join(块表)#拼接

#框架槽
inject=装载服务.inject#Cordis 依赖
Config=装载服务.Config#Cordis 配置
default=装载服务#Cordis 默认导出
