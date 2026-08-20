"""DeepSeek Harness SDK 运行时协议的具名线类型：三对请求/结果，以及四条服务端到客户端的通知载荷。

对齐上游 `sdk/protocol/src/types.ts`。公开面仅中文名。配置键、方法名与 `serverInfo.name` 字面量保持上游。
"""

__all__=[#仅中文公开名
    '初始化参数','初始化结果','会话提示参数','会话提示结果','SDK运行状态',
    '会话事件通知','会话状态通知','子智能体启动通知','子智能体结束通知',
    '装备SDK通知映射','装备SDK请求映射',
]#公开面结束

# 进程级 SDK 握手参数：工作目录、提供方、模型、可选输出 token 上限。
初始化参数=('cwd','provider','model','maxTokens')#握手请求字段键表

# 初始化返回的线稳定服务端身份。
初始化结果=('serverInfo',)#握手成功结果字段

# 一条 SDK 会话上的一次用户回合。
会话提示参数=('sessionId','contentBlocks')#会话提示请求字段

# 一次提示的持久入队回执。
会话提示结果=('messageId',)#排队结果字段

# 部署映射后的 SDK 结果：ok 表示已接受，其余为 error。
SDK运行状态=('ok','error')#回合或子智能体结果状态

# session.event 载荷字段。
会话事件通知=('sessionId','event')#会话事件通知字段

# 一个会话的整智能体生命周期状态。
会话状态通知=('sessionId','status')#会话状态通知字段

# subagent.started 载荷字段。
子智能体启动通知=('parentSessionId','childSessionId')#子智能体启动通知字段

# subagent.finished 载荷字段。
子智能体结束通知=(#子智能体结束通知字段
    'provider','agentId','parentSessionId','childSessionId',
    'status','stopReason','lastAssistantMessage',
)#字段结束

# 按 JSON-RPC 方法名划分的服务端到客户端通知（键为线方法名）。
装备SDK通知映射={#通知方法到载荷字段映射
    'session.event':会话事件通知,#会话事件
    'session.status':会话状态通知,#会话状态
    'subagent.started':子智能体启动通知,#子智能体启动
    'subagent.finished':子智能体结束通知,#子智能体结束
}#映射结束

# 客户端到服务端的请求方法及其参数与结果字段。
装备SDK请求映射={#请求方法到参数与结果字段映射
    'initialize':{'params':初始化参数,'result':初始化结果},#握手
    'session/prompt':{'params':会话提示参数,'result':会话提示结果},#会话提示
    'shutdown':{'params':None,'result':()},#关闭，结果为空对象
}#映射结束
