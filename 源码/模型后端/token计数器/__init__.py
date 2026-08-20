"""单一、感知回放的 token 计量服务，用于请求与表面压力。对齐上游 `token-meter/src/index.ts`。公开面仅中文名。

Cordis 槽 `Config` / `default` 可保留。配置键与诊断英文字面量保持上游。
"""
from weakref import WeakKeyDictionary as 弱键字典#会话到回放状态
from cordis import 服务#服务基类
from schemastery import 模式#配置校验
from llm.组装器 import 块组装器#块组装器
from llm.调用配置 import 深冻结,结构化克隆#深冻结与拆离克隆
from session import 归一请求头,请求头是否相等,是否表面事件#规范头、头相等与表面判定
from .类型 import 取,试取#读取字段
from .分解投影 import 分解投影定义#分解投影
from .用量投影 import 用量投影定义,压力投影定义#压力与用量投影
from .计价 import 计价内容,计价请求头,计价消息 as 纯计价消息,角色开销#计价与角色开销
from .表面折叠 import 折叠表面令牌#按节点表面折叠

__all__=['用量令牌','可选头相等','校验配置键','令牌计量','默认']#仅中文公开名（Cordis 槽另挂）

def 用量令牌(用量):#合计提供方用量桶
    """合计互不相交的提供方用量桶，不把推理输出再计一次。"""
    缓存读=试取(用量,'cacheReadTokens')#缓存读
    缓存写=试取(用量,'cacheWriteTokens')#缓存写
    return 取(用量,'inputTokens')+(0 if 缓存读 is None else 缓存读)+(0 if 缓存写 is None else 缓存写)+取(用量,'outputTokens')#未缓存输入加缓存加输出

def 可选头相等(左,右):#比较可选信封
    """比较可选信封，使无头估算也能跟踪后续表面增量。"""
    if 左 is None or 右 is None:#一方缺席
        return 左 is 右#两边都缺才等
    return 请求头是否相等(左,右)#两边都有则逐字段

def 校验配置键(配置):#拒绝未知配置键
    """在默认值能把它们藏起来之前拒绝过时或拼错的键。"""
    for 键 in 配置:#遍历自有键
        raise Exception(f'TokenMeterConfig: unknown key "{键}" (no settings are supported)')#不支持任何设置

class 令牌计量(服务):#token 计量服务
    """一份服务级估算器与按会话隔离折叠的回放所有者。"""
    Config=模式.对象({})#空配置模式（Cordis 协议槽；无设置项）

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

        ctx.inject(['sessionProjections'],挂投影)#有投影注册表才挂

        def 追上(会话,*位置参数):#已有折叠才追上
            """已有折叠才追上。"""
            if 会话 in 自身.状态表:#已有折叠
                自身._同步(会话)#追上

        ctx.on('session/event',追上)#新事件

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
        锚点=状态['anchor']#最新锚点
        if 锚点 is not None and 可选头相等(锚点['header'],头):#信封匹配则可复用锚点
            基线=锚点['baseline']#沿用锚点基线
            表面增量=状态['surfaceTokens']-锚点['surfaceTokens']#表面相对锚点
        elif 头 is None and 状态['surfaceTokens']==0:#无头且空表面
            基线={'kind':'none','tokens':0}#尚无基线
            表面增量=0#无增量
        else:#信封变了或无法复用
            基线={'kind':'estimated','tokens':计价请求头(头)+状态['surfaceTokens']}#完整启发式
            表面增量=0#已含在基线里
        return 深冻结(结构化克隆({
            'logRevision':状态['consumedEvents'],#已消费修订
            'baseline':基线,#基线
            'surfaceDeltaTokens':表面增量,#表面增量
            'totalTokens':max(0,基线['tokens']+表面增量),#非负总压力
            'surfaceTokens':状态['surfaceTokens'],#表面合计
            'nodes':状态['surface'],#表面节点
        }))#拆离并冻结

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
        种类=取(事件,'type')#事件类型
        数据=取(事件,'data')#载荷
        if 种类=='request/header':#请求头
            下一头=归一请求头(取(数据,'header'))#更新规范头
        elif 种类=='step/start':#步开始
            if 状态['stepStart'] is not None:#已有打开步
                打开=状态['stepStart']#打开步
                raise Exception(
                    f'token meter: step/start at seq {取(事件,"seq")} arrived before turn {打开["turn"]}/step {打开["step"]} ended'
                )#步未闭合
            下一步起点={'turn':取(数据,'turn'),'step':取(数据,'step'),'surfaceTokens':状态['surfaceTokens']}#记下打开时表面
        elif 种类=='step/end':#步结束
            打开=状态['stepStart']#打开步
            if 打开 is None or 打开['turn']!=取(数据,'turn') or 打开['step']!=取(数据,'step'):#不成对
                raise Exception(f'token meter: step/end at seq {取(事件,"seq")} has no matching step/start event')#不成对
            下一步起点=None#关闭步
        表面=折叠表面令牌(状态['surface'],事件) if 是否表面事件(事件) else None#按节点折叠
        if 种类=='assistant/message':#助手定稿
            打开=状态['stepStart']#打开步
            if 打开 is None or 打开['turn']!=取(数据,'turn') or 打开['step']!=取(数据,'step'):#不成对
                raise Exception(f'token meter: assistant/message at seq {取(事件,"seq")} has no matching step/start event')#不成对
            事件令牌=表面['tokens']#本事件表面价格
            用量=试取(数据,'usage')#提供方用量
            if 用量 is not None and 下一头 is not None:#有用量且有头
                提供方助手=自身._估算提供方助手(会话,事件,事件令牌)#提供方输出计价
                锚点表面=打开['surfaceTokens']+提供方助手#打开步表面加提供方输出
                提供方合计=用量令牌(用量)#提供方合计
                估算锚点=计价请求头(下一头)+锚点表面#完整启发式锚点
                if 提供方合计>=估算锚点:#提供方不低于启发式
                    基线={'kind':'usage','tokens':提供方合计,'usage':用量}#用提供方
                else:#否则启发式
                    基线={'kind':'estimated','tokens':估算锚点}#启发式
                下一锚点={'header':下一头,'surfaceTokens':锚点表面,'baseline':基线}#新锚点
            else:#没有用量或没有头
                锚点表面=打开['surfaceTokens']+事件令牌#打开步表面加持久输出
                下一锚点={
                    'header':下一头,#当时信封
                    'surfaceTokens':锚点表面,#当时表面
                    'baseline':{'kind':'estimated','tokens':计价请求头(下一头)+锚点表面},#估算
                }#启发式锚点
        状态['header']=下一头#提交头
        状态['stepStart']=下一步起点#提交打开步
        if 表面 is not None:#有表面折叠
            状态['surface']=表面['nodes']#下一表面
            状态['surfaceTokens']+=表面['deltaTokens']#更新合计
        状态['anchor']=下一锚点#提交锚点

    def _估算提供方助手(自身,会话,事件,持久事件令牌):#按源块估算提供方助手输出
        """从用量锚点所引用的精确块序号重组提供方输出。

        缺失的遗留源序号保守地把持久输出当作提供方输出；显式空列表给已知空流计价。
        """
        源序号=试取(事件,'sourceEventSeqs')#源块序号
        if 源序号 is None:#遗留：用持久价格
            return 持久事件令牌#持久输出价格
        组装器=块组装器()#重组流
        已见=set()#已见序号
        定稿序号=取(事件,'seq')#定稿序号
        数据=取(事件,'data')#定稿载荷
        日志=会话.events#只追加日志
        for 序号 in 源序号:#逐个源序号
            if 序号>=定稿序号:#不早于定稿
                raise Exception(f'token meter: assistant/message at seq {定稿序号} source seq {序号} is not earlier')#必须更早
            if 序号 in 已见:#重复引用
                raise Exception(f'token meter: assistant/message at seq {定稿序号} repeats source seq {序号}')#不得重复
            已见.add(序号)#记下已见
            源事件=日志[序号]#按下标取源事件
            if 取(源事件,'type')!='assistant/chunk':#不是块
                raise Exception(f'token meter: assistant/message at seq {定稿序号} source seq {序号} is not assistant/chunk')#必须是块
            源数据=取(源事件,'data')#源载荷
            if 取(源数据,'turn')!=取(数据,'turn') or 取(源数据,'step')!=取(数据,'step'):#不在同一步
                raise Exception(f'token meter: assistant/message at seq {定稿序号} source seq {序号} belongs to another step')#必须同一步
            组装器.推入(取(源数据,'chunk'))#喂进组装器
        提供方内容=组装器.块列表()#组装提供方块
        if len(提供方内容)==0:#空流
            return 0#已知空流
        return 计价内容(提供方内容)+角色开销#计价

默认=令牌计量#中文默认导出
default=令牌计量#Cordis默认导出（协议槽）
