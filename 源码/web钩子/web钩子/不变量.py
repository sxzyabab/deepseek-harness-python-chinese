"""校验 webhook 来源消息已属于其 cwd 工作区。"""
包名='@deepseek-ai/dsh-webhook'
名称='webhook-invariant'
依赖=['invariants']

__all__=['包名','名称','依赖','应用','默认']

def 安装(上下文,失败):
    """校验 webhook 来源消息已属于其 cwd 工作区。"""
    def 内部派发(_模式,事件名,参数,*位置参数):
        """提交前检查 session/event。"""
        if 事件名!='session/event':
            return
        会话,事件=参数[0],参数[1]
        if 事件['type']!='agent/inbox/spliced':
            return
        插入列表=事件['data']['inserted'] if 'inserted' in 事件['data'] else []
        webhook消息=[消息 for 消息 in 插入列表 if 消息['source']['kind']=='webhook']
        if len(webhook消息)==0:
            return
        头=会话['header']#跨包会话为 dict
        工作目录=头['cwd'] if 'cwd' in 头 else None
        会话号=头['id']
        if 工作目录 is None:
            return 失败(f'webhook Session "{会话号}" has no cwd')
        拥有者列表=[]
        for 工作区 in 上下文.workspaceRegistry.list():#跨包工作区为 dict
            会话号列表=工作区['sessionIds'] if 'sessionIds' in 工作区 else []
            if 会话号 in 会话号列表:
                拥有者列表.append(工作区)
        if len(拥有者列表)!=1:
            return 失败(f'webhook Session "{会话号}" belongs to {len(拥有者列表)} Workspaces at prompt admission')
        if 拥有者列表[0]['path']!=工作目录:
            失败(f'webhook Session "{会话号}" cwd {repr(工作目录)} differs from its Workspace path')
    上下文.监听('internal/dispatch',内部派发,{'全局':True})

安装.依赖=['workspaceRegistry']
安装.inject=安装.依赖

def 应用(上下文):
    """注册本包的不变量配套，返回拆除器。"""
    return 上下文.invariants.register(包名,安装)

默认=应用
name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
default=默认#框架槽
