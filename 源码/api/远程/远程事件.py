"""本应用转发宿主事件白名单的唯一出处。

对齐上游 `remotes/src/remote-events.ts`。公开面仅中文名。配置键、事件名字面量保持上游。
"""
远程转发事件=(#宿主事件转发白名单
    'agent-preset/selected',#智能体预设已选定
    'commands/change',#命令表已变更
    'credentials/updated',#凭证已更新
    'cordis/request-run',#请求运行动态包
    'cordis/request-run-resolved',#动态包运行请求已决议
    'cordis/dynamic-package',#动态包清单
    'cordis/dynamic-retract',#动态包撤回
    'cordis/inspect-query',#动态包探查查询
    'cordis/inspect-query-resolved',#动态包探查查询已决议
    'llm/adapters-updated',#大模型适配器已更新
    'settings/document-updated',#设置文档已更新
)#只读元组，元素为字面量事件名

API_REMOTE_FORWARDED_EVENTS=远程转发事件#上游常量名对照（载荷字面量出处）

__all__=['远程转发事件','API_REMOTE_FORWARDED_EVENTS']#公开面
