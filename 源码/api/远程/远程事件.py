"""本应用转发宿主事件白名单的唯一出处。

对齐上游 `remotes/src/remote-events.ts`。公开面仅中文名。配置键、事件名字面量保持上游。
"""
远程转发事件=(#宿主事件转发白名单；对齐上游 API_REMOTE_FORWARDED_EVENTS
    'agent-preset/selected',#智能体预设已选定
    'approval/request',#审批请求瀑布
    'api-session/activity',#会话活动
    'api-session/added',#会话已添加
    'api-session/error',#会话错误
    'api-session/removed',#会话已移除
    'api-session/status',#会话状态
    'commands/change',#命令表已变更
    'credentials/reference-updated',#凭证引用已更新
    'goal/activation-changed',#目标激活已变更
    'cordis/request-run',#请求运行动态包
    'cordis/request-run-resolved',#动态包运行请求已决议
    'cordis/dynamic-package',#动态包清单
    'cordis/dynamic-retract',#动态包撤回
    'cordis/inspect-query',#动态包探查查询
    'cordis/inspect-query-resolved',#动态包探查查询已决议
    'llm/adapters-updated',#大模型适配器已更新
    'settings/document-updated',#设置文档已更新
    'user-questions/request',#用户提问瀑布
)#只读元组，元素为字面量事件名

__all__=['远程转发事件']#公开面
