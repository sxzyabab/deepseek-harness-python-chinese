"""工作流缝词汇：引擎消费与产出的请求/运行/结果类型，以及 `workflow/*` 事件载荷中的字段。仅类型（外加 id 品牌工厂），符合包约定。"""
from typing import Literal,NotRequired,TypedDict#字面量、可选字段与结构类型

def 工作流运行标识(标识):#把原始字符串打成运行标识
    """把字符串打成工作流运行标识。引擎铸造 UUID；测试可传入夹具。不做校验。"""
    return 标识#编译期品牌在 Python 中无运行时成本

工作流运行标识品牌='WorkflowRunId'#运行身份品牌名

class 工作流阶段(TypedDict):#脚本 meta.phases 中声明的一个阶段（仅进度词汇——阶段在观察者/界面里给智能体分组；不施加执行结构）
    title:str#阶段标题；phase() 调用按精确字符串匹配
    detail:NotRequired[str]#该阶段做什么的可选一行描述
    provider:NotRequired[str]#该阶段预期使用的可选提供方覆盖（仅供参考）
    model:NotRequired[str]#该阶段预期使用的可选模型覆盖（仅供参考）

class 工作流元数据(TypedDict):#脚本的身份块，作为普通 JSON 数据与脚本正文一并提供（面向模型的工具把它放在 meta 参数里），并在正文运行前由引擎校验；name/description 必填；其余为可选注解；字段词汇与 Claude Code 动态工作流的 meta 块一致
    name:str#短的 kebab-case 工作流名（展示 + 持久化键）
    description:str#该工作流做什么的一行描述
    whenToUse:NotRequired[str]#何时适用此工作流的可选指引（列表中展示）
    phases:NotRequired[list[工作流阶段]]#由 phase() 调用匹配的可选阶段声明

工作流停止原因=Literal['completed','cancelled','error']#运行为何结算：completed=脚本跑到最终 return；cancelled=运行被取消；error=脚本抛错、致命 WorkflowError 传播、或结果物化失败

class 工作流结果(TypedDict):#存活工作流运行兑现的结局；value 是脚本物化后的返回值（宿主领域的普通 JSON 数据；脚本返回 undefined 时为 null）——仅对 completed 有意义；非 completed 原因把失败放在 error 里
    value:object#脚本返回值（宿主 JSON 数据；无返回时为 null）
    stopReason:工作流停止原因#运行为何结算
    error:NotRequired[str]#失败消息（当且仅当 stopReason 不是 completed 时存在）
    agentsStarted:int#该运行整个生命周期内接受了多少次 agent() 调用；优雅结算时为脚本侧计数；终止路径上降级为宿主观察到的计数

class 工作流运行信息(TypedDict):#一次运行的身份细节，由每条 workflow/* 事件携带为借用的不可变数据，绝不是存活运行本身
    id:str#运行 id（工作流运行标识品牌）
    meta:工作流元数据#运行已校验的 meta 块

class 工作流智能体信息(TypedDict):#一次运行内某次 agent() 调用的身份（workflow/agent-start 载荷）
    seq:int#该次 agent() 调用在运行内的从 1 起的序号
    label:str#展示标签（label 选项，或提示词片段）
    phase:NotRequired[str]#该智能体所属阶段（phase 选项，否则为当前 phase() 标题）
    childId:str#子智能体缝上的子智能体 id（会话标识品牌）

工作流智能体结局=Literal['completed','failed','cancelled']#一次 agent() 调用如何结算：干净结果、子运行失败（脚本看到 null）、或运行取消

class 工作流智能体结束信息(工作流智能体信息):#一次 agent() 调用的结算（workflow/agent-end 载荷）
    outcome:工作流智能体结局#该次调用如何结算

class 工作流结果信息(TypedDict):#已结算运行作为事件数据的结局（workflow/end 载荷）：工作流结果去掉 value（观察结局的监听器不得收到调用方结果值的可变别名；需要该值的消费方持有运行并等待 result）
    stopReason:工作流停止原因#运行为何结算
    error:NotRequired[str]#失败消息（当且仅当 stopReason 不是 completed 时存在）
    agentsStarted:int#该运行接受了多少次 agent() 调用（见工作流结果.agentsStarted）

# 事件声明（仅文档；由引擎经 emitWorkflowEvent 派发；对齐上游 Cordis Events 扩充）：
# workflow/start(info) @mode emit：一次工作流运行已启动——脚本的 meta 块已校验，即将执行正文；与 workflow/end 成对。
# workflow/phase(info, title) @mode emit：脚本进入一个阶段（一次 phase(title) 调用）——供观察者分组进度；无执行语义。
# workflow/log(info, message) @mode emit：脚本写出一行叙述（一次 log(message) 调用）。
# workflow/agent-start(info, agent) @mode emit：一次 agent() 调用已建立已发布的子运行；与 workflow/agent-end 按 agent.seq 成对；若从未拿到已发布运行则这一对都不会发出。
# workflow/agent-end(info, agent) @mode emit：一次 agent() 调用已结算（干净结果、子运行失败、或运行取消）；与 workflow/agent-start 按 agent.seq 成对；终止路径上可由引擎合成 cancelled。
# workflow/end(info, result) @mode emit：一次工作流运行已结算；在 WorkflowRun.result 兑现时发出；与 workflow/start 成对；故意不含结果值。
