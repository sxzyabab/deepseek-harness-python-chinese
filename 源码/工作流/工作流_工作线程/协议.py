"""宿主⇄worker 线路协议：每个方向一个字符串取值的消息标签枚举、一份给出各标签参数的载荷映射（唯一真相源），以及由此导出的消息联合。载荷按构造就是供跨线程传递的普通 JSON。两个方向都是封闭引擎协议，接收方使用断言永不；带类型的发送方让标签/载荷不匹配成为编译期错误，而不是静默跳过的消息。"""

class 工人到宿主类型:#worker→宿主消息类型
    """worker 发给宿主的消息标签（线路值就是标签字符串）。"""
    就绪='ready'#启动握手：会话已在监听，等待宿主到工人类型.开始
    阶段='phase'#观察者叙述：一次 phase(title) 调用
    日志='log'#观察者叙述：一次 log(message) 调用
    智能体开始='agent-start'#观察者生命周期：一次 agent() 调用已启动子
    智能体结束='agent-end'#观察者生命周期：一次 agent() 调用已结算
    子启动='child-start'#子 RPC：在宿主上启动子（由子已启动或子启动错误应答）
    子销毁='child-dispose'#子 RPC：销毁已启动的子（由子已销毁应答）
    结果='result'#该次运行唯一的终态结果

# 每个 worker→宿主标签携带的载荷（文档约定；运行时消息为 dict）：
# Ready: {}
# Phase: { title: str }
# Log: { message: str }
# AgentStart: { info: WorkflowAgentInfo }
# AgentEnd: { info: WorkflowAgentEndInfo }
# ChildStart: { callId: number; request: ChildStartRequest }
# ChildDispose: { callId: number }
# Result: { result: WorkflowResult }

class 宿主到工人类型:#宿主→worker 消息类型
    """宿主发给 worker 的消息标签（线路值就是标签字符串）。"""
    开始='go'#放开启动闸门：执行脚本正文
    取消='cancel'#取消运行：钩子开始抛错，脚本在下一次 await 处死掉
    子已启动='child-started'#子 RPC 应答：提供方兑现了已发布运行
    子启动错误='child-start-error'#子 RPC 应答：提供方的异步启动失败
    子已结算='child-settled'#子 RPC：已启动子的结果已兑现（其 JSON 投影）
    子失败='child-failed'#子 RPC：已启动子的结果被拒绝（基础设施故障，已渲染）
    子已销毁='child-disposed'#子 RPC 应答：一次请求的销毁已完成

# 每个宿主→worker 标签携带的载荷（文档约定）：
# Go: {}
# Cancel: { reason: str }
# ChildStarted: { callId: number; childId: str }
# ChildStartError: { callId: number; rendered: str }
# ChildSettled: { callId: number; result: ChildResult }
# ChildFailed: { callId: number; rendered: str }
# ChildDisposed: { callId: number }
