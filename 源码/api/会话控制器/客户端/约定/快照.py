"""会话拥有的可观察状态约定（不含 Conversation 目标数据）。

公开面仅中文名。形状以 dict 承载；本模块文档化字段名。
"""
__all__=['会话快照字段','打开状态','待定放置']#仅中文公开名

打开状态=('cold','loading','open','error')#打开生命周期
待定放置=('transcript','queued','steering')#提交放置

会话快照字段=(#SessionSnapshot 键
    'sessionId','pendingSubmissions','running','subagent','removed',
    'openState','openError','hasMore','loadingOlder','promptError','blank',
    'lastAgentError','promptAttempted','awaitingFirstTurn',
)#字段结束
