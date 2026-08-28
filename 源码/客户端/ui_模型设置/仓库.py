"""模型设置页仓库与首次引导就绪度投影。

对齐上游 `ui-settings-models/src/client/store.ts`。公开面仅中文名。
"""
from ...依赖 import cordis#外部依赖胶水
是否thenable=cordis.工具.是否thenable#可等待判定
from ..schema_form import 再水合模式,路径上节点,取路径,有路径#schema 路径

__all__=[#仅中文公开名
    '快照仓库','错误文案','推导密钥引用','协议选项','提供方可用','引导就绪度','模型设置仓库','已加载则刷新',
]#公开面结束

探测路由='\u0000probe'#探测用路由键

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待
    return 值#同步

def 错误文案(错误):#拒绝值收成可展示文案
    """Error 取其 message。"""
    return str(错误) if isinstance(错误,Exception) else str(错误)#文案

def 推导密钥引用(提供方):#由提供方路由推导凭证引用名
    """大写后非常量字符换成 _，再加 _API_KEY。"""
    import re#正则
    return re.sub(r'[^A-Z0-9]+','_',提供方.upper())+'_API_KEY'#推导

def 协议选项(命名空间):#从所属命名空间 schema 读出协议选项
    """schema 没有则空列表。"""
    if 命名空间 is None:#无
        return []#空
    节点=路径上节点(再水合模式(取字段(命名空间,'schema')),['providers',探测路由,'api'])#api 节点
    支=取字段(节点,'anyOf') or 取字段(节点,'oneOf') or []#联合成员
    if not 支:#非 union
        return []#空
    结果=[]#协议标识
    for 项 in 支:#成员
        值=取字段(项,'const')#常量
        if isinstance(值,str):#字符串
            结果.append(值)#记入
    return 结果#选项

def 密钥引用于(命名空间,路径):#从已解析 profile 取出 apiKeyEnv
    """非空字符串才算引用。"""
    if 命名空间 is None:#无
        return None#无
    档=取路径(取字段(命名空间,'value'),路径)#profile
    if not isinstance(档,dict):#非对象
        return None#无
    引用=取字段(档,'apiKeyEnv')#字段
    return 引用 if isinstance(引用,str) and len(引用)>0 else None#引用

class 快照仓库:#简易快照仓库
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

class 模型设置仓库:#模型设置页控制器
    """拼合提供方目录、设置命名空间与所引用凭证。"""
    def __init__(自身,接口):#注入 API
        """空闲快照。"""
        自身.接口=接口#settings/credentials/llm
        自身.store=快照仓库({#页面快照
            'status':'idle','error':None,'credentialError':None,'writable':False,'rows':[],'namespaces':{},
        })#仓库结束
        自身.世代=0#在飞请求世代

    def load(自身):#刷新整页快照
        """目录与命名空间并行拉取，再批量凭证 describe。"""
        自身.世代+=1#抬世代
        世代=自身.世代#本请求
        def 标加载(态):#loading
            """标 loading。"""
            态['status']='loading'#加载中
            态['error']=None#清错误
        自身.store.update(标加载)#写入
        try:#并行拉
            目录应答=解开(自身.接口.llm.providers({}))#提供方目录
            设置应答=解开(自身.接口.settings.describe({}))#设置描述
            if not 取字段(取字段(目录应答,'result'),'ok'):#目录失败
                raise Exception(取字段(取字段(取字段(目录应答,'result'),'error'),'message'))#抛
            if not 取字段(取字段(设置应答,'result'),'ok'):#设置失败
                raise Exception(取字段(取字段(取字段(设置应答,'result'),'error'),'message'))#抛
            提供方表=取字段(取字段(取字段(目录应答,'result'),'value'),'providers') or []#目录
            可写=bool(取字段(取字段(取字段(设置应答,'result'),'value'),'writable'))#可写
            视图表=取字段(取字段(取字段(设置应答,'result'),'value'),'namespaces') or []#命名空间
        except Exception as 错误:#整页失败
            if 世代!=自身.世代:#过期
                return#丢弃
            def 写错误(态):#整页错误
                """保留上次好行。"""
                态['status']='error'#错误
                态['error']=错误文案(错误)#文案
            自身.store.update(写错误)#写入
            return#结束
        命名空间图={取字段(视,'ns'):视 for 视 in 视图表}#按 ns
        行表=[]#提供方行
        for 条目 in 提供方表:#每条目录
            命名空间=命名空间图.get(取字段(条目,'settingsNs'))#所属 ns
            路径=取字段(条目,'settingsPath') or []#设置路径
            已配置=命名空间 is not None and (len(路径)==0 or 取路径(取字段(命名空间,'value'),路径) is not None)#已配置
            可删=命名空间 is not None and len(路径)>0 and 有路径(取字段(命名空间,'user'),路径) and not 有路径(取字段(命名空间,'base'),路径)#可删回 base
            行表.append({#一行
                'entry':条目,#目录条目
                'configured':已配置,#已配置
                'removable':可删,#可删
                'apiKeyEnv':密钥引用于(命名空间,路径),#凭证引用
                'credential':None,#稍后补全
            })#行结束
        引用表=list({行['apiKeyEnv'] for 行 in 行表 if 行['apiKeyEnv']})#去重引用
        凭证图={}#引用→凭证
        凭证错误=None#补全文案
        if len(引用表)>0:#有引用
            try:#描述凭证
                应答=解开(自身.接口.credentials.describe({'refs':引用表}))#批量
                if 取字段(取字段(应答,'result'),'ok'):#成功
                    凭证图=取字段(取字段(取字段(应答,'result'),'value'),'credentials') or {}#图
                else:#业务拒绝
                    凭证错误=取字段(取字段(取字段(应答,'result'),'error'),'message')#文案
            except Exception as 错误:#传输失败
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
                if 引用 is not None and isinstance(凭证图,dict) and 引用 in 凭证图:#有凭证
                    新['credential']=凭证图[引用]#补上
                补全.append(新)#记入
            态['rows']=补全#行
            态['namespaces']=命名空间图#命名空间
        自身.store.update(写就绪)#写入

def 提供方可用(行):#一行当前能否承接模型请求
    """未激活不可用；无凭证引用则走自有路径。"""
    条目=取字段(行,'entry') or {}#条目
    if not 取字段(条目,'active'):#未激活
        return False#不可用
    if 取字段(行,'apiKeyEnv') is None:#无引用
        return True#自有路径
    return 取字段(取字段(行,'credential'),'configured') is True#须已存凭证

def 引导就绪度(状态):#从模型拼合投影首次引导就绪度
    """任一可用提供方即结束；否则看官方 DeepSeek 路由。"""
    行表=取字段(状态,'rows') or []#行
    状态名=取字段(状态,'status')#状态
    if (状态名=='idle' or 状态名=='loading') and len(行表)==0:#尚未拉到
        return {'kind':'loading'}#加载中
    if 状态名=='error':#整页失败
        return {'kind':'unavailable','reason':'load-failed'}#加载失败
    if any(提供方可用(行) for 行 in 行表):#任一可用
        return {'kind':'provider-ready'}#就绪
    官方=None#官方行
    for 候选 in 行表:#找官方
        条目=取字段(候选,'entry') or {}#条目
        if 取字段(条目,'provider')=='deepseek-official' and 取字段(条目,'settingsNs')=='llm-deepseek' and len(取字段(条目,'settingsPath') or [])==0:#官方
            官方=候选#记下
            break#找到
    if 官方 is None:#无官方声明
        return {'kind':'adapter-absent'}#适配器缺失
    if not 取字段(取字段(官方,'entry'),'active'):#未激活
        return {'kind':'unavailable','reason':'provider-inactive'}#未激活
    if 取字段(状态,'credentialError') is not None or 取字段(官方,'credential') is None:#凭证未补全
        return {'kind':'unavailable','reason':'credentials-unavailable'}#凭证不可用
    if not 取字段(状态,'writable'):#设置只读
        return {'kind':'unavailable','reason':'settings-read-only'}#只读
    if not 取字段(取字段(官方,'credential'),'writable'):#凭证只读
        return {'kind':'unavailable','reason':'credential-read-only'}#凭证只读
    return {'kind':'credential-missing'}#缺密钥

def 已加载则刷新(控制器):#已打开过才重拉
    """idle 则跳过。"""
    if 取字段(控制器.store.getSnapshot(),'status')=='idle':#尚未打开
        return#跳过
    控制器.load()#刷新
