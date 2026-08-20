"""ConversationSnapshot / ConversationNode：逻辑层喂给 UI 的唯一数据结构。

对齐上游 `runtime/src/client/sessions/conversation.ts`。公开面仅中文名。
发布约定：每次变更都换顶层对象；未变的子结构保持原引用。
节点与快照以字典形态承载；本模块提供分类器、空快照单例与字段约定。
callId/approvalId 此处保持裸 str（方便时再收窄到真正的品牌类型）。
"""
from typing import TypedDict,NotRequired,Literal,Any#结构类型
from session.类型 import 待办条目#再导出 TodoItem（session 权威）

__all__=[#仅中文公开名
    '待办条目',#TodoItem 再导出
    '转助手块','转助手块们','空会话视图','空聊天快照',
    '打开状态','作曲器阶段',
    '助手请求配置','助手来源视图','助手块种类','助手块',#AssistantBlock
    '用户消息节点','助手计时','助手消息节点','转向消息节点',
    '上下文消息节点','模型重试节点','回合错误节点','回合满token节点',
    '工具结果节点','压缩摘要节点','未知表面节点','命令节点',
    '会话节点种类','会话节点','工具调用块',#ConversationNode / ToolCallBlock
    '运行中工具调用','排队消息','部分助手',
    '提示错误','聊天节点仓库','聊天位置节点索引','遗留会话切片',
    '聊天快照','会话快照',
]#公开面结束

#------------------------------ 闭集常量 ------------------------------

打开状态=('cold','loading','open','error')#OpenState
作曲器阶段=('blank','engaging','active')#ComposerPhase
助手块种类=('text','reasoning','image','tool-call','other')#AssistantBlock.kind
会话节点种类=(#ConversationNode 判别
    'user','assistant','steering','context','model-retry',
    'turn-error','turn-max-tokens','tool-result','command',
    'compaction','unknown',
)#结束种类

#------------------------------ 分类器（上游运行时函数） ------------------------------

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 转助手块(块):#分类一块
    """分类一块（ToolCallBlock 字段是 id/arguments，映射到 callId/argsRaw）。

    @param 块 - 一块核心内容块。
    @returns UI 分类。
    """
    类型=取字段(块,'type')#核心块类型
    if 类型=='text':#文本
        return {'kind':'text','text':取字段(块,'text')}#文本
    if 类型=='reasoning':#推理
        return {'kind':'reasoning','text':取字段(块,'text')}#推理
    if 类型=='image':#图片
        return {'kind':'image','attachment':取字段(块,'attachment')}#图片
    if 类型=='tool-call':#工具调用头
        return {'kind':'tool-call','callId':str(取字段(块,'id')),'name':取字段(块,'name'),'argsRaw':取字段(块,'arguments')}#工具
    return {'kind':'other','block':块}#未知回退

def 转助手块们(内容):#批量分类
    """核心 ContentBlock[] → AssistantBlock[]。

    @param 内容 - 原样的核心内容块。
    @returns 源顺序的 UI 分类块。
    """
    return [转助手块(块) for 块 in 内容]#逐块分类

#------------------------------ 节点与辅助结构字段约定 ------------------------------

class 助手请求配置(TypedDict):#AssistantRequestConfig
    """一次提供方调用记下的请求配置。"""
    provider:str#提供方
    model:str#模型
    purpose:NotRequired[str]#用途
    thinking:NotRequired[str]#思考档
    reasoningEffort:NotRequired[str]#推理力度
    temperature:NotRequired[float]#温度
    maxTokens:NotRequired[int]#最大 token
    stop:NotRequired[list]#停止序列

class 助手来源视图(TypedDict):#AssistantProvenanceView
    """一次已完成请求报告的稳定提供方/模型身份。"""
    provider:str#提供方
    model:str#模型

class 助手文本块(TypedDict):#AssistantBlock text 臂
    """文本正文。"""
    kind:Literal['text']#判别
    text:str#正文

class 助手推理块(TypedDict):#AssistantBlock reasoning 臂
    """可折叠推理。"""
    kind:Literal['reasoning']#判别
    text:str#推理文本

class 助手图片块(TypedDict):#AssistantBlock image 臂
    """图片附件。"""
    kind:Literal['image']#判别
    attachment:Any#ImageAttachmentRef

class 助手工具调用头(TypedDict):#AssistantBlock tool-call 臂
    """工具调用卡片头。"""
    kind:Literal['tool-call']#判别
    callId:str#调用 id
    name:str#工具名
    argsRaw:str#原始参数

class 助手其它块(TypedDict):#AssistantBlock other 臂
    """其它回退。"""
    kind:Literal['other']#判别
    block:Any#原块

助手块=助手文本块|助手推理块|助手图片块|助手工具调用头|助手其它块#AssistantBlock

class 用户消息节点(TypedDict):#UserMessageNode
    """一条已定稿的用户消息。"""
    kind:Literal['user']#判别标签
    seq:int#事件序号
    time:int#来源会话事件 Unix 纪元毫秒
    content:list#内容块
    source:Any#来源载荷

class 助手计时(TypedDict):#AssistantTiming
    """用于派生助手延迟与吞吐的已记录边界。"""
    stepStartTime:Any#匹配 step/start；窗外为 None
    firstTokenTime:Any#首非空增量；无 token 增量为 None
    completedTime:int#最终 assistant/message 时间戳

class 助手消息节点(TypedDict):#AssistantMessageNode
    """一条已定稿（或因中断冻结）的助手消息。"""
    kind:Literal['assistant']#判别标签
    seq:int#事件序号
    time:int#时间戳
    turn:int#回合号
    step:int#步骤号
    blocks:list#已分类助手块
    messageId:NotRequired[Any]#定稿消息 id；中断冻结部分无
    usage:NotRequired[Any]#用量
    provenance:NotRequired[助手来源视图]#提供方/模型身份
    requestConfig:NotRequired[助手请求配置]#请求配置
    timing:NotRequired[助手计时]#计时
    interrupted:NotRequired[Literal[True]]#中断冻结

class 转向消息节点(TypedDict):#SteeringMessageNode
    """回合运行中从下一步收件箱接纳的一条人类消息。"""
    kind:Literal['steering']#判别标签
    messageId:Any#稳定消息身份
    seq:int#事件序号
    time:int#时间戳
    content:list#内容块
    source:Any#来源载荷

class 上下文消息节点(TypedDict):#ContextMessageNode
    """出现在流里的一条 context/system 注入。"""
    kind:Literal['context']#判别标签
    seq:int#事件序号
    time:int#时间戳
    content:list#内容块
    source:Any#来源载荷
    provenance:Any#ContextProvenanceView
    form:Any#KnownContextForm | None

class 模型重试节点(TypedDict):#ModelRetryNode = LlmRetryEventData & 扩展
    """已关闭失败步骤正在等待模型请求重试的持久通知。

    与上游 LlmRetryEventData 两臂相交字段一并交出；maxRetries 仅 normal 臂有。
    """
    kind:Literal['model-retry']#判别标签
    seq:int#事件序号
    time:int#时间戳
    retryState:Literal['scheduled','started','cancelled']#客户端派生生命周期
    retryId:Any#重试链身份 RetryId
    turn:int#回合
    step:int#步骤
    provider:str#提供方
    mode:Literal['normal','always']#重试模式
    policyKey:str#政策键
    retry:int#本次重试序号
    delayMs:float#等待毫秒
    failure:Any#触发失败 LlmFailure
    maxRetries:NotRequired[int]#最大重试次数（仅 normal）

class 回合错误节点(TypedDict):#TurnErrorNode
    """没有排期重试的回合的持久终端失败。"""
    kind:Literal['turn-error']#判别标签
    seq:int#所属 turn/end seq
    time:int#时间戳
    turn:int#回合号
    step:int#步骤号
    message:str#错误文案
    code:NotRequired[str]#错误码

class 回合满token节点(TypedDict):#TurnMaxTokensNode
    """因单次请求输出 token 上限而结束的回合的持久通知。"""
    kind:Literal['turn-max-tokens']#判别标签
    seq:int#所属 turn/end seq
    time:int#时间戳
    turn:int#回合号
    step:int#步骤号

class 工具结果节点(TypedDict):#ToolResultNode
    """一条工具结果，在窗口内时与其调用头配对。"""
    kind:Literal['tool-result']#判别标签
    seq:int#事件序号
    time:int#时间戳
    callId:str#调用 id
    call:Any#{name,argsRaw} | None
    callTime:Any#配对 tool/call 时间；窗外为 None
    content:list#结果内容
    isError:bool#是否错误
    error:NotRequired[dict]#错误名与码
    meta:NotRequired[Any]#元数据
    callView:Any#ToolCallView | None
    resultView:Any#ToolResultView | None
    subCalls:list#工具调用块（按派发顺序）

class 压缩摘要节点(TypedDict):#CompactionSummaryNode
    """一次已落地的压缩，标在检查点自己的日志位置。"""
    kind:Literal['compaction']#判别标签
    seq:int#替换 user/message 的 seq
    time:int#检查点时间戳
    summary:Any#摘要文本；窗外为 None
    summaryEventSeq:Any#compaction/summary seq；窗外为 None
    shadowedItemCount:Any#被盖条目数；不可用为 None
    shadowedTokenCount:Any#被盖 token 数；不可用为 None

class 未知表面节点(TypedDict):#UnknownSurfaceNode
    """本 UI 版本不认识的表面事件回退。"""
    kind:Literal['unknown']#判别标签
    seq:int#事件序号
    time:int#时间戳
    type:str#事件类型
    data:Any#原始载荷

class 命令节点(TypedDict):#CommandNode
    """一次斜杠命令生命周期（command/run ↔ command/done）。"""
    kind:Literal['command']#判别标签
    seq:int#锚定 seq
    time:int#时间戳
    commandId:Any#宿主配对 id
    name:Any#命令名；run 窗外为 None
    args:Any#原样 rawInput；窗外为 None
    outcome:Any#{kind,text?,sourceEventSeq?} | None

会话节点=(#ConversationNode 判别联合
    用户消息节点|助手消息节点|转向消息节点|上下文消息节点|
    模型重试节点|回合错误节点|回合满token节点|工具结果节点|
    命令节点|压缩摘要节点|未知表面节点
)#结束会话节点

class 运行中工具调用(TypedDict):#RunningToolCall
    """进行中的工具卡片材料：已见 tool/call，尚未见 tool/result。"""
    callId:str#调用 id
    name:str#工具名
    argsRaw:str#原始参数
    turn:int#回合号
    step:int#步骤号
    time:int#时间戳
    callView:Any#ToolCallView | None
    subCalls:list#工具调用块

工具调用块=运行中工具调用|工具结果节点#ToolCallBlock

class 排队消息(TypedDict):#QueuedMessage
    """权威 session/queue 快照里的一次瞬时收件箱出现。"""
    id:Any#队列项 id
    messageId:Any#稳定消息身份
    placement:Literal['queued','steering','context']#放置
    content:list#完整内容
    preview:str#预览
    text:Any#可编辑文本；含非文本块时为 None

class 部分助手(TypedDict):#PartialAssistant
    """进行中的助手输出（块累加器产物）。"""
    turn:int#回合号
    step:int#步骤号
    blocks:list#已分类助手块

class 提示错误(TypedDict):#PromptError
    """输入错误条上展示的发送/停止失败。"""
    op:Literal['send','stop']#发送或停止
    error:Any#RpcError

#------------------------------ 仓库与快照协议 ------------------------------

class 聊天节点仓库:#ChatNodeStore（稳定按键活读者）
    """旧 ChatSnapshot 通过本仓库观察后来的 flush。"""

    def get(自身,键):#按键读
        """读当前节点（可见或隐藏）。"""
        raise NotImplementedError#由装配器实现

    def values(自身):#枚举节点
        """当前已物化的全部节点，不强加渲染顺序。"""
        raise NotImplementedError#由装配器实现

class 聊天位置节点索引:#ChatLocationNodeIndex
    """稳定的活位置索引。"""

    def getTurn(自身,回合):#按回合读
        """该回合内有序的聊天节点键。"""
        raise NotImplementedError#由装配器实现

    def getStep(自身,回合,步骤):#按步骤读
        """该步骤内有序的聊天节点键。"""
        raise NotImplementedError#由装配器实现

class 遗留会话切片(TypedDict):#LegacyConversationSlice
    """支撑 StatsLine 与遗留顶层快照字段的兼容投影。"""
    nodes:list#节点列表
    turnTimings:Any#回合计时 Map
    turnEnds:Any#回合结束 seq Map
    partial:Any#部分助手 | None
    runningCalls:list#运行中调用

class 聊天快照(TypedDict):#ChatSnapshot
    """增量聊天发布：不可变顺序加上稳定的按键活读者。"""
    order:list#渲染顺序
    nodes:Any#聊天节点仓库
    locations:Any#聊天位置节点索引
    timeline:Any#对话时间线快照
    legacy:遗留会话切片#遗留切片

class 会话快照(TypedDict):#ConversationSnapshot
    """Session 交给 uSES 的不可变快照约定。"""
    sessionId:Any#会话 id
    views:Any#已登记目标快照仓库
    chat:聊天快照#最终聊天目标
    nodes:list#遗留顶层节点列表
    turnTimings:Any#回合计时
    turnEnds:Any#回合结束
    partial:Any#部分助手 | None
    runningCalls:list#运行中调用
    pending:list#待处理交互
    queue:list#收件箱
    running:bool#是否在跑
    subagent:Any#{address,parentAvailable} | None
    composerPhase:Literal['blank','engaging','active']#作曲器阶段
    removed:bool#host/session-removed 之后
    openState:Literal['cold','loading','open','error']#打开状态
    openError:Any#RpcError | None
    hasMore:bool#窗外是否还有更早历史
    loadingOlder:bool#是否正在加载更早页
    promptError:Any#提示错误 | None
    blank:bool#空白位
    lastAgentError:Any#最近智能体错误 | None

#------------------------------ 空单例（上游 EMPTY_*） ------------------------------

空列表=()#空列表单例
空时间线={'turnOrder':空列表,'turns':{}}#空时间线单例

def _空读(_键=None):#空仓库读
    """无构建器时读不到。"""
    return None#缺席

def _空值们():#空枚举
    """无节点。"""
    return 空列表#空

def _空回合(_回合=None):#空回合键
    """回合内无键。"""
    return 空列表#空

def _空步骤(_回合=None,_步骤=None):#空步骤键
    """步骤内无键。"""
    return 空列表#空

空会话视图={'get':_空读}#EMPTY_CONVERSATION_VIEWS

空聊天快照={#EMPTY_CHAT_SNAPSHOT
    'order':空列表,#空顺序
    'nodes':{'get':_空读,'values':_空值们},#空节点仓库
    'locations':{'getTurn':_空回合,'getStep':_空步骤},#空位置索引
    'timeline':空时间线,#空时间线
    'legacy':{#空遗留切片
        'nodes':空列表,#无节点
        'turnTimings':{},#无回合计时
        'turnEnds':{},#无回合结束
        'partial':None,#无部分助手
        'runningCalls':空列表,#无运行中调用
    },#结束 legacy
}#结束空聊天快照
