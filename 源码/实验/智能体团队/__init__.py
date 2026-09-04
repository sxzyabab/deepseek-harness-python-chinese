"""Agent Teams 服务门面：覆盖 roster、mailbox、task 与运行时生命周期所有者。

对齐上游 `agent-team/src/index.ts`。公开面仅中文名。
"""
import threading#微任务调度
from ...依赖.schemastery import 正整数字段,字典字段#配置字段
from ...依赖.工具 import 聚合错误#聚合错误
from ...内核.智能体循环.辅助 import 解开#等待
from ...typert.协议 import 远程服务,远程 as _远程#Remote 基类
from .活动 import 团队活动#变更等待
from .错误 import 团队错误,错误文案#领域错误
from .日志 import 团队日志#日志事务
from .生命周期 import 团队运行时生命周期#生命周期
from .邮箱 import 团队邮箱#邮箱
from .投影 import 团队投影定义#投影定义
from .名册 import 团队名册#成员表
from .任务板 import 团队任务板#任务板
from .类型 import 团队标识,团队任务标识,团队消息标识#身份

__all__=[#仅中文公开名
    '名称','注入','配置','应用','团队服务',
    '团队标识','团队任务标识','团队消息标识','团队错误',
]#公开面结束

名称='agent-team'#插件名
注入=['agents','sessions','sessionPersistence','sessionProjections','subagents']#依赖
name=名称#Cordis 名
inject=注入#Cordis 注入

默认最大成员=8#默认成员上限
默认最大任务=256#默认任务上限
默认最大待投=64#默认每成员待投上限
默认最大消息字节=65_536#默认单消息字节上限
默认处置超时毫秒=5_000#默认处置超时

配置=字典字段({#配置 schema
    'maxMembers':正整数字段(默认值=默认最大成员),#成员上限
    'maxTasks':正整数字段(默认值=默认最大任务),#任务上限
    'maxPendingMessagesPerMember':正整数字段(默认值=默认最大待投),#待投上限
    'maxMessageBytes':正整数字段(默认值=默认最大消息字节),#消息字节
    'disposalTimeoutMs':正整数字段(默认值=默认处置超时毫秒),#处置超时
})#配置结束
Config=配置#Cordis 配置

def 正限制(名,值):#正整数限制
    """校验一个正的安全整数部署限制。"""
    from ...内核.智能体循环.辅助 import 是否安全整数#安全整数
    if (not 是否安全整数(值)) or 值<1:#非法
        raise 团队错误(名+' must be a positive safe integer','TEAM_INVALID_CONFIG')#非法配置
    return int(值)#通过

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class 团队服务(远程服务):#团队服务
    """以精确 live Lead Session 日志为后台的 Agent Teams 服务。"""
    inject=注入#类级注入
    注入=inject#中文别名
    Config=配置#配置模式

    def __init__(自身,上下文,配置值=None):#构造并接线
        """构造并接线活动、生命周期、日志、名册、邮箱与任务板。"""
        super().__init__(上下文,'agentTeams')#注册 Remote 名
        if 配置值 is None:#缺省
            配置值={}#空
        自身.config={#组装配置
            'maxMembers':正限制('maxMembers',取字段(配置值,'maxMembers',默认最大成员)),#成员上限
            'maxTasks':正限制('maxTasks',取字段(配置值,'maxTasks',默认最大任务)),#任务上限
            'maxPendingMessagesPerMember':正限制(#待投上限
                'maxPendingMessagesPerMember',#名
                取字段(配置值,'maxPendingMessagesPerMember',默认最大待投),#值
            ),#待投结束
            'maxMessageBytes':正限制('maxMessageBytes',取字段(配置值,'maxMessageBytes',默认最大消息字节)),#消息字节
            'disposalTimeoutMs':正限制(#处置超时
                'disposalTimeoutMs',#名
                取字段(配置值,'disposalTimeoutMs',默认处置超时毫秒),#值
            ),#超时结束
        }#配置结束
        自身.activity=团队活动()#活动等待器
        自身.lifecycle=团队运行时生命周期(自身.config['disposalTimeoutMs'])#生命周期
        自身.journal=团队日志(上下文,lambda 根:自身.activity.通知(团队标识(根.id)))#日志提交通知
        自身.roster=团队名册(上下文,自身.journal,自身.lifecycle,自身.config['maxMembers'])#roster
        自身.mailbox=团队邮箱(#mailbox
            上下文,自身.journal,自身.roster,自身.lifecycle,#依赖
            自身.config['maxPendingMessagesPerMember'],自身.config['maxMessageBytes'],#限制
        )#mailbox 结束
        自身.tasks=团队任务板(自身.journal,自身.config['maxTasks'])#任务板
        自身._接线监听(上下文)#监听与 effect

    def _接线监听(自身,上下文):#接线监听
        """挂会话事件、恢复与运行时处置。"""
        def 观察事件(会话,事件,*_其余):#观察投递确认
            """观察会话事件。"""
            自身.mailbox.观察会话事件(会话,事件)#委托邮箱
        上下文.on('session/event',观察事件)#观察投递确认
        def 会话启动(载荷,*_其余):#会话启动恢复
            """调度恢复。"""
            自身._调度恢复(取字段(载荷,'agent'))#恢复
        上下文.on('agent/session-start',会话启动)#会话启动恢复
        def 状态变化(载荷,*_其余):#状态变化
            """通知等待者。"""
            关系=自身.roster.试成员关系(取字段(载荷,'agent'))#试解析成员
            if 关系 is not None:#是成员
                自身.activity.通知(关系['id'])#通知等待者
        上下文.on('agent/status',状态变化)#status 监听
        def 寿命效果():#生命周期 effect
            """注册投影并在拆除时处置运行时。"""
            卸投影=上下文.root.sessionProjections.register(团队投影定义)#注册投影
            def 卸除():#卸除
                """先处置运行时再卸投影。"""
                try:#先处置
                    自身._处置运行时()#处置
                finally:#再卸投影
                    卸投影()#卸投影
            return 卸除#卸除器
        上下文.effect(寿命效果,'agentTeams.runtimeLifecycle()')#effect 名
        for 智能体 in 上下文.agents.list():#已有 agent 补恢复
            自身._调度恢复(智能体)#调度

    def membership(自身,智能体):#解析成员关系
        """解析一个精确 live Agent 的 Team 角色。"""
        return 自身.roster.成员关系(智能体)#委托 roster

    def listMembers(自身,智能体):#列成员
        """列出一个 Team 成员可见的、经运行时充实的 roster。"""
        return 自身.roster.列表(自身.roster.成员关系(智能体))#按成员关系列

    def spawnTeammate(自身,调用方,请求):#创建 teammate
        """创建一个具名、可延续的 Team Lead 直接子代。"""
        return 自身.roster.创建(调用方,请求)#委托 roster

    def sendMessage(自身,调用方,请求):#发消息
        """排队一条持久 peer 消息，再尝试即时投递。"""
        return 自身.mailbox.发送(调用方,请求)#委托 mailbox

    def createTask(自身,调用方,请求):#建任务
        """在 Team Lead 日志中创建一条无主 pending 任务。"""
        return 自身.tasks.创建(自身.roster.成员关系(调用方),请求)#委托任务板

    def getTask(自身,调用方,标识):#取任务
        """返回一条任务，含已删除 tombstone。"""
        return 自身.tasks.获取(自身.roster.成员关系(调用方),标识)#委托任务板

    def listTasks(自身,调用方):#列任务
        """按数字创建顺序列出当前未删除任务。"""
        return 自身.tasks.列表(自身.roster.成员关系(调用方))#委托任务板

    def updateTask(自身,调用方,请求):#更新任务
        """compare-and-set 一次已授权的任务转换。"""
        return 自身.tasks.更新(调用方,自身.roster.成员关系(调用方),请求)#委托任务板

    def waitForChange(自身,调用方,超时毫秒,信号):#等待变化
        """等待下一次 Team 域或成员状态变化。"""
        关系=自身.roster.成员关系(调用方)#解析成员
        return 自身.activity.等待(关系['id'],超时毫秒,信号)#委托活动

    def interrupt(自身,调用方,目标名):#中断 teammate
        """中断一个 live teammate 轮次，不清理其 pending inbox。"""
        return 自身.roster.中断(调用方,目标名)#委托 roster

    def tryMembership(自身,智能体):#试解析成员
        """不抛错地解析调用方，供 scoped 工具安装与观察者使用。"""
        return 自身.roster.试成员关系(智能体)#委托 roster

    @_远程('view')
    def remoteView(自身,智能体):#Remote 总览
        """经生成的 Remote API 读取当前 roster 与未删除任务板。"""
        return {'members':自身.listMembers(智能体),'tasks':自身.listTasks(智能体)}#总览

    @_远程('createTask')
    def remoteCreateTask(自身,智能体,请求):#Remote 建任务
        """经生成的 Remote API 创建一条共享任务。"""
        return 自身._任务变更结果(自身.createTask(智能体,请求))#包装领域结果

    @_远程('updateTask')
    def remoteUpdateTask(自身,智能体,请求):#Remote 更新任务
        """应用一次任务变更，并把 Team 拒绝保留为业务结果。"""
        return 自身._任务变更结果(自身.updateTask(智能体,请求))#包装领域结果

    def _任务变更结果(自身,操作):#包装变更
        """保留 Team 任务拒绝，同时让意外失败仍拒绝 Remote 调用。"""
        try:#试执行
            return {'ok':True,'value':解开(操作) if hasattr(操作,'wait') or hasattr(操作,'等待') else 操作}#成功
        except 团队错误 as 错误:#领域拒绝
            码='team-task-conflict' if 错误.code=='TEAM_TASK_STALE_REVISION' else 'team-rejected'#冲突区分
            return {'ok':False,'error':{'code':码,'message':错误.message}}#拒绝
        except Exception:#非领域
            raise#上抛

    def _调度恢复(自身,智能体):#调度恢复
        """在发布栈回退后排队一次受控恢复。"""
        def 微任务():#微任务
            """执行恢复。"""
            if 自身.lifecycle.已处置:#已处置则跳过
                return#跳过
            try:#恢复
                自身._执行恢复(智能体)#恢复
            except Exception as 错误:#恢复失败
                if 自身.lifecycle.已处置:#处置中静默
                    return#静默
                自身.ctx.logger.warn('Agent Teams recovery for "'+str(智能体.id)+'" failed: '+错误文案(错误))#记警告
        threading.Thread(target=微任务,daemon=True).start()#微任务线程

    def _执行恢复(自身,智能体):#执行恢复
        """先对账 roster provisioning，再重试该成员的 pending mailbox。"""
        自身.roster.恢复(智能体,自身.lifecycle.信号)#roster 恢复
        自身.mailbox.恢复(智能体,自身.lifecycle.信号)#mailbox 恢复

    def _处置运行时(自身):#处置运行时
        """在服务处置完成前停止 Team 拥有的 live 分支并释放每一个等待者。"""
        自身.lifecycle.关闭()#关闭准入
        自身.activity.关闭()#释放等待者
        失败们=[]#收集失败
        自身.lifecycle.结算(自身.roster.待创建们(),失败们)#结算创建
        自身.lifecycle.结算(自身.mailbox.待投递们(),失败们)#结算投递
        for 根,子标识们 in 自身.roster.按根分组活子().items():#按根停子
            try:#停 teammate
                自身.roster.停止队友们(根,子标识们)#停止
            except Exception as 错误:#收集
                失败们.append(错误)#收集
        if len(失败们)>0:#汇总失败
            raise 聚合错误(失败们,'Agent Teams runtime disposal failed')#汇总

def 应用(上下文,配置值=None):#安装团队服务
    """构造并登记团队服务。"""
    团队服务(上下文,配置值)#构造并登记

apply=应用#Cordis 插件入口
