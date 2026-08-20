"""一条提供方路由的模型目录物化。

对齐上游 `llm-pi-ai/src/catalog.ts`。公开面仅中文名；无英文别名。
"""
import pi_ai#pi-ai SDK

__all__=(#仅中文公开名
    '无费用','模态列表','思考档位列表','受支持思考格式',
    '目录提供方们','目录提供方','目录提供方标识列表','目录提供方接受密钥',
    '目录模型','解析路由模型',
)#公开面结束

无费用={'input':0,'output':0,'cacheRead':0,'cacheWrite':0}#零费用占位

模态门={
    'text':True,#文本
    'image':True,#图片
}#模态漂移门
模态列表=tuple(模态门.keys())#可声明模态

思考档位门={
    'off':True,#关闭
    'minimal':True,#最小
    'low':True,#低
    'medium':True,#中
    'high':True,#高
    'xhigh':True,#更高
    'max':True,#最大
}#档位漂移门
思考档位列表=tuple(思考档位门.keys())#可声明档位

思考格式门={
    'openai':True,#OpenAI
    'deepseek':True,#DeepSeek
    'openrouter':True,#OpenRouter
    'together':True,#Together
    'zai':True,#Z.ai
    'qwen':True,#Qwen
    'string-thinking':True,#字符串思考
    'ant-ling':True,#Ant Ling
}#格式漂移门
受支持思考格式=tuple(思考格式门.keys())#可点名格式列表

提供方索引=None#惰性目录提供方索引

def 已声明输入(已配置):
    """条目声明的模态，空或缺席则无答案。"""
    if 已配置 is None or len(已配置)==0:#空列表与缺席都表示没有声明，交给后续回落到目录或路由默认
        return None#无答案，调用方继续往目录/路由找
    return list(已配置)#已声明模态，拷一份避免改到配置原件

def 目录提供方们():
    """已安装目录提供方按 id，构造一次。"""
    global 提供方索引#惰性索引
    if 提供方索引 is None:#第一次调用才向 pi-ai 要内置提供方，之后复用同一份字典
        提供方索引={}#首次构造
        for 提供方 in pi_ai.builtinProviders():#按 id 建索引，后续查找走字典而不是再扫列表
            提供方索引[提供方.id]=提供方#按id索引；后出现的同 id 会覆盖先出现的
    return 提供方索引#已构造索引

def 目录提供方(提供方):
    """按路由取目录提供方，未运来则为 None。"""
    return 目录提供方们().get(提供方)#查找；未运来返回 None，不抛

def 目录提供方标识列表():
    """已安装 pi-ai 目录运来的每条提供方路由。"""
    return pi_ai.getBuiltinProviders()#内置id列表

def 目录提供方接受密钥(提供方):
    """目录提供方是否声明 api-key 方法。"""
    条目=目录提供方(提供方)#目录提供方
    if 条目 is None:#未运来的路由没有密钥方法可广告
        return False#未运来则不能声称接受密钥
    认证=getattr(条目,'auth',None)#认证块；对象用属性，缺席当无认证
    if 认证 is None:#有提供方但没有认证块，同样不能用密钥
        return False#无认证则配置面不得要求填密钥
    密钥方法=认证.get('apiKey') if isinstance(认证,dict) else getattr(认证,'apiKey',None)#密钥方法；映射与对象都认
    return 密钥方法 is not None#有密钥方法才广告；仅 OAuth 的目录到这里为假

def 模型作字典(模型):
    """把目录模型收成字典以便展开覆盖。"""
    if 模型 is None:#没有目录基则从空字典开始叠，手声明模型走这条
        return {}#空
    if isinstance(模型,dict):#已经是字典则拷一份，避免改到目录原件
        return dict(模型)#已是字典
    return dict(vars(模型))#对象字段收成字典后再叠覆盖

def 目录模型(提供方):
    """一条路由的已安装目录模型，按模型 id 索引。"""
    if 提供方 not in 目录提供方们():#未运来的路由没有内置模型
        return {}#未运来则空，解析路由时必须手写 models 列表
    表={}#按id索引
    for 模型 in pi_ai.getBuiltinModels(提供方):#把内置模型收成按 id 索引的字典
        字典=模型作字典(模型)#收成字典，后续物化从这份拷
        表[字典['id']]=字典#按id写入；同 id 后出现的覆盖先出现的
    return 表#目录模型表

def 非法(提供方,细节):
    """带路由诊断抛出。"""
    raise Exception(f'llm-pi-ai: provider "{提供方}" {细节}')#点名路由

def 共用目录协议(默认表):
    """一条目录路由已运来模型所同意的那一条线路协议。"""
    协议集合=set()#见到的协议
    for 模型 in 默认表.values():#收集这条路由上所有已运来模型的协议
        协议集合.add(模型['api'])#记下；多协议时下面无法给出路由默认
    if len(协议集合)==1:#恰好一条才能当路由默认协议，条目没写 api 时用它
        return next(iter(协议集合))#恰好一条
    return None#空目录或多种协议都没有共用答案，条目必须自己点名 api

def 是否正整数(值):
    """判定是否为正整数，含整值浮点。"""
    if isinstance(值,bool):#布尔是 int 子类，不能当容量
        return False#布尔不算，True 不得当成 1
    if isinstance(值,int):#整数看正负
        return 值>0#正整数才通过；零与负数拒绝
    if isinstance(值,float):#浮点必须是整值且为正，JSON 数字可能走这条
        return 值>0 and 值.is_integer()#整值浮点才通过，1.5 拒绝
    return False#其它类型一律拒绝，字符串数字也不收

def 解析模型推理(提供方,条目,基):
    """从已声明力度解析一个模型的推理能力。"""
    if 'reasoningEfforts' not in 条目:#没声明力度则继承目录推理能力，与显式 false 不同
        基推理=False if 基 is None else 基.get('reasoning',False)#无目录基则非推理；有基则抄其 reasoning
        return {'reasoning':基推理}#继承或非推理，不产出 thinkingLevelMap
    力度=条目['reasoningEfforts']#已声明力度，下面按 false / 空 / 档位表分流
    if 力度 is False:#显式 False 关掉推理，与省略字段不同
        return {'reasoning':False}#显式关掉，不继承目录思考档位
    if 力度 is None or (isinstance(力度,dict) and len(力度)==0):#空映射不是合法声明，必须点名档位或写成 false
        非法(提供方,'model "'+条目['id']+'" has an empty reasoningEfforts; declare the offered levels, set'
            +' false for a non-reasoning model, or omit the field to keep the installed catalog\'s capability')#必须声明或省略
    已声明=[]#已声明档位
    for 档位 in 思考档位列表:#只认已知档位键，未知键忽略，避免把拼写错误当新档位
        if 档位 not in 力度:#这条配置没点这个档位
            continue#没点这个档位则不进分派表，稍后会钉成不支持
        已声明.append((档位,力度[档位]))#有则带上，线路拼写留到下一轮校验
    for 档位,线路 in 已声明:#已声明档位必须给出线路拼写，off 可以空
        if 线路 is None:#None 表示不发线路值
            if 档位!='off':#只有 off 允许不发线路值，其它档位必须有对端认得的拼写
                非法(提供方,'model "'+条目['id']+'" reasoningEfforts.'+档位+' needs the wire value dispatch'
                    +' should send; only "off" may leave it empty')#必须给线路值
        elif len(线路)==0:#空串不是合法线路拼写，与 None 不同，None 只给 off
            非法(提供方,'model "'+条目['id']+'" reasoningEfforts.'+档位+' must not be an empty string')#不得空串
    仅关闭=True#是否只有off；有思考档位才会翻成假
    for 档位,线路 in 已声明:#必须有一个思考档位，否则应写成 false
        if 档位!='off':#见到非 off 则这是推理模型
            仅关闭=False#有思考档位
            break#已判定，不必扫完
    if 仅关闭:#只给 off 等于没有思考档位，配置不合法
        非法(提供方,'model "'+条目['id']+'" reasoningEfforts offers no level beyond "off"; declare a thinking'
            +' level, or set reasoningEfforts to false for a non-reasoning model')#必须有思考档位或关掉
    映射={}#分派映射
    for 档位 in 思考档位列表:#每个已知档位都要钉成支持或不支持
        if 档位 not in 力度:#没点名则钉成不支持，避免继承目录残留
            映射[档位]=None#钉成不支持，调用方不得再从目录基抄这个档位
        elif 力度[档位] is not None:#有拼写才写入分派表；off 的 None 表示不发线路值
            映射[档位]=力度[档位]#写入拼写
    return {'reasoning':True,'thinkingLevelMap':映射}#推理模型

def 解析模型兼容(提供方,条目,路由,基,协议):
    """从配置的推理开关解析一个模型的 compat 块。"""
    条目兼容=条目.get('compat') or {}#模型开关；缺席当空映射，后面用 in 判断是否真写了键
    路由兼容=路由 or {}#路由开关；None 当空映射
    思考格式=条目兼容.get('thinkingFormat')#模型格式；None 表示模型没写
    if 思考格式 is None:#模型没写则回落路由级格式
        思考格式=路由兼容.get('thinkingFormat')#路由格式；仍可能是 None
    支持力度=条目兼容.get('supportsReasoningEffort')#模型力度开关
    if 支持力度 is None:#模型没写则回落路由级力度开关
        支持力度=路由兼容.get('supportsReasoningEffort')#路由力度开关；仍可能是 None
    if 思考格式 is None and 支持力度 is None:#两条开关都没有则不产出 compat，避免空对象覆盖目录
        return {}#没有任何开关
    if 协议!='openai-completions':#这两条开关只存在于 Completions，其它协议不得带着模型级开关
        模型开了格式=条目.get('compat') is not None and 'thinkingFormat' in (条目.get('compat') or {})#模型自己写了格式，不是路由回落
        模型开了力度=条目.get('compat') is not None and 'supportsReasoningEffort' in (条目.get('compat') or {})#模型自己写了力度开关
        if 模型开了格式 or 模型开了力度:#模型自己写了开关却不是 Completions，配置错误
            非法(提供方,'model "'+条目['id']+'" sets compat reasoning switches, but its api is "'+协议+'";'
                +' thinkingFormat and supportsReasoningEffort exist only on openai-completions')#只存在于Completions
        return {}#仅路由级开关碰上非 Completions 则跳过，不把路由开关抄到这条模型
    可继承=None#可继承的compat
    if 基 is not None and 基.get('api')==协议:#目录基同协议才继承其 compat，跨协议继承会把 Completions 开关接到别的线路
        可继承=基.get('compat')#目录compat；可能仍是 None
    兼容={}#合并compat
    if 可继承 is not None:#先铺目录基，再覆盖配置开关
        兼容.update(可继承 if isinstance(可继承,dict) else dict(vars(可继承)))#目录基；对象收成字典再叠
    if 思考格式 is not None:#配置的格式覆盖目录，None 表示没写不是删掉目录值
        兼容['thinkingFormat']=思考格式#覆盖格式
    if 支持力度 is not None:#配置的力度开关覆盖目录
        兼容['supportsReasoningEffort']=支持力度#覆盖力度开关
    return {'compat':兼容}#compat块

def 解析路由模型(请求):
    """在已配置条目下合并已安装目录默认，物化一条路由的目录。"""
    提供方=请求['provider']#路由键
    默认表=目录模型(提供方)#已安装目录
    目录方=目录提供方(提供方)#目录提供方
    提供方基址=None if 目录方 is None else getattr(目录方,'baseUrl',None)#目录端点
    已配置=请求.get('models') or []#已配置列表；缺席当空，后面用长度判断是否整份替换
    覆盖=请求.get('modelOverrides') or {}#按id覆盖；与 models 列表互斥
    for 标识,一条 in 覆盖.items():#覆盖表按模型 id 校验，不能和 models 列表并用
        if len(标识)==0:#覆盖键就是模型 id，空键无法寻址
            非法(提供方,'has a modelOverrides entry with an empty model id')#id不得空
        if len(默认表)==0:#没有已安装目录就不能用覆盖，必须手写 models 列表
            非法(提供方,'sets modelOverrides for "'+标识+'", but the installed catalog does not describe this route;'
                +' a declared route spells every model out in its models list')#手声明必须用models列表
        if len(已配置)>0:#写了 models 列表就等于替换整份目录，覆盖应写在条目上
            非法(提供方,'sets modelOverrides for "'+标识+'" beside a models list; models already replaces the served'
                +' catalog, so declare the fields on its entries')#应写在条目上
        if 标识 not in 默认表:#覆盖只能点目录里已有的模型，未知 id 不是新增
            非法(提供方,'modelOverrides names "'+标识+'", which the installed catalog does not describe')#未知模型
        if 'id' in 一条:#id 是字典键，条目里再写 id 会冲突
            非法(提供方,'modelOverrides entry "'+标识+'" sets "id", which is the dict key')#id是键
    if len(已配置)>0:#配置给了 models 列表则整份替换目录，不再从默认表生成条目
        条目们=list(已配置)#用列表
    else:#没有列表则用目录条目叠覆盖
        条目们=[]#目录加覆盖
        for 模型 in 默认表.values():#每个目录模型先抄 id 再叠覆盖字段
            一条={'id':模型['id']}#目录id，覆盖不得改这个键
            一条.update(覆盖.get(模型['id']) or {})#叠覆盖；没点这个 id 则 {} 不改字段
            条目们.append(一条)#写入
    if len(条目们)==0:#最终一条模型都没有，手声明路由必须列出 models
        非法(提供方,'resolves no models; the installed catalog does not describe this route, so its models'
            +' must be listed in configuration')#必须列出
    路由协议=共用目录协议(默认表)#目录共用协议；多种协议时为 None，条目必须自己点名
    路由兼容=请求.get('compat') or {}#路由兼容
    路由开了兼容=('thinkingFormat' in 路由兼容) or ('supportsReasoningEffort' in 路由兼容)#路由设了开关；用来在收尾检查有没有 Completions 模型
    已见=set()#已见id
    配置上限={}#显式按次上限；只有条目自己写了 maxTokens 才进这张表
    模型们=[]#物化模型
    for 条目 in 条目们:#逐条物化：协议、端点、窗口、上限、名字、模态都按配置→目录→路由默认回落
        if len(条目['id'])==0:#模型 id 不得空
            非法(提供方,'has a model with an empty id')#id不得空
        if 条目['id'] in 已见:#同一路由不能列两次同一 id
            非法(提供方,'lists model "'+条目['id']+'" more than once')#id重复
        已见.add(条目['id'])#记下已见，后面再遇到就报重复
        基=默认表.get(条目['id'])#目录条目；手声明未知 id 为 None，后面字段必须自己给
        协议=请求.get('api')#路由协议；写了则整条路由同一协议
        if 协议 is None and 基 is not None:#路由没写协议则用目录条目协议
            协议=基.get('api')#条目协议
        if 协议 is None:#条目也没有则用整条路由的共用协议
            协议=路由协议#共用协议；目录多种协议时仍是 None
        if 协议 is None:#三处都没有则无法知道线路，必须点名
            非法(提供方,'model "'+条目['id']+'" needs an api; the installed catalog does not describe it, so set the'
                +" route's api to the wire protocol its endpoint speaks")#必须点名协议
        基址=请求.get('baseURL')#路由端点
        if 基址 is None and 基 is not None:#路由没写端点则用目录条目端点
            基址=基.get('baseUrl')#条目端点
        if 基址 is None:#条目也没有则用提供方目录端点
            基址=提供方基址#提供方端点
        if 基址 is None:#三处都没有则无法发请求
            非法(提供方,'model "'+条目['id']+'" needs a baseURL; the installed catalog does not describe this route')#必须点名端点
        窗口=条目.get('contextWindow')#条目窗口
        if 窗口 is None and 基 is not None:#条目没写窗口则用目录窗口
            窗口=基.get('contextWindow')#目录窗口
        if 窗口 is None:#目录也没有则用路由默认窗口
            窗口=请求['defaultContextWindow']#路由默认；调用方保证键在
        if not 是否正整数(窗口):#窗口必须是正整数，含整值浮点
            非法(提供方,'model "'+条目['id']+'" contextWindow must be a positive integer')#窗口非法
        上限=条目.get('maxTokens')#条目上限
        if 上限 is None and 基 is not None:#条目没写上限则用目录上限
            上限=基.get('maxTokens')#目录上限
        if 上限 is None:#目录也没有则用路由默认上限
            上限=请求['defaultMaxTokens']#路由默认
        if not 是否正整数(上限):#上限必须是正整数
            非法(提供方,'model "'+条目['id']+'" maxTokens must be a positive integer')#上限非法
        if 条目.get('maxTokens') is not None:#只有配置显式写了上限才记入按次上限表，目录继承的不进
            配置上限[条目['id']]=条目['maxTokens']#记下显式上限
        物化=模型作字典(基)#目录基；无基则空字典，下面逐字段钉
        物化['id']=条目['id']#模型id
        名称=条目.get('name')#条目名
        if 名称 is None and 基 is not None:#条目没写名则用目录名
            名称=基.get('name')#目录名
        if 名称 is None:#目录也没有则展示名落到 id
            名称=条目['id']#落到id，配置面至少有可显示字符串
        物化['name']=名称#展示名
        物化['api']=协议#协议
        物化['provider']=提供方#路由键
        物化['baseUrl']=基址#端点
        输入=已声明输入(条目.get('input'))#条目模态；空列表当没声明
        if 输入 is None and 基 is not None:#条目没声明模态则用目录模态
            输入=基.get('input')#目录模态
        if 输入 is None:#目录也没有则用路由默认模态
            输入=list(请求['defaultInput'])#路由默认，拷一份避免共享列表
        物化['input']=输入#模态
        费用=None if 基 is None else 基.get('cost')#目录费用；手声明无基则下面用零占位
        物化['cost']=无费用 if 费用 is None else 费用#费用或零占位，不把 None 写进模型
        物化['contextWindow']=窗口#窗口
        物化['maxTokens']=上限#能力上限
        物化.update(解析模型推理(提供方,条目,基))#推理字段
        物化.update(解析模型兼容(提供方,条目,请求.get('compat'),基,协议))#兼容块
        模型们.append(物化)#写入
    有补全=False#是否有Completions模型；路由级思考开关必须落在 Completions 上
    for 模型 in 模型们:#扫物化结果，看这条路由有没有 Completions 模型
        if 模型['api']=='openai-completions':#见到 Completions 则路由级思考开关才有落点
            有补全=True#已有 Completions，不必再扫
            break#已判定
    if 路由开了兼容 and not 有补全:#路由设了开关却没有Completions模型
        非法(提供方,'sets compat reasoning switches, but no model on the route speaks openai-completions;'
            +' thinkingFormat and supportsReasoningEffort exist only on that protocol')#只存在于该协议
    return {'models':模型们,'configuredMaxTokens':配置上限}#物化目录
