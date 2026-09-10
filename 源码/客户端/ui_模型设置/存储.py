"""模型设置页存储与首次引导就绪度投影。

对齐上游 `ui-settings-models/src/client/store.ts`。公开面仅中文名。
"""
import re#正则
from ..模式表单 import 再水合模式,取路径,有路径#schema 路径

__all__=[#仅中文公开名
    '模型设置错误','快照存储','错误文案','推导密钥引用','协议选项','提供方可用','引导就绪度','模型设置存储','已加载则刷新','拼合提供方目录',
]#公开面结束

探测路由='\u0000probe'#探测用路由键
密钥引用清洗=re.compile(r'[^A-Z0-9]+',re.ASCII)#非常量字符

def 拼合提供方目录(已注册,目录):#拼合在线路由与可配置声明
    """对齐 joinProviderDirectory：声明行在前，其后补无声明的在线路由；可选带上 declared/error。"""
    活跃=set()#在线 id
    for 提供方 in 已注册:#每条在线
        if 'id' in 提供方:#有 id
            活跃.add(提供方['id'])#记入
    已声明=set()#已声明 id
    for 条目 in 目录:#每条声明
        if 'provider' in 条目:#有路由
            已声明.add(条目['provider'])#记入
    行表=[]#拼合结果
    for 条目 in 目录:#声明行
        行={#基础字段
            'provider':条目['provider'] if 'provider' in 条目 else None,#路由
            'displayName':条目['displayName'] if 'displayName' in 条目 else None,#显示名
            'settingsNs':条目['settingsNs'] if 'settingsNs' in 条目 else None,#命名空间
            'settingsPath':list(条目['settingsPath']) if 'settingsPath' in 条目 and 条目['settingsPath'] is not None else [],#路径副本
            'active':('provider' in 条目 and 条目['provider'] in 活跃),#是否在线
        }#基础结束
        if 'declared' in 条目 and 条目['declared'] is not None:#可选 declared
            行['declared']=条目['declared']#带上
        if 'error' in 条目 and 条目['error'] is not None:#可选 error
            行['error']=条目['error']#带上
        行表.append(行)#记入
    for 提供方 in 已注册:#补无声明的在线
        标识=提供方['id'] if 'id' in 提供方 else None#id
        if 标识 is None or 标识 in 已声明:#已有声明
            continue#跳过
        行表.append({#追加在线未声明行
            'provider':标识,#路由
            'displayName':提供方['name'] if 'name' in 提供方 else 标识,#显示名
            'settingsNs':'',#无设置命名空间
            'settingsPath':[],#无设置路径
            'active':True,#在线
        })#追加结束
    return 行表#拼合结果

class 模型设置错误(Exception):
    """本包异常基类。"""
    def __init__(自身,消息):
        """记下英文消息。"""
        super().__init__(消息)#消息原样英文

def 错误文案(错误):#拒绝值收成可展示文案
    """Error 取其 message。"""
    return str(错误)#文案

def 推导密钥引用(提供方):#由提供方路由推导凭证引用名
    """大写后非常量字符换成 _，再加 _API_KEY。"""
    return 密钥引用清洗.sub('_',提供方.upper(),count=0)+'_API_KEY'#推导

def 协议选项(命名空间):#从所属命名空间 schema 读出协议选项
    """schema 没有则空列表。"""
    if 命名空间 is None:#无
        return []#空
    模式=命名空间['schema'] if 'schema' in 命名空间 else None#schema
    节点=取路径(再水合模式(模式),['providers',探测路由,'api'])#api 节点
    支=None#联合成员
    if 节点 is not None and 'anyOf' in 节点:#anyOf 键在
        支=节点['anyOf']#anyOf
    if 支 is None and 节点 is not None and 'oneOf' in 节点:#oneOf 键在
        支=节点['oneOf']#oneOf
    if 支 is None:#皆无
        return []#空
    if len(支)==0:#空联合
        return []#空
    结果=[]#协议标识
    for 项 in 支:#成员
        值=项['const'] if 'const' in 项 else None#常量
        if isinstance(值,str):#字符串
            结果.append(值)#记入
    return 结果#选项

def 密钥引用于(命名空间,路径):#从已解析 profile 取出 apiKeyEnv
    """非空字符串才算引用。"""
    if 命名空间 is None:#无
        return None#无
    值=命名空间['value'] if 'value' in 命名空间 else None#已解析值
    档=取路径(值,路径)#profile
    if not isinstance(档,dict):#非对象
        return None#无
    引用=档['apiKeyEnv'] if 'apiKeyEnv' in 档 else None#字段
    return 引用 if isinstance(引用,str) and len(引用)>0 else None#引用

class 快照存储:#简易快照存储
    """页面快照 + 订阅。"""
    def __init__(自身,初值):#播种
        """记下初值。"""
        自身.状态=dict(初值)#状态
        自身.监听者=set()#订阅者

    def getSnapshot(自身):#读快照
        """返回当前状态。"""
        return 自身.状态#状态

    def subscribe(自身,回调):#订阅
        """登记变更回调。"""
        自身.监听者.add(回调)#加入
        def 退订():#退订
            """取消。"""
            自身.监听者.discard(回调)#删除
        return 退订#退订器

    def update(自身,变换):#就地变换并通知
        """调用变换(state)。"""
        变换(自身.状态)#变换
        for 回调 in list(自身.监听者):#通知
            回调()#触发

class 模型设置存储:#模型设置页控制器
    """拼合提供方目录、设置命名空间与所引用凭证。"""
    def __init__(自身,接口):#注入 API
        """空闲快照。"""
        自身.接口=接口#settings/credentials/llm
        自身.存储=快照存储({#页面快照
            'status':'idle','error':None,'credentialError':None,'writable':False,'rows':[],'namespaces':{},
        })#存储结束
        自身.世代=0#在飞请求世代

    def load(自身):#刷新整页快照
        """目录与命名空间并行拉取，再批量凭证 describe。"""
        自身.世代+=1#抬世代
        世代=自身.世代#本请求
        def 标加载(态):#loading
            """标 loading。"""
            态['status']='loading'#加载中
            态['error']=None#清错误
        自身.存储.update(标加载)#写入
        try:#并行拉
            目录应答=自身.接口.llm.providers({}).等待()#提供方目录
            设置应答=自身.接口.settings.describe({}).等待()#设置描述
            目录结果=目录应答['result']#目录业务
            设置结果=设置应答['result']#设置业务
            if not 目录结果['ok']:#目录失败
                错误体=目录结果['error'] if 'error' in 目录结果 else None#错误
                raise 模型设置错误(错误体['message'] if 错误体 is not None and 'message' in 错误体 else None)#抛
            if not 设置结果['ok']:#设置失败
                错误体=设置结果['error'] if 'error' in 设置结果 else None#错误
                raise 模型设置错误(错误体['message'] if 错误体 is not None and 'message' in 错误体 else None)#抛
            目录值=目录结果['value'] if 'value' in 目录结果 else None#目录值
            设置值=设置结果['value'] if 'value' in 设置结果 else None#设置值
            提供方表=目录值['providers'] if 目录值 is not None and 'providers' in 目录值 and 目录值['providers'] is not None else []#目录
            可写=bool(设置值['writable']) if 设置值 is not None and 'writable' in 设置值 else False#可写
            视图表=设置值['namespaces'] if 设置值 is not None and 'namespaces' in 设置值 and 设置值['namespaces'] is not None else []#命名空间
        except Exception as 错误:#整页失败；RPC 异常契约未定
            if 世代!=自身.世代:#过期
                return#丢弃
            def 写错误(态):#整页错误
                """保留上次好行。"""
                态['status']='error'#错误
                态['error']=错误文案(错误)#文案
            自身.存储.update(写错误)#写入
            return#结束
        命名空间图={视['ns']:视 for 视 in 视图表}#按 ns
        行表=[]#提供方行
        for 条目 in 提供方表:#每条目录
            名=条目['settingsNs'] if 'settingsNs' in 条目 else None#所属 ns 名
            命名空间=命名空间图[名] if 名 in 命名空间图 else None#所属 ns
            路径=条目['settingsPath'] if 'settingsPath' in 条目 and 条目['settingsPath'] is not None else []#设置路径
            解析值=命名空间['value'] if 命名空间 is not None and 'value' in 命名空间 else None#已解析
            用户层=命名空间['user'] if 命名空间 is not None and 'user' in 命名空间 else None#用户层
            基层=命名空间['base'] if 命名空间 is not None and 'base' in 命名空间 else None#基层
            已配置=命名空间 is not None and (len(路径)==0 or 取路径(解析值,路径) is not None)#已配置
            可删=命名空间 is not None and len(路径)>0 and 有路径(用户层,路径) and not 有路径(基层,路径)#可删回 base
            行表.append({#一行
                'entry':条目,#目录条目
                'configured':已配置,#已配置
                'removable':可删,#可删
                'apiKeyEnv':密钥引用于(命名空间,路径),#凭证引用
                'credential':None,#稍后补全
            })#行结束
        引用表=list({行['apiKeyEnv'] for 行 in 行表 if 行['apiKeyEnv'] is not None})#去重引用
        凭证图={}#引用→凭证
        凭证错误=None#补全文案
        if len(引用表)>0:#有引用
            try:#描述凭证
                应答=自身.接口.credentials.describe({'refs':引用表}).等待()#批量
                结果=应答['result']#业务
                if 结果['ok']:#成功
                    值=结果['value'] if 'value' in 结果 else None#值
                    凭证图=值['credentials'] if 值 is not None and 'credentials' in 值 and 值['credentials'] is not None else {}#图
                else:#业务拒绝
                    错误体=结果['error'] if 'error' in 结果 else None#错误
                    凭证错误=错误体['message'] if 错误体 is not None and 'message' in 错误体 else None#文案
            except Exception as 错误:#传输失败；RPC 异常契约未定
                凭证错误=错误文案(错误)#文案
        if 世代!=自身.世代:#过期
            return#丢弃
        def 写就绪(态):#就绪快照
            """补进凭证。"""
            态['status']='ready'#就绪
            态['error']=None#清错误
            态['credentialError']=凭证错误#补全文案
            态['writable']=可写#可写
            补全=[]#行
            for 行 in 行表:#每行
                新=dict(行)#拷贝
                引用=行['apiKeyEnv']#引用
                if 引用 is not None and 引用 in 凭证图:#有凭证
                    新['credential']=凭证图[引用]#补上
                补全.append(新)#记入
            态['rows']=补全#行
            态['namespaces']=命名空间图#命名空间
        自身.存储.update(写就绪)#写入

def 提供方可用(行):#一行当前能否承接模型请求
    """未激活不可用；无凭证引用则走自有路径。"""
    条目=行['entry'] if 'entry' in 行 and 行['entry'] is not None else {}#条目
    if 'active' not in 条目 or 条目['active'] is not True:#未激活
        return False#不可用
    if 'apiKeyEnv' not in 行 or 行['apiKeyEnv'] is None:#无引用
        return True#自有路径
    凭证=行['credential'] if 'credential' in 行 else None#凭证
    return 凭证 is not None and 'configured' in 凭证 and 凭证['configured'] is True#须已存凭证

def 引导就绪度(状态):#从模型拼合投影首次引导就绪度
    """任一可用提供方即结束；否则看官方 DeepSeek 路由。"""
    行表=状态['rows'] if 'rows' in 状态 and 状态['rows'] is not None else []#行
    状态名=状态['status'] if 'status' in 状态 else None#状态
    if (状态名=='idle' or 状态名=='loading') and len(行表)==0:#尚未拉到
        return {'kind':'loading'}#加载中
    if 状态名=='error':#整页失败
        return {'kind':'unavailable','reason':'load-failed'}#加载失败
    if any(提供方可用(行) for 行 in 行表):#任一可用
        return {'kind':'provider-ready'}#就绪
    官方=None#官方行
    for 候选 in 行表:#找官方
        条目=候选['entry'] if 'entry' in 候选 and 候选['entry'] is not None else {}#条目
        路径=条目['settingsPath'] if 'settingsPath' in 条目 and 条目['settingsPath'] is not None else []#路径
        if ('provider' in 条目 and 条目['provider']=='deepseek-official'
            and 'settingsNs' in 条目 and 条目['settingsNs']=='llm-deepseek'
            and len(路径)==0):#官方
            官方=候选#记下
            break#找到
    if 官方 is None:#无官方声明
        return {'kind':'adapter-absent'}#适配器缺失
    官方条目=官方['entry'] if 'entry' in 官方 and 官方['entry'] is not None else {}#条目
    if 'active' not in 官方条目 or 官方条目['active'] is not True:#未激活
        return {'kind':'unavailable','reason':'provider-inactive'}#未激活
    凭证错误=状态['credentialError'] if 'credentialError' in 状态 else None#凭证错误
    官方凭证=官方['credential'] if 'credential' in 官方 else None#官方凭证
    if 凭证错误 is not None or 官方凭证 is None:#凭证未补全
        return {'kind':'unavailable','reason':'credentials-unavailable'}#凭证不可用
    可写=状态['writable'] if 'writable' in 状态 else None#可写
    if 可写 is not True:#设置只读
        return {'kind':'unavailable','reason':'settings-read-only'}#只读
    if 'writable' not in 官方凭证 or 官方凭证['writable'] is not True:#凭证只读
        return {'kind':'unavailable','reason':'credential-read-only'}#凭证只读
    return {'kind':'credential-missing'}#缺密钥

def 已加载则刷新(控制器):#已打开过才重拉
    """idle 则跳过。"""
    if 控制器.存储.getSnapshot()['status']=='idle':#尚未打开
        return#跳过
    控制器.load()#刷新
