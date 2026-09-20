from .团队动作 import 团队动作
from .文案 import 命名空间,中文,英文

__all__=['依赖','挂载智能体团队界面','登记界面']

依赖=['sessions','uiWorkspace','remote','slots','locale']

def 领导会话标识(会话服务,会话标识):
    """把当前会话映射到 Team Lead 会话。"""
    绑定=会话服务.binding(会话标识)
    if 绑定 is None:
        return 会话标识
    会话=绑定.session
    if 会话 is None:
        return 会话标识
    快照=会话.getSnapshot()
    if 'subagent' not in 快照:
        return 会话标识
    子=快照['subagent']
    if 子 is None or 'address' not in 子:
        return 会话标识
    地址=子['address']
    if 地址 is None or 'parentSessionId' not in 地址:
        return 会话标识
    父=地址['parentSessionId']
    if 父 is not None:
        return 父
    return 会话标识

def 登记界面(上下文):
    """登记词典与标题栏动作槽。"""
    def 卸词典():
        """登记词典并返回拆除器。"""
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})
    上下文.副作用(卸词典,'client-ui-agent-team: dictionaries')
    会话服务=上下文.sessions

    def 加载(会话标识):
        """读总览 Remote。"""
        return 上下文.remote.agentTeams.view(领导会话标识(会话服务,会话标识)).等待()

    def 建任务(会话标识,输入):
        """建任务 Remote。"""
        return 上下文.remote.agentTeams.createTask(领导会话标识(会话服务,会话标识),输入).等待()

    def 更新任务(会话标识,输入):
        """更新任务 Remote。"""
        请求={
            'taskId':输入['taskId'],
            'expectedRevision':输入['expectedRevision'],
            'action':输入['action'],
        }
        if 'owner' in 输入 and 输入['owner'] is not None:
            请求['owner']=输入['owner']
        for 键 in ('subject','description','blockedBy','writeScopes'):
            if 键 in 输入 and 输入[键] is not None:
                请求[键]=输入[键]
        return 上下文.remote.agentTeams.updateTask(领导会话标识(会话服务,会话标识),请求).等待()

    def 打开队友(会话标识,成员):
        """打开 teammate 子会话。"""
        if 成员['role']!='teammate':
            return
        父会话=领导会话标识(会话服务,会话标识)
        会话服务.refreshSubagents(父会话)
        持有=会话服务.retainInfo(会话标识).getSnapshot()
        主视图=持有['retainedBy']['mainView'] if 'retainedBy' in 持有 and 'mainView' in 持有['retainedBy'] else 0
        if 主视图==0:
            return
        上下文.uiWorkspace.openSession({
            'parentSessionId':父会话,
            'childSessionId':成员['id'],
            'mode':'continuable',
        })

    动作={'load':加载,'createTask':建任务,'updateTask':更新任务,'openTeammate':打开队友}
    def 依赖动作():
        """登记标题栏动作槽。"""
        return 上下文.slots.register({
            'name':'conversation.session.header.actions',
            'id':'agent-team',
            'order':20,
            'locale':命名空间,
            'inject':动作,
        },团队动作)
    上下文.slots.inject('conversation.session.header.actions',依赖动作)

def 挂载智能体团队界面(上下文,贡献):
    """挂载一份生成的 Team Remote contribution，再注册其浏览器 UI。"""
    卸远程=上下文.remote.$mount(贡献).等待()
    界面=上下文.依赖启动(['sessions','uiWorkspace','remote.agentTeams','slots','locale'],登记界面)
    try:
        界面.等待()
    except Exception:#挂载 UI 可能抛 DOM/插件错误，契约未定所以收不窄
        界面.dispose().等待()
        卸远程()
        raise
    def 卸除():
        """卸 UI 与 Remote。"""
        界面.dispose().等待()
        卸远程()
    return 卸除
