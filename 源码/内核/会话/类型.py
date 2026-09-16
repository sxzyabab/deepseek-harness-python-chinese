from typing import Literal,NotRequired,TypedDict#字面量、可选字段与结构类型

安全整数上限=9007199254740991#JS Number.MAX_SAFE_INTEGER

__all__=[#仅中文公开名
    '会话标识','会话格式版本','安全整数上限','会话头字段','会话头',
    '创建会话选项','会话种子事件状态','恢复会话选项','准备会话选项',
    '智能体取消原因','轮次结束取消原因','轮次结束原因映射','轮次结束原因',
    '待办状态','待办条目','纪元请求头','请求上下文','请求头原因',
    '核心会话事件类型','工具结果错误','表面事件类型','表面操作','表面意图','会话事件信封字段',
]#公开面结束

def 会话标识(标识):#品牌会话 id
    """把字符串标成会话标识，不做校验。"""
    return 标识#编译期品牌在 Python 中无运行时成本

会话格式版本=3#当前逻辑格式版本

#不可变的已校验存储元数据，放在对话事件日志之外（对齐上游 SessionHeader）。
会话头字段=(#会话头字段键表
    'version',#磁盘格式版本，创建时从会话格式版本盖上
    'id',#会话 id（镜像 Session.id）
    'createdAt',#创建时的非负安全整数 Unix 纪元毫秒
    'cwd',#可选：创建时所在绝对工作目录
    'parentSession',#可选：分叉自的父会话 id
    'isSeeded',#是否含分叉继承的事件前缀
    'origin',#可选：来源分类，仅允许 "subagent"
    'delegationDepth',#可选：委托深度（顶层缺省为零）
    'agentPreset',#可选：本会话 Agent 组合自的预设 id
)#会话头字段结束

class 会话头(TypedDict):#不可变已校验存储元数据
    version:int#磁盘格式版本
    id:str#会话 id（会话标识品牌）
    createdAt:int#创建时 Unix 纪元毫秒
    cwd:NotRequired[str]#可选绝对工作目录
    parentSession:NotRequired[str]#可选父会话 id
    isSeeded:bool#是否含种子前缀
    origin:NotRequired[Literal['subagent']]#可选来源分类
    delegationDepth:NotRequired[int]#可选委托深度
    agentPreset:NotRequired[str]#可选 Agent 预设 id

class 创建会话选项(TypedDict):#经存储创建会话的选项
    seed:NotRequired[list]#可选初始回放或分叉历史
    inheritedEventCount:NotRequired[int]#meta.isSeeded 为真时的精确分叉继承前缀长度
    meta:NotRequired[dict]#发表前读一次的存储元数据字段

会话种子事件状态=Literal['detached','shared-frozen']#可采纳会话种子的别名状态

class 恢复会话选项(TypedDict):#转给准备的可采纳存储值，不再二次拷贝或冻结
    seed:list#独立拥有或已深冻结的事件
    meta:会话头#要就地校验并冻结的独立拥有存储元数据
    inheritedEventCount:int#从存储解码的精确分叉继承前导事件条数
    eventState:会话种子事件状态#产出该种子的操作携带的别名状态

准备会话选项=创建会话选项|恢复会话选项#构造尚未发表会话时接受的输入

智能体取消原因=Literal['user','parent','hook','disposed']#活动 Agent 驱动器为何被取消（hook 另带 reason 字符串）
轮次结束取消原因=智能体取消原因|Literal['legacy']#可持久化取消原因，含无原因的导入

轮次结束原因映射={#一轮为何结束；可合并扩展的和类型（键为 reason.kind）
    'completed':{'kind':'completed'},#正常完成
    'aborted':{'kind':'aborted'},#取消请求打断在线轮次；另带 reason
    'blocked':{'kind':'blocked'},#预步骤拒绝
    'error':{'kind':'error'},#轮次失败；另带结构化 error
    'max-tokens':{'kind':'max-tokens'},#至少一步到达输出 token 上限
    'interrupted':{'kind':'interrupted'},#持久化后端关闭崩溃孤儿轮次
}#轮次结束原因映射结束
轮次结束原因=Literal['completed','aborted','blocked','error','max-tokens','interrupted']#轮次结束原因联合

待办状态=('pending','in_progress','completed')#待办生命周期三态，无 id

def 待办条目(内容,状态):#构造一条待办
    """一条待办：短祈使内容和三态状态。整表替换所以不需要稳定身份。"""
    return {'content':内容,'status':状态}#一条待办快照

class 纪元请求头(TypedDict):#派生历史之外的已记下请求状态：调用配置与工具
    config:object#调用配置（提供方、模型、推理力度与采样标量）
    adapterDefaults:NotRequired[dict]#由精确适配器物化的有效配置字段旗标
    tools:NotRequired[list]#组装后的工具模式；无则缺省

class 请求上下文(TypedDict):#一条已解析模型路由的注册绑定元数据
    provider:str#提供方
    model:str#模型
    contextWindow:NotRequired[int]#广告的最大请求加响应上下文 token 数
    systemPromptUpdate:NotRequired[Literal['in-history']]#系统提示更新模式

请求头原因=Literal['initial','resume','change','series']#为何追加 request/header 快照

class 工具结果错误(TypedDict):#tool/result.error；仅结果块 isError 时允许
    name:str#失败身份名
    code:str#失败码
    reason:NotRequired[str]#面向用户的原始原因，在模型内容之外

核心会话事件类型=Literal[#核心事件类型（线协议英文）
    'turn/start','turn/end','step/start','step/end',
    'user/message','system/message','assistant/message','assistant/attempt',
    'tool/call','tool/result','request/header','request/context','session/end-seed',
]#核心类型结束

表面事件类型=frozenset(['system/message','user/message','assistant/message','tool/result'])#表面事件类型
表面操作=Literal['append']|dict#追加，或 {op:'replace',startSeq,endSeq}
表面意图=Literal['append','replace']#表面意图

会话事件信封字段=('type','seq','time','data','ignorable','sourceEventSeqs','surfaceOp')#事件信封字段
