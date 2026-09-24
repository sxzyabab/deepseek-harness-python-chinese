from .团队动作 import 团队动作
from .文案 import 命名空间,中文,英文

__all__=['依赖','挂载智能体团队界面','登记界面']

依赖=['sessions','uiWorkspace','slots','locale']

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
    """登记词典与标题栏动作槽；面板读 Lead 的 agentTeam 投影，不做 Team RPC。"""
    def 卸词典():
        """登记词典并返回拆除器。"""
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})
    上下文.副作用(卸词典,'client-ui-agent-team: dictionaries')
    会话服务=上下文.sessions

    def 打开队友(会话标识,子会话标识):
        """从当前对话打开 roster 会话。"""
        父会话=领导会话标识(会话服务,会话标识)
        持有=会话服务.retainInfo(会话标识).getSnapshot()
        主视图=持有['retainedBy']['mainView'] if 'retainedBy' in 持有 and 'mainView' in 持有['retainedBy'] else 0
        if 主视图==0:
            return
        if 子会话标识==父会话:
            上下文.uiWorkspace.openSession(父会话)
            return
        上下文.uiWorkspace.openSession({
            'parentSessionId':父会话,
            'childSessionId':子会话标识,
            'mode':'continuable',
        })

    动作={'openTeammate':打开队友}
    def 注入动作():
        """槽注入 Team 动作。"""
        return 动作
    def 依赖动作():
        """登记标题栏动作槽。"""
        return 上下文.slots.register({
            'name':'conversation.session.header.actions',
            'id':'agent-team',
            'order':-20,
            'locale':命名空间,
            'inject':注入动作,
        },团队动作)
    上下文.slots.inject('conversation.session.header.actions',依赖动作)

def 挂载智能体团队界面(上下文,_贡献=None):
    """登记浏览器 UI；Team 行为在投影域，不再挂载 Team Remote。"""
    登记界面(上下文)
