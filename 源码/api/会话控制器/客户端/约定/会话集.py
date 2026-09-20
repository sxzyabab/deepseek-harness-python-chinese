"""对外 sessions 服务面约定（ctx.sessions）。

实现见 `客户端/服务.py`。
"""
__all__=['会话集面动词']#仅中文公开名

会话集面动词=(#ISessions 动词
    'retain','using','retainInfo','retainAgentScope','create','subagentAddress',
    'setSubagentCatalogOpen','refreshSubagents','refresh','search','fork','scope',
    'scopeOf','sessionOf','binding',
)#动词结束
