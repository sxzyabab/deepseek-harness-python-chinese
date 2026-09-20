import threading
from ...依赖.schemastery import 正整数字段,字典字段
from ...依赖.工具 import 聚合错误
from ...typert.协议 import 远程服务,远程 as _远程
from .活动 import 团队活动
from .错误 import 团队错误,错误文案
from .日志 import 团队日志
from .生命周期 import 团队运行时生命周期
from .邮箱 import 团队邮箱
from .投影 import 团队投影定义
from .名册 import 团队名册
from .任务板 import 团队任务板
from .类型 import 团队标识,团队任务标识,团队消息标识

__all__=[
    '名称','依赖','配置','应用','团队服务',
    '团队标识','团队任务标识','团队消息标识','团队错误',
]

名称='agent-team'
依赖=['agents','sessions','sessionPersistence','sessionProjections','subagents']

默认最大成员=8
默认最大任务=256
默认最大待投=64
默认最大消息字节=65_536
默认拆除超时毫秒=5_000

配置=字典字段(字典结构={
    'maxMembers':正整数字段(默认值=默认最大成员),
    'maxTasks':正整数字段(默认值=默认最大任务),
    'maxPendingMessagesPerMember':正整数字段(默认值=默认最大待投),
    'maxMessageBytes':正整数字段(默认值=默认最大消息字节),
    'disposalTimeoutMs':正整数字段(默认值=默认拆除超时毫秒),
})

def 正限制(名,值):
    """校验一个正整数部署限制。"""
    if not isinstance(值,int) or isinstance(值,bool) or 值<1:
        raise 团队错误(名+' must be a positive safe integer','TEAM_INVALID_CONFIG')
    return int(值)

def _配置项(配置值,键,缺省):
    """从配置映射读键，缺席用缺省。"""
    if 配置值 is None or 键 not in 配置值:
        return 缺省
    return 配置值[键]

class 团队服务(远程服务):
    """以精确 live Lead Session 日志为后台的 Agent Teams 服务。"""
    def __init__(自身,上下文,配置值=None):
        """构造并接线活动、生命周期、日志、名册、邮箱与任务板。"""
        super().__init__(上下文,'agentTeams')
        自身.config={
            'maxMembers':正限制('maxMembers',_配置项(配置值,'maxMembers',默认最大成员)),
            'maxTasks':正限制('maxTasks',_配置项(配置值,'maxTasks',默认最大任务)),
            'maxPendingMessagesPerMember':正限制(
                'maxPendingMessagesPerMember',
                _配置项(配置值,'maxPendingMessagesPerMember',默认最大待投),
            ),
            'maxMessageBytes':正限制('maxMessageBytes',_配置项(配置值,'maxMessageBytes',默认最大消息字节)),
            'disposalTimeoutMs':正限制(
                'disposalTimeoutMs',
                _配置项(配置值,'disposalTimeoutMs',默认拆除超时毫秒),
            ),
        }
        自身.activity=团队活动()
        自身.lifecycle=团队运行时生命周期(自身.config['disposalTimeoutMs'])
        def 提交时(根):
            """通知等待者。"""
            自身.activity.通知(团队标识(根.id))
        自身.journal=团队日志(上下文,提交时)
        自身.roster=团队名册(上下文,自身.journal,自身.lifecycle,自身.config['maxMembers'])
        自身.mailbox=团队邮箱(
            上下文,自身.journal,自身.roster,自身.lifecycle,
            自身.config['maxPendingMessagesPerMember'],自身.config['maxMessageBytes'],
        )
        自身.tasks=团队任务板(自身.journal,自身.config['maxTasks'])
        自身._接线监听(上下文)

    def _接线监听(自身,上下文):
        """挂会话事件、恢复与运行时拆除。"""
        def 观察事件(会话,事件,*_其余):
            """观察会话事件。"""
            自身.mailbox.观察会话事件(会话,事件)
        上下文.监听('session/event',观察事件)
        def 会话启动(载荷,*_其余):
            """调度恢复。"""
            自身._调度恢复(载荷['agent'])
        上下文.监听('agent/session-start',会话启动)
        def 状态变化(载荷,*_其余):
            """通知等待者。"""
            关系=自身.roster.试成员关系(载荷['agent'])
            if 关系 is not None:
                自身.activity.通知(关系['id'])
        上下文.监听('agent/status',状态变化)
        def 寿命效果():
            """注册投影并在拆除时拆除运行时。"""
            卸投影=上下文.根.sessionProjections.register(团队投影定义)
            def 卸除():
                """先拆除运行时再卸投影。"""
                try:
                    自身._拆除运行时()
                finally:
                    卸投影()
            return 卸除
        上下文.副作用(寿命效果,'agentTeams.runtimeLifecycle()')
        for 智能体 in 上下文.agents.list():
            自身._调度恢复(智能体)

    def membership(自身,智能体):
        """解析一个精确 live Agent 的 Team 角色。"""
        return 自身.roster.成员关系(智能体)

    def listMembers(自身,智能体):
        """列出一个 Team 成员可见的、经运行时充实的 roster。"""
        return 自身.roster.列表(自身.roster.成员关系(智能体))

    def spawnTeammate(自身,调用方,请求):
        """创建一个具名、可延续的 Team Lead 直接子代。"""
        return 自身.roster.创建(调用方,请求)

    def sendMessage(自身,调用方,请求):
        """排队一条持久 peer 消息，再尝试即时投递。"""
        return 自身.mailbox.发送(调用方,请求)

    def createTask(自身,调用方,请求):
        """在 Team Lead 日志中创建一条无主 pending 任务。"""
        return 自身.tasks.创建(自身.roster.成员关系(调用方),请求)

    def getTask(自身,调用方,标识):
        """返回一条任务，含已删除 tombstone。"""
        return 自身.tasks.获取(自身.roster.成员关系(调用方),标识)

    def listTasks(自身,调用方):
        """按数字创建顺序列出当前未删除任务。"""
        return 自身.tasks.列表(自身.roster.成员关系(调用方))

    def updateTask(自身,调用方,请求):
        """compare-and-set 一次已授权的任务转换。"""
        return 自身.tasks.更新(调用方,自身.roster.成员关系(调用方),请求)

    def waitForChange(自身,调用方,超时毫秒,信号):
        """等待下一次 Team 域或成员状态变化。"""
        关系=自身.roster.成员关系(调用方)
        return 自身.activity.等待(关系['id'],超时毫秒,信号)

    def interrupt(自身,调用方,目标名):
        """中断一个 live teammate 轮次，不清理其 pending inbox。"""
        return 自身.roster.中断(调用方,目标名)

    def tryMembership(自身,智能体):
        """不抛错地解析调用方，供 scoped 工具安装与观察者使用。"""
        return 自身.roster.试成员关系(智能体)

    @_远程('view')
    def remoteView(自身,智能体):
        """经生成的 Remote API 读取当前 roster 与未删除任务板。"""
        return {'members':自身.listMembers(智能体),'tasks':自身.listTasks(智能体)}

    @_远程('createTask')
    def remoteCreateTask(自身,智能体,请求):
        """经生成的 Remote API 创建一条共享任务。"""
        return 自身._任务变更结果(自身.createTask(智能体,请求))

    @_远程('updateTask')
    def remoteUpdateTask(自身,智能体,请求):
        """应用一次任务变更，并把 Team 拒绝保留为业务结果。"""
        return 自身._任务变更结果(自身.updateTask(智能体,请求))

    def _任务变更结果(自身,操作):
        """保留 Team 任务拒绝，同时让意外失败仍拒绝 Remote 调用。"""
        try:
            return {'ok':True,'value':操作}
        except 团队错误 as 错误:
            码='team-task-conflict' if 错误.code=='TEAM_TASK_STALE_REVISION' else 'team-rejected'
            return {'ok':False,'error':{'code':码,'message':错误.message}}

    def _调度恢复(自身,智能体):
        """在发布栈回退后排队一次受控恢复。"""
        def 微任务():
            """执行恢复。"""
            if 自身.lifecycle.已拆除:
                return
            try:
                自身._执行恢复(智能体)
            except Exception as 错误:#roster/mailbox 恢复可能抛团队错误/持久化错误，契约未定所以收不窄
                if 自身.lifecycle.已拆除:
                    return
                自身.ctx.日志.警告('Agent Teams recovery for "'+str(智能体.id)+'" failed: '+错误文案(错误))
        threading.Thread(target=微任务,daemon=True).start()

    def _执行恢复(自身,智能体):
        """先对账 roster provisioning，再重试该成员的 pending mailbox。"""
        自身.roster.恢复(智能体,自身.lifecycle.信号)
        自身.mailbox.恢复(智能体,自身.lifecycle.信号)

    def _拆除运行时(自身):
        """在服务拆除完成前停止 Team 拥有的 live 分支并拆除每一个等待者。"""
        自身.lifecycle.关闭()
        自身.activity.关闭()
        失败列表=[]
        自身.lifecycle.结算(自身.roster.列出待创建(),失败列表)
        自身.lifecycle.结算(自身.mailbox.列出待投递(),失败列表)
        for 根,子标识列表 in 自身.roster.按根分组活子().items():
            try:
                自身.roster.停止队友(根,子标识列表)
            except Exception as 错误:#停止队友可能抛团队错误/会话错误，契约未定所以收不窄
                失败列表.append(错误)
        if len(失败列表)>0:
            raise 聚合错误(失败列表,'智能体团队运行时拆除失败')

def 应用(上下文,配置值=None):
    """构造并登记团队服务。"""
    团队服务(上下文,配置值)

name=名称
inject=依赖
apply=应用
Config=配置
