"""会话拥有的可观察状态约定（不含 Conversation 目标数据）。

对齐上游 `session-controller/src/client/contract/snapshot.ts`。公开面仅中文名。
形状以 dict 承载；本模块文档化字段名。
"""
__all__=['会话快照字段','打开状态','排队放置']#仅中文公开名

打开状态=('cold','loading','open','error')#打开生命周期
排队放置=('queued','steering','context')#队列放置

会话快照字段=(#SessionSnapshot 键
    'sessionId','queue','pendingSubmissions','running','subagent','removed',
    'openState','openError','hasMore','loadingOlder','promptError','blank',
    'lastAgentError','promptAttempted','awaitingFirstTurn',
)#字段结束
