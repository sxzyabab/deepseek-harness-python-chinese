__all__=['已知会话事件类型']#仅中文公开名

已知会话事件类型=frozenset((#本构建认识的会话事件类型
    'agent-preset/selected',#Agent 预设已选
    'agent/inbox/spliced',#收件箱拼接
    'approval/asked',#已询问审批
    'approval/decided',#审批已决
    'approval/policy',#审批策略
    'assistant/attempt',#助手尝试
    'assistant/message',#助手消息
    'command/done',#命令完成
    'command/run',#命令运行
    'compaction/end',#压缩结束
    'compaction/prune',#压缩修剪
    'compaction/start',#压缩开始
    'compaction/summary',#压缩摘要
    'deliverables/presented',#文件产出已呈现
    'feedback/message-delete',#反馈删除
    'feedback/message-put',#反馈写入
    'feedback/record',#反馈记录
    'goal/change',#目标变更
    'hook/invoked',#钩子已调用
    'hook/result',#钩子结果
    'llm/retry',#模型重试
    'llm/retry-started',#模型重试已开始
    'model/selection',#模型选择
    'permission/preset',#权限预设
    'plan/mode',#计划模式
    'request/context',#请求上下文
    'request/header',#请求头
    'sandbox/mode',#沙盒模式
    'schedule/change',#日程变更
    'session-log-deepseek/delivery-accepted',#投递接受
    'session/end-seed',#会话种子结束
    'session/title',#会话标题
    'session/title-llm-request',#会话标题模型请求
    'step/end',#步骤结束
    'step/start',#步骤开始
    'subagent/catalog',#子智能体目录
    'subagent/descriptor',#子 Agent 描述符
    'subagent/model-selection-policy',#子智能体模型策略
    'system/message',#系统消息
    'team/member',#团队成员
    'team/message/delivered',#团队消息送达
    'team/message/queued',#团队消息入队
    'team/task',#团队任务
    'todo/write',#待办写入
    'tool-workflow/agent-end',#工具工作流 Agent 结束
    'tool-workflow/agent-start',#工具工作流 Agent 开始
    'tool-workflow/run-end',#工具工作流运行结束
    'tool-workflow/run-start',#工具工作流运行开始
    'tool/call',#工具调用
    'tool/ptc-dispatch',#ptc 分发
    'tool/ptc-dispatch-start',#ptc 分发开始
    'tool/result',#工具结果
    'turn/end',#轮次结束
    'turn/start',#轮次开始
    'user/message',#用户消息
    'web/deepseek-search-llm-request',#搜索 LLM 请求
))#集合结束
