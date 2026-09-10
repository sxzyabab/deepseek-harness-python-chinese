"""对外 sessions 服务面约定（ctx.sessions）。

对齐上游 `session-controller/src/client/contract/sessions.ts`。公开面仅中文名。
实现见 `客户端/服务.py`。
"""
__all__=['会话集面动词']#仅中文公开名

会话集面动词=(#ISessions 动词
    'create','open','openSubagent','subagentAddress','setSubagentCatalogOpen',
    'refreshSubagents','clear','refresh','search','fork','scope','scopeOf',
    'sessionOf','binding',
)#动词结束
