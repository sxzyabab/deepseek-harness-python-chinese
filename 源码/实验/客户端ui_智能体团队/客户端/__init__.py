'登记智能体团队文案，并在会话标题栏挂上团队动作'
from . import 挂载,文案,团队动作

__all__=['挂载','文案','团队动作','依赖','应用']

依赖=挂载.依赖#注入名
命名空间=文案.命名空间#词典命名空间
中文=文案.中文#中文表
英文=文案.英文#英文表


def 应用(上下文,配置=None):
    '登记词典和会话标题栏动作。面板读 Lead 的 agentTeam 投影，不做团队 RPC'
    def 登记词典():
        '登记中英文案表。界面显示不走英文表'
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})
    上下文.副作用(登记词典,'client-ui-agent-team: dictionaries')
    会话服务=上下文.sessions#会话服务

    def 打开队友(会话标识,子会话标识):
        '从当前对话打开成员会话。主视图没有留住这一会话就不动'
        绑定=会话服务.binding(会话标识)#当前绑定
        父会话=会话标识#默认就是 Lead
        if 绑定 is not None:
            快照=绑定['session'].getSnapshot()#会话快照
            子智能体=快照.get('subagent')#子智能体
            地址=None if 子智能体 is None else 子智能体.get('address')#地址
            if 地址 is not None and 地址.get('parentSessionId') is not None:
                父会话=地址.get('parentSessionId')#父会话
        保留=会话服务.retainInfo(会话标识)['getSnapshot']()#保留计数
        按源=保留.get('retainedBy')#按来源
        主视图=0#没有主视图
        if 按源 is not None and 按源.get('mainView') is not None:
            主视图=按源.get('mainView')#主视图计数
        if 主视图==0:
            return#没有留在主视图
        if 子会话标识==父会话:
            上下文.uiWorkspace.openSession(父会话)#打开 Lead
            return
        上下文.uiWorkspace.openSession({
            'parentSessionId':父会话,
            'childSessionId':子会话标识,
            'mode':'continuable',
        })#打开可继续的成员会话

    动作={'openTeammate':打开队友}#注入给面板的动作

    def 注入动作(*位置参数):
        '槽位按会话调用。打开动作不依赖会话键'
        return 动作

    def 登记动作():
        '等标题栏动作槽出现再登记'
        return 上下文.slots.register({
            'name':'conversation.session.header.actions',
            'id':'agent-team',
            'order':-20,
            'locale':命名空间,
            'inject':注入动作,
        },团队动作.团队动作)
    上下文.slots.inject('conversation.session.header.actions',登记动作)


inject=依赖
apply=应用
