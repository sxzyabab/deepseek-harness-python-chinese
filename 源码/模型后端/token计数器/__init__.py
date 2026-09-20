"""按会话回放计量 token，供请求预算与表面压力使用。"""
from weakref import WeakKeyDictionary as 弱键字典#会话到回放状态
from ...依赖 import cordis#外部依赖胶水
服务=cordis.服务#服务基类
from ..llm.助手流 import 组装助手流#嵌入流重组
from ..llm.调用配置 import 深冻结,结构化克隆#深冻结与拆离克隆
from ...内核.会话 import 归一请求头,请求头是否相等,是否表面事件#规范头、头相等与表面判定
from .类型 import 计量错误#计量异常
from .分解投影 import 分解投影定义#分解投影
from .用量投影 import 用量投影定义,压力投影定义#压力与用量投影
from .计价 import 计价内容,计价工具令牌,计价消息 as 纯计价消息,角色开销#计价与角色开销
from .表面折叠 import 折叠表面令牌#按节点表面折叠
from .路由计价 import 计价表面#路由计价

__all__=['计量错误','用量令牌','可选头相等','校验配置键','令牌计量','默认']#仅中文公开名（Cordis 槽另挂）

def 用量令牌(用量):#合计提供方用量桶
    """合计互不相交的提供方用量桶，不把推理输出再计一次。"""
    缓存读=用量['cacheReadTokens'] if 'cacheReadTokens' in 用量 else None#缓存读
    缓存写=用量['cacheWriteTokens'] if 'cacheWriteTokens' in 用量 else None#缓存写
    return 用量['inputTokens']+(0 if 缓存读 is None else 缓存读)+(0 if 缓存写 is None else 缓存写)+用量['outputTokens']#未缓存输入加缓存加输出

def 可选头相等(左,右):#比较可选信封
    """比较可选信封，使无头估算也能跟踪后续表面增量。"""
    if 左 is None or 右 is None:#一方缺席
        return 左 is 右#两边都缺才等
    return 请求头是否相等(左,右)#两边都有则逐字段

def 校验配置键(配置):#拒绝未知配置键
    """在默认值能把它们藏起来之前拒绝过时或拼错的键。"""
    for 键 in 配置:#遍历自有键
        raise 计量错误('TokenMeterConfig: unknown key "'+键+'" (no settings are supported)')#不支持任何设置

class 令牌计量(服务):#token 计量服务
    """一份服务级估算器与按会话隔离折叠的回放所有者。"""
    Config={}#空配置模式（Cordis 协议槽；无设置项）

    def __init__(自身,ctx,配置=None):#构造计量服务
        """构造计量服务并以 tokenMeter 名登记。"""
        if 配置 is None:#未传配置
            配置={}#空配置
        super().__init__(ctx,'tokenMeter')#以 tokenMeter 名注册
        校验配置键(配置)#拒绝未知键
        自身.状态表=弱键字典()#会话到回放状态

        def 挂投影(投影上下文,*位置参数):#有投影注册表才挂三个单元
            """有投影注册表才挂三个单元。"""
            表=投影上下文.sessionProjections#投影注册表
            表.register(用量投影定义)#用量投影
            表.register(压力投影定义)#压力投影
            表.register(分解投影定义)#分解投影

        ctx.依赖启动(['sessionProjections'],挂投影)#有投影注册表才挂

        def 追上(会话,*位置参数):#已有折叠才追上
            """已有折叠才追上。"""
            if 会话 in 自身.状态表:#已有折叠
                自身._同步(会话)#追上

        ctx.监听('session/event',追上)#新事件

    def 测量(自身,会话,请求头=None):#测量当前压力与表面
        """经持久尾测量当前请求压力与表面。

        仅当最近一次成功调用的规范请求信封匹配且其合计不低于该次调用的完整启发式锚点时才复用提供方用量；否则对完整信封与表面做启发式重新计价。
        `请求头` 只影响请求压力；表面字段始终描述当前会话表面。每次调用都克隆按位置节点，因此测量是 O(表面)。
        """
        状态=自身._同步(会话)#追上持久尾
        if 请求头 is None:#调用方未给头
            头=状态['header']#用最新已记录头
        else:#调用方给了头
            头=归一请求头(请求头)#规范调用方信封
        定价=自身._路由图像计价(头)#路由图定价（若 llm 已挂）
        文件文本=自身._文件请求文本()#文件投影（若 llm 已挂）
        表面=计价表面(状态['surface'],定价,文件文本)#按路由计价表面
        锚点=状态['anchor']#最新锚点
        if 锚点 is not None and 可选头相等(锚点['header'],头):#信封匹配则可复用锚点
            基线=锚点['baseline']#沿用锚点基线
            表面增量=表面['surfaceTokens']-锚点['surfaceTokens']#表面相对锚点
        elif 头 is None and 表面['surfaceTokens']==0:#无头且空表面
            基线={'kind':'none','tokens':0}#尚无基线
            表面增量=0#无增量
        else:#信封变了或无法复用
            基线={'kind':'estimated','tokens':计价工具令牌(头)+表面['surfaceTokens']}#工具加表面（系统在表面）
            表面增量=0#已含在基线里
        return 深冻结(结构化克隆({
            'logRevision':状态['consumedEvents'],#已消费修订
            'baseline':基线,#基线
            'surfaceDeltaTokens':表面增量,#表面增量
            'totalTokens':max(0,基线['tokens']+表面增量),#非负总压力
            'surfaceTokens':表面['surfaceTokens'],#表面合计
            'nodes':表面['nodes'],#表面节点
        }))#拆离并冻结

    def _路由图像计价(自身,头):#路由图定价
        """解析路由模型的图片定价；llm 服务与路由声明时才有。"""
        if 头 is None or 'config' not in 头:#无头
            return None#无
        配置=头['config']#调用配置
        llm=自身.ctx.获取服务('llm')#可选 llm
        if llm is None or not hasattr(llm,'imageRequestPricing'):#未挂或无方法
            return None#无
        return llm.imageRequestPricing(配置.get('provider'),配置.get('model'))#问 llm

    def _文件请求文本(自身):#文件请求文本解析器
        """已挂载 LLM 服务时解析请求时文件投影。"""
        llm=自身.ctx.获取服务('llm')#可选 llm
        if llm is None or not hasattr(llm,'fileRequestText'):#未挂
            return None#无
        return llm.fileRequestText#绑定

    def 计价消息(自身,消息):#实例面计价消息
        """启发式计价一条模型可见消息（计价模块纯函数的实例面）。"""
        return 纯计价消息(消息)#交给纯函数

    def _同步(自身,会话):#追上回放
        """把一份会话的折叠追上当前持久尾。"""
        状态=自身.状态表.get(会话)#已有状态
        if 状态 is None:#第一次读
            状态={
                'consumedEvents':0,#尚未消费
                'header':None,#尚无头
                'surface':[],#空表面
                'surfaceTokens':0,#合计0
                'stepStart':None,#无打开步
                'anchor':None,#无锚点
            }#初始状态
            自身.状态表[会话]=状态#记下
        日志=会话.events#只追加日志
        while 状态['consumedEvents']<len(日志):#还有未读事件
            事件=日志[状态['consumedEvents']]#按下标取下一条
            自身._折事件(会话,状态,事件)#折进状态
            状态['consumedEvents']+=1#前进一步
        return 状态#当前折叠

    def _折事件(自身,会话,状态,事件):#折一条事件
        """在改写回放状态之前校验并准备每一段会失败的部分。

        畸形事件在每次重试时都保持未读，而不是把同一变更部分应用超过一次。
        """
        下一头=状态['header']#候选头
        下一步起点=状态['stepStart']#候选打开步
        下一锚点=状态['anchor']#候选锚点
        种类=事件['type']#事件类型
        数据=事件['data']#载荷
        if 种类=='request/header':#请求头
            下一头=归一请求头(数据['header'])#更新规范头
        elif 种类=='step/start':#步开始
            if 状态['stepStart'] is not None:#已有打开步
                打开=状态['stepStart']#打开步
                raise 计量错误(
                    'token meter: step/start at seq '+str(事件['seq'])+' arrived before turn '+str(打开['turn'])+'/step '+str(打开['step'])+' ended'
                )#步未闭合
            下一步起点={'turn':数据['turn'],'step':数据['step']}#记下打开步
        elif 种类=='step/end':#步结束
            打开=状态['stepStart']#打开步
            if 打开 is None or 打开['turn']!=数据['turn'] or 打开['step']!=数据['step']:#不成对
                raise 计量错误('token meter: step/end at seq '+str(事件['seq'])+' has no matching step/start event')#不成对
            下一步起点=None#关闭步
        表面=折叠表面令牌(状态['surface'],事件) if 是否表面事件(事件) else None#按节点折叠
        if 种类=='assistant/message':#助手定稿
            打开=状态['stepStart']#打开步
            if 打开 is None or 打开['turn']!=数据['turn'] or 打开['step']!=数据['step']:#不成对
                raise 计量错误('token meter: assistant/message at seq '+str(事件['seq'])+' has no matching step/start event')#不成对
            事件令牌=表面['tokens']#本事件表面价格
            用量=数据['usage'] if 'usage' in 数据 else None#提供方用量
            #循环在step/start之后准入提示词与用户消息；本调用只计价助手前表面
            助手前表面=状态['surfaceTokens']#提交前当前表面合计
            if 用量 is not None and 下一头 is not None:#有用量且有头
                提供方助手=自身._估算提供方助手(事件)#提供方输出计价
                锚点表面=助手前表面+提供方助手#助手前表面加提供方输出
                提供方合计=用量令牌(用量)#提供方合计
                估算锚点=计价工具令牌(下一头)+锚点表面#完整启发式锚点（系统在表面）
                if 提供方合计>=估算锚点:#提供方不低于启发式
                    基线={'kind':'usage','tokens':提供方合计,'usage':用量}#用提供方
                else:#否则启发式
                    基线={'kind':'estimated','tokens':估算锚点}#启发式
                下一锚点={'header':下一头,'surfaceTokens':锚点表面,'baseline':基线}#新锚点
            else:#没有用量或没有头
                锚点表面=助手前表面+事件令牌#助手前表面加持久输出
                下一锚点={
                    'header':下一头,#当时信封
                    'surfaceTokens':锚点表面,#当时表面
                    'baseline':{'kind':'estimated','tokens':计价工具令牌(下一头)+锚点表面},#估算
                }#启发式锚点
        状态['header']=下一头#提交头
        状态['stepStart']=下一步起点#提交打开步
        if 表面 is not None:#有表面折叠
            状态['surface']=表面['nodes']#下一表面
            状态['surfaceTokens']+=表面['deltaTokens']#更新合计
        状态['anchor']=下一锚点#提交锚点

    def _估算提供方助手(自身,事件):#按嵌入流估算提供方助手输出
        """从消息嵌入流重组提供方输出。"""
        提供方内容=组装助手流(事件['data']['stream'] if 'stream' in 事件['data'] else []).块列表()#从嵌入流重组
        if len(提供方内容)==0:#空流
            return 0#已知空流
        return 计价内容(提供方内容)+角色开销#计价

默认=令牌计量
default=令牌计量#框架槽
