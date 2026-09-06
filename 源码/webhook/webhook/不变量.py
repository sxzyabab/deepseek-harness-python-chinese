"""`@deepseek-ai/dsh-webhook` 的本包拥有不变量配套。对齐上游 `webhook/src/invariant.ts`。"""
包名='@deepseek-ai/dsh-webhook'#本包的不变量所有权名
名称='webhook-invariant'#配套不变量插件名
注入=['invariants']#依赖 invariants 服务

__all__=['包名','名称','注入','安装','应用']#仅中文公开名

def 安装(上下文对象,失败):#安装 webhook 来源准入不变量
    """校验 webhook 来源消息已属于其 cwd 工作区。"""
    def 内部派发(_模式,事件名,参数,*位置参数):#提交前检查
        """提交前检查 session/event。"""
        if 事件名!='session/event':#非会话事件
            return#放过
        会话,事件=参数[0],参数[1]#会话与事件
        if 事件['type']!='agent/inbox/spliced':#非收件箱拼接
            return#放过
        插入列表=事件['data']['inserted'] if 'inserted' in 事件['data'] else []#插入消息
        webhook消息=[消息 for 消息 in 插入列表 if 消息['source']['kind']=='webhook']#webhook来源
        if len(webhook消息)==0:#没有 webhook 消息
            return#放过
        头=会话['header']#跨包会话为 dict
        工作目录=头['cwd'] if 'cwd' in 头 else None#会话 cwd
        会话号=头['id']#会话 id
        if 工作目录 is None:#无 cwd
            return 失败(f'webhook Session "{会话号}" has no cwd')#失败
        拥有者列表=[]#匹配工作区
        for 工作区 in 上下文对象.workspaceRegistry.list():#跨包工作区为 dict
            会话号列表=工作区['sessionIds'] if 'sessionIds' in 工作区 else []#会话列表
            if 会话号 in 会话号列表:#属于该工作区
                拥有者列表.append(工作区)#记下
        if len(拥有者列表)!=1:#不是恰好一个
            return 失败(f'webhook Session "{会话号}" belongs to {len(拥有者列表)} Workspaces at prompt admission')#失败
        if 拥有者列表[0]['path']!=工作目录:#cwd不一致
            失败(f'webhook Session "{会话号}" cwd {repr(工作目录)} differs from its Workspace path')#失败
    上下文对象.监听('internal/dispatch',内部派发,{'全局':True})#全局监听

安装.inject=['workspaceRegistry']#安装时还要 workspaceRegistry

def 应用(上下文对象):#注册本包不变量配套
    """注册本包的不变量配套，返回拆除器。"""
    return 上下文对象.invariants.register(包名,安装)#同步登记

name=名称#框架槽
inject=注入#框架槽
apply=应用#框架槽
