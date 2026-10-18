import re
from ...存储 import 创建快照存储

__all__=['推导密钥引用','协议选项','推理档位选项','提供方可用','模型设置存储']

探测路由='\u0000probe'
密钥清洗=re.compile(r'[^A-Z0-9]+')

def 推导密钥引用(提供方):
    '路由标识大写后，非字母数字换成下划线，再加 _API_KEY'
    return 密钥清洗.sub('_',提供方.upper())+'_API_KEY'

def 协议选项(命名空间,模式):
    '从命名空间自己的 schema 读出可声明的协议标识'
    if 命名空间 is None:
        return []
    节点=模式['路径节点'](模式['再水合'](命名空间['schema']),['providers',探测路由,'api'])
    if isinstance(节点,dict) is False or 节点.get('type')!='union' or isinstance(节点.get('list'),list) is False:
        return []
    结果=[]
    for 项 in 节点['list']:
        值=项.get('value') if isinstance(项,dict) else None
        if isinstance(值,str):
            结果.append(值)
    return 结果

def 推理档位选项(命名空间,模式):
    '从同一份 schema 读出 reasoningEfforts 接受的档位，按升级顺序'
    if 命名空间 is None:
        return []
    路径=['providers',探测路由,'models','0','reasoningEfforts']
    节点=模式['路径节点'](模式['再水合'](命名空间['schema']),路径)
    分支=[]
    if isinstance(节点,dict) and isinstance(节点.get('list'),list):
        分支=节点['list']
    键模式=None
    for 支 in 分支:
        if isinstance(支,dict) and 支.get('type')=='dict':
            键模式=支.get('sKey')
            break
    列表=[]
    if isinstance(键模式,dict) and isinstance(键模式.get('list'),list):
        列表=键模式['list']
    结果=[]
    for 项 in 列表:
        值=项.get('value') if isinstance(项,dict) else None
        if isinstance(值,str):
            结果.append(值)
    return 结果

def 提供方可用(行):
    '路由已登记，且档案点名的凭据已经存上。没点名引用的走提供方自己的认证'
    if 行['entry']['active'] is not True:
        return False
    if 行['entry']['provider']=='deepseek-account':
        return 行.get('accountAvailable') is True
    if 行.get('apiKeyEnv') is None:
        return True
    凭据=行.get('credential')
    return isinstance(凭据,dict) and 凭据.get('configured') is True

class 模型设置存储:
    '拼合可配置提供方目录、设置命名空间和所引用的凭据'
    def __init__(自身,上下文,模式,描述面):
        '空闲快照。描述面是共享设置镜像'
        自身.上下文=上下文
        自身.模式=模式
        自身.描述面=描述面
        自身.存储=创建快照存储({
            'status':'idle',
            'error':None,
            'credentialError':None,
            'writable':False,
            'rows':[],
            'namespaces':{},
        })
        自身.世代=0

    def 加载(自身):
        '重读整页。后一次调用盖过还没发布的前一次'
        自身.世代=自身.世代+1
        自身.读取(自身.世代)

    def 读取(自身,世代):
        '目录和设置镜像读完后，再按引用批量描述凭据'
        def 标加载(状态):
            '进入加载并清掉整页错误'
            状态['status']='loading'
            状态['error']=None
        自身.存储.update(标加载)
        已注册=自身.上下文.remote.llm.listProviders()
        已声明=自身.上下文.remote.llm.listConfigurableProviders()
        自身.描述面.确保()
        if 世代!=自身.世代:
            return
        if 已注册['ok'] is not True:
            自身.失败(已注册['error']['message'])
            return
        if 已声明['ok'] is not True:
            自身.失败(已声明['error']['message'])
            return
        镜像=自身.描述面.getSnapshot()
        if 镜像.get('view') is None:
            if 镜像.get('error') is None:
                raise Exception('settings describe settled with neither a view nor an error')
            自身.失败(镜像['error'])
            return
        活跃=set()
        for 提供方 in 已注册['value']:
            活跃.add(提供方['id'])
        已有声明=set()
        for 条目 in 已声明['value']:
            已有声明.add(条目['provider'])
        目录=[]
        for 条目 in 已声明['value']:
            行={
                'provider':条目['provider'],
                'displayName':条目['displayName'],
                'settingsNs':条目['settingsNs'],
                'settingsPath':list(条目['settingsPath']),
                'active':条目['provider'] in 活跃,
            }
            if 'declared' in 条目 and 条目['declared'] is not None:
                行['declared']=条目['declared']
            if 'defaultBaseURL' in 条目 and 条目['defaultBaseURL'] is not None:
                行['defaultBaseURL']=条目['defaultBaseURL']
            if 'baseURLEnv' in 条目 and 条目['baseURLEnv'] is not None:
                行['baseURLEnv']=条目['baseURLEnv']
            if 'nativeAuth' in 条目 and 条目['nativeAuth'] is not None:
                行['nativeAuth']=条目['nativeAuth']
            if 'error' in 条目 and 条目['error'] is not None:
                行['error']=条目['error']
            目录.append(行)
        for 提供方 in 已注册['value']:
            if 提供方['id'] in 已有声明:
                continue
            目录.append({
                'provider':提供方['id'],
                'displayName':提供方['name'],
                'settingsNs':'',
                'settingsPath':[],
                'active':True,
            })
        def 排序键(行):
            '账号、官方 DeepSeek，然后保持原顺序'
            if 行['provider']=='deepseek-account':
                return 0
            if 行['provider']=='deepseek-official':
                return 1
            return 2
        目录.sort(key=排序键)
        可写=镜像['view']['writable']
        空间={}
        for 视图 in 镜像['view']['namespaces']:
            空间[视图['ns']]=视图
        行表=[]
        for 条目 in 目录:
            命名空间=空间.get(条目['settingsNs'])
            已配置=命名空间 is not None and (
                len(条目['settingsPath'])==0
                or 自身.模式['取路径'](命名空间['value'],条目['settingsPath']) is not None
            )
            可移除=命名空间 is not None and len(条目['settingsPath'])>0 and 自身.模式['有路径'](命名空间['user'],条目['settingsPath']) and 自身.模式['有路径'](命名空间['base'],条目['settingsPath']) is False
            引用=None
            if 条目['provider']!='deepseek-account' and 命名空间 is not None:
                档案=自身.模式['取路径'](命名空间['value'],条目['settingsPath'])
                if isinstance(档案,dict):
                    名=档案.get('apiKeyEnv')
                    if isinstance(名,str) and len(名)>0:
                        引用=名
            行表.append({
                'entry':条目,
                'configured':已配置,
                'removable':可移除,
                'apiKeyEnv':引用,
                'credential':None,
            })
        有账号=False
        for 行 in 行表:
            if 行['entry']['provider']=='deepseek-account':
                有账号=True
                break
        if 有账号:
            名录=自身.上下文.remote.session.modelCatalog()
            账号可用=False
            if 名录['ok'] is True:
                for 组 in 名录['value']['groups']:
                    if 组['id']=='deepseek-account' and len(组['models'])>0:
                        账号可用=True
                        break
            for 行 in 行表:
                if 行['entry']['provider']=='deepseek-account':
                    行['accountAvailable']=账号可用
        引用集=[]
        见过=set()
        for 行 in 行表:
            if 行['entry']['provider']=='deepseek-account':
                continue
            if 行.get('apiKeyEnv') is None:
                名单=[推导密钥引用(行['entry']['provider'])]
                原生=行['entry'].get('nativeAuth')
                if isinstance(原生,dict) and isinstance(原生.get('env'),list):
                    名单.extend(原生['env'])
            else:
                名单=[行['apiKeyEnv']]
            for 引用 in 名单:
                if 引用 not in 见过:
                    见过.add(引用)
                    引用集.append(引用)
        凭证={}
        凭证错误=None
        起点=0
        while 起点<len(引用集):
            应答=自身.上下文.remote.credentials.describe(引用集[起点:起点+64])
            if 应答['ok'] is True:
                if isinstance(应答.get('value'),dict):
                    凭证.update(应答['value'])
            else:
                凭证错误=应答['error']['message']
                break
            起点=起点+64
        if 世代!=自身.世代:
            return
        发布=[]
        for 行 in 行表:
            if 行['entry']['provider']=='deepseek-account':
                if 行.get('accountAvailable') is True:
                    发布.append(行)
                continue
            点名=None
            if 行.get('apiKeyEnv') is not None:
                点名=凭证.get(行['apiKeyEnv'])
            派生=None
            if 行.get('apiKeyEnv') is None:
                派生=凭证.get(推导密钥引用(行['entry']['provider']))
            下一=dict(行)
            if 点名 is not None:
                下一['credential']=点名
            if 派生 is not None:
                下一['derivedCredential']=派生
            if 凭证错误 is None:
                检查={}
                if 行.get('apiKeyEnv') is None:
                    原生=行['entry'].get('nativeAuth')
                    检查引用=原生.get('env') if isinstance(原生,dict) and isinstance(原生.get('env'),list) else []
                else:
                    检查引用=[行['apiKeyEnv']]
                for 引用 in 检查引用:
                    if 引用 in 凭证:
                        检查[引用]=凭证[引用]
                下一['credentialChecks']=检查
            发布.append(下一)
        def 标就绪(状态):
            '发布拼好的行和命名空间'
            状态['status']='ready'
            状态['error']=None
            状态['credentialError']=凭证错误
            状态['writable']=可写
            状态['rows']=发布
            状态['namespaces']=空间
        自身.存储.update(标就绪)

    def 失败(自身,消息):
        '整页读取失败。已有行留着，错误文案换上这次的'
        def 标失败(状态):
            '记下失败文案'
            状态['status']='error'
            状态['error']=消息
        自身.存储.update(标失败)
