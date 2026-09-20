"""会话集群所调用的 Remote 命名空间约定。

运行时以宿主提供的 remote 对象承载；本模块只文档化期望形状。
"""
__all__=['会话远程面说明']#仅中文公开名

会话远程面说明={
    'commands':'execute(agentId, line, attachments, signal?)',#斜杠命令
    'session':'list/search/create/fork/prompt/… 见传输与 Host Remote',#会话
    'subagents':'list/prompt/interruptByParent',#子智能体
    '$stream':'网关流工厂（若已移植）',#流
}#形状说明
