"""缝面向消费方的约定：SubagentProvider 的请求、结果与能力类型，以及插件与宿主观察的 subagent/start 和 subagent/end 载荷。内部控制接口跟实现走——生命周期观察者在 lifecycle，续跑宿主在 continuation——因此本模块保持已发布表面。"""
from typing import Literal,NotRequired,TypedDict#字面量、可选字段与结构类型

def 子智能体跑标识(标识):#把字符串打成跑id品牌
    """把字符串打成 SubagentRunId。仅供服务铸造；消费方从不自己造键。"""
    return 标识#原样返回并打成跑id品牌

子智能体跑标识品牌='SubagentRunId'#跑身份品牌名

class 子智能体跑信息(TypedDict):#已发布子智能体跑的只观察身份细节，由 subagent/start 携带；一次性跑与可续跑 Activation 纪元共享此载荷
    runId:str#与配对终态事件共享的唯一身份（子智能体跑标识品牌）
    provider:str#子体首次创建时记下的提供方名
    id:str#子智能体的会话 id
    local:bool#SubagentRun.localAgent 在 start 兑现时是否存在的快照

class 子智能体跑结束信息(TypedDict):#已结算子智能体跑的只观察结局细节，由 subagent/end 携带，并通过 runId 与一份跑信息配对
    runId:str#与配对开始事件共享的唯一身份
    provider:str#配对开始事件携带的同一提供方名
    id:str#子智能体的会话 id
    local:bool#SubagentRun.localAgent 在 start 兑现时是否存在的快照
    stopReason:str#终态停止原因（子智能体停止原因）
    lastAssistantMessage:NotRequired[list]#最终助手输出；基础设施拒绝或子体未产出时缺席

class 子智能体能力(TypedDict):#提供方支持哪些启动时功能；服务在委托 start 之前检查
    outputSchema:bool#是否支持输出模式
    depthLimit:bool#是否支持深度上限
    toolFilter:bool#是否支持工具过滤
    persona:bool#是否支持人设

class 子智能体启动请求(TypedDict):#启动一次性子智能体时调用方要的东西
    label:NotRequired[str]#可选的短显示标签，与有会话的子体一起持久化
    prompt:list#作为子体用户消息投递的内容（内容块列表）
    parent:object#拉起方智能体（上游类型为 Agent）
    signal:object#来自拉起上下文的取消信号（上游类型为 AbortSignal）
    agentOptions:NotRequired[object]#可选子智能体选项
    outputSchema:NotRequired[object]#可选结构化输出模式（对象 JSON Schema）
    maxDepth:NotRequired[int]#正在启动的子体的可选绝对委托深度上限
    toolFilter:NotRequired[object]#可选的子工具作用域
    persona:NotRequired[str]#可选的每子体人设

class 已解析子智能体启动请求(子智能体启动请求):#start 解析耐久子描述符之后、面向提供方的一次性请求
    descriptor:object#有会话的提供方持久化进子日志的分离描述符

class 可续跑创建请求(TypedDict):#续跑管理器在物化一个可续跑子体的第一次激活时向提供方要的东西
    sessionId:str#已预留的耐久子会话 id，供提供方诊断
    parent:object#委托父智能体（上游类型为 Agent）
    signal:object#调用方取消（上游类型为 AbortSignal）

class 可续跑创建规格(TypedDict):#提供方对一个可续跑子体创建的分离贡献；这是数据，绝不是能力
    seed:NotRequired[list]#用来给子会话播种的父日志已完成回合前缀；全新子体则缺席

子智能体停止原因映射=TypedDict('子智能体停止原因映射',{#一次子智能体跑为何结束；可合并扩展（后端可加变体）；键含 max-tokens 故用函数式 TypedDict
    'completed':Literal['completed'],#子体正常结束其回合
    'aborted':Literal['aborted'],#经请求信号或拆除取消
    'error':Literal['error'],#模型或传输失败
    'max-tokens':Literal['max-tokens'],#子体在完成前碰到 token 上限
    'refusal':Literal['refusal'],#子体拒绝该任务
})#停止原因映射结束
子智能体停止原因=Literal['completed','aborted','error','max-tokens','refusal']#停止原因联合

class 子智能体结果(TypedDict):#子智能体跑的终态结局，由 SubagentRun.result 决议
    output:list#子体最终助手输出（内容块列表）；两者都没产出时为 []
    structured:NotRequired[object]#所请求 outputSchema 成功满足后的结构化结果
    stopReason:子智能体停止原因#跑为何结束

class 子智能体跑:#发布后返回的一次性子句柄协议；提示提交、回合工作以及该边界之后的基础设施故障属于 result
    """持有者所有的一次性子跑。提供方对象实现本协议：载荷字段名对齐上游 SubagentRun（id/localAgent/result）；拆除入口仅 销毁。"""
    id=None#父作用域跑 id（会话标识品牌；载荷键字面量）
    localAgent=None#精确的已发布进程内子体；远程跑为 None（载荷键字面量）
    result=None#结算结果承诺（载荷键字面量；上游为 Promise<SubagentResult>）

    def 销毁(自身):#取消剩余工作、达到子体静止并释放资源
        """取消剩余工作、达到子体静止并释放资源。幂等。"""
        raise NotImplementedError('子智能体跑.销毁')#由提供方实现

class 子智能体提供方:#运行子智能体的一个已登记传输协议；提供方是受信任的同进程实现
    """具名传输实现。登记名字段对齐上游 provider.name；能力与启动入口仅中文方法 启动 / 准备可续跑。"""
    name=None#唯一注册表名（例如 spawn、fork、acp；载荷键字面量）
    capabilities=None#本提供方支持的启动时功能（子智能体能力；载荷键字面量）
    inheritsParentContext=None#子体是否看见父的已完成回合前缀（描述性，非服务校验）

    def 启动(自身,请求):#建立一次性子体并在发布后返回其句柄
        """建立一次性子体并在发布后返回其句柄。"""
        raise NotImplementedError('子智能体提供方.启动')#由提供方实现

    def 准备可续跑(自身,请求):#可选：贡献区分本提供方可续跑子体的分离创建输入
        """可选可续跑创建能力；方法存在即能力。缺省实现表示不支持。"""
        raise NotImplementedError('子智能体提供方.准备可续跑')#由具备该能力的提供方覆写

# 事件声明（仅文档；由服务经生命周期发射器派发；对齐上游 Cordis Events 扩充）：
# subagent/provider-added(provider) @mode emit：提供方在注册表中变为可解析。
# subagent/provider-removed(name) @mode emit：提供方离开注册表；已接受的跑仍由持有者拥有。
# subagent/start(info) @mode emit：提供方建立了已发布子体；与 subagent/end 成对；作用域过滤按委托父载体。
# subagent/end(info) @mode emit：已发布子体结算；作用域过滤使用与 start 相同的委托父载体。
