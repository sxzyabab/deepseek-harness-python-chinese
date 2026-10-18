'会话集群所调用的 Remote 命名空间约定'
__all__=['会话远程面说明','会话远程方法']#仅中文公开名

会话远程方法=(
    'list','search','create','selectModel','modelCatalog',
    'canOpenWorkspacePath','openWorkspacePath','workspacePathApplications',
    'rename','fork','prompt','attachment','updateQueue','cancel',
    'page','follow','projections','control',
)#session 命名空间方法

会话远程面说明={
    'commands':'execute(agentId, line, attachments, signal?)',#斜杠命令
    'session':'/'.join(会话远程方法),#会话，含 workspacePathApplications 与 projections
    'subagents':'prompt/interruptByParent',#子智能体
    '$stream':'网关流工厂',#流
}#形状说明
