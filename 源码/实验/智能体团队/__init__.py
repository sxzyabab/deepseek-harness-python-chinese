from functools import partial as 偏函数
import json,threading
from ...基础设施.js特性 import PromiseEX as 期约#恢复与拆除的异步结果
from ...依赖.schemastery import 正整数字段,字典字段
from ...依赖.工具 import 聚合错误
from ...模型后端.llm import 创建用户消息#转向 Lead 时的用户消息
from ...类型化远程调用.协议 import 远程服务
from .活动 import 团队活动
from .异常 import 团队错误,错误文案
from .日志 import 团队日志
from .生命周期 import 团队运行时生命周期,若已中止则抛出,合成中止
from .投影 import 团队投影定义
from .名册 import 团队名册,解析活跃成员
from .任务板 import 团队任务板
from .类型 import 团队标识,团队任务标识,团队消息标识
from . import (
    不变量,
    任务图,
    会话消息,
    客户端,
    持久化,
    校验,
)

__all__=[
    '名称','依赖','配置','应用','团队服务',
    '团队标识','团队任务标识','团队消息标识','团队错误',
]

名称='agent-team'
依赖=['agents','sessions','sessionPersistence','sessionProjections','subagents']

默认最大成员=16
默认最大任务=256
默认最大消息字节=65_536
默认拆除超时毫秒=5_000

配置=字典字段(字典结构={
    'maxMembers':正整数字段(默认值=默认最大成员),
    'maxTasks':正整数字段(默认值=默认最大任务),
    'maxMessageBytes':正整数字段(默认值=默认最大消息字节),
    'disposalTimeoutMs':正整数字段(默认值=默认拆除超时毫秒),
})

def 正限制(名,值):
    '校验一个正整数部署限制'
    if not isinstance(值,int) or isinstance(值,bool) or 值<1:
        raise 团队错误(名+' must be a positive safe integer','TEAM_INVALID_CONFIG')
    return int(值)

def _配置项(配置值,键,缺省):
    '从配置映射读键，缺席用缺省'
    if 配置值 is None or 键 not in 配置值:
        return 缺省
    return 配置值[键]

class 团队服务(远程服务):
    '以精确 live Lead Session 日志为后台的 Agent Teams 服务'
    def __init__(自身,上下文,配置值=None):
        '构造并接线活动、生命周期、日志、名册与任务板'
        super().__init__(上下文,'agentTeams')
        自身.config={
            'maxMembers':正限制('maxMembers',_配置项(配置值,'maxMembers',默认最大成员)),
            'maxTasks':正限制('maxTasks',_配置项(配置值,'maxTasks',默认最大任务)),
            'maxMessageBytes':正限制('maxMessageBytes',_配置项(配置值,'maxMessageBytes',默认最大消息字节)),
            'disposalTimeoutMs':正限制(
                'disposalTimeoutMs',
                _配置项(配置值,'disposalTimeoutMs',默认拆除超时毫秒),
            ),
        }
        自身.activity=团队活动()
        自身.lifecycle=团队运行时生命周期(自身.config['disposalTimeoutMs'])
        def 提交时(根):
            '通知等待者'
            自身.activity.通知(团队标识(根.id))
        自身.journal=团队日志(上下文,提交时)
        自身.roster=团队名册(上下文,自身.journal,自身.lifecycle,自身.config['maxMembers'])
        自身.tasks=团队任务板(自身.journal,自身.config['maxTasks'])
        自身._接线监听(上下文)

    def _接线监听(自身,上下文):
        '挂会话事件、恢复与运行时拆除'
        def 智能体已创建(载荷,*_其余):
            '调度恢复'
            自身._调度恢复(载荷['agent'])
        上下文.监听('agent/created',智能体已创建)
        def 状态变化(载荷,*_其余):
            '通知等待者'
            关系=自身.roster.试成员关系(载荷['agent'])
            if 关系 is not None:
                自身.activity.通知(关系['id'])
        上下文.监听('agent/status',状态变化)
        def 寿命效果():
            '注册投影并在拆除时拆除运行时'
            卸投影=上下文.根.sessionProjections.register(团队投影定义)
            def 卸除():
                '先拆除运行时再卸投影。返回期约'
                return 自身._拆除运行时().最终(卸投影)#拆除失败也卸投影
            return 卸除
        上下文.副作用(寿命效果,'agentTeams.runtimeLifecycle()')
        for 智能体 in 上下文.agents.list():
            自身._调度恢复(智能体)

    def membership(自身,智能体):
        '解析一个精确 live Agent 的 Team 角色'
        return 自身.roster.成员关系(智能体)

    def listMembers(自身,智能体):
        '列出一个 Team 成员可见的、经运行时充实的 roster'
        return 自身.roster.列表(自身.roster.成员关系(智能体))

    def spawnTeammate(自身,调用方,请求):
        '创建一个具名、可延续的 Team Lead 直接子代'
        return 自身.roster.创建(调用方,请求)

    def sendMessage(自身,调用方,请求):
        '把一条同伴消息转进目标收件箱。接受即返回，不等模型处理'
        if 自身.lifecycle.已拆除:#正在拆除
            raise 团队错误('Agent Teams service is disposing','TEAM_DISPOSED')#拒绝
        信号=合成中止(请求.get('signal'),自身.lifecycle.信号)#调用方与寿命
        合并=dict(请求)#不改调用方对象
        合并['signal']=信号#合成后的取消
        return 自身.lifecycle.跟踪(自身._发送已准入(调用方,合并))#计入拆除结算

    def createTask(自身,调用方,请求):
        '在 Team Lead 日志中创建一条无主 pending 任务'
        return 自身.tasks.创建(自身.roster.成员关系(调用方),请求)

    def getTask(自身,调用方,标识):
        '返回一条任务，含已删除 tombstone'
        return 自身.tasks.获取(自身.roster.成员关系(调用方),标识)

    def listTasks(自身,调用方):
        '按数字创建顺序列出当前未删除任务'
        return 自身.tasks.列表(自身.roster.成员关系(调用方))

    def updateTask(自身,调用方,请求):
        'compare-and-set 一次已授权的任务转换'
        return 自身.tasks.更新(调用方,自身.roster.成员关系(调用方),请求)

    def waitForChange(自身,调用方,超时毫秒,信号):
        '等待下一次 Team 域或成员状态变化'
        关系=自身.roster.成员关系(调用方)
        return 自身.activity.等待(关系['id'],超时毫秒,信号)

    def interrupt(自身,调用方,目标名):
        '中断一个 live teammate 轮次，不清理其 pending inbox'
        return 自身.roster.中断(调用方,目标名)

    def tryMembership(自身,智能体):
        '不抛错地解析调用方，供 scoped 工具安装与观察者使用'
        return 自身.roster.试成员关系(智能体)

    def _调度恢复(自身,智能体):
        '在发布栈回退后排队一次受控恢复'
        def 恢复失败(错误):#恢复失败
            '恢复失败只写警告；运行时已拆除时视为预期'
            if 自身.lifecycle.已拆除:
                return None
            自身.ctx.日志.警告(f'Agent Teams 对 "{智能体.id}" 的恢复失败：{错误文案(错误)}')
        def 恢复(启动值):#开始恢复
            '开始恢复；同步抛出也转成拒绝'
            return 自身._执行恢复(智能体)
        def 微任务():
            '执行恢复；线程只负责等发布栈回退，失败由期约链收纳'
            if 自身.lifecycle.已拆除:
                return
            启动=期约()#恢复在失败处理登记之后才开始
            启动.然后(恢复).捕获(恢复失败)
            启动.解决(None)#开始
        threading.Thread(target=微任务,daemon=True).start()

    def _执行恢复(自身,智能体):
        '对账这个智能体的 roster 供应。返回期约'
        return 自身.roster.恢复(智能体,自身.lifecycle.信号)#只对账名册

    def _发送已准入(自身,调用方,请求):
        '用 Lead 的权威投递，身份仍是实际发送者。返回期约，兑现值含 messageId'
        关系=自身.roster.成员关系(调用方)#发送者
        若已中止则抛出(请求.get('signal'))#准入前已取消
        根=关系['root']#Lead
        目标=解析活跃成员(根,自身.journal.状态(根),请求['target'])#按名字
        if 目标['id']==调用方.id:#不能发给自己
            raise 团队错误('a Team member cannot message itself','TEAM_SELF_MESSAGE')#拒绝
        内容=[{'type':'text','text':'Team message from '+关系['name']+':'}]#前缀
        for 块 in 请求['content']:#调用方的块
            内容.append(dict(块) if isinstance(块,dict) else 块)#拆开一份
        字节=len(json.dumps(内容,ensure_ascii=False,separators=(',',':')).encode('utf-8'))#UTF-8 字节
        if 字节>自身.config['maxMessageBytes']:#超限
            raise 团队错误('team message exceeds '+str(自身.config['maxMessageBytes'])+' bytes','TEAM_MESSAGE_TOO_LARGE')#拒绝
        来源={'kind':'agent-message','form':'relay','senderSessionId':调用方.id}#中继来源
        if 目标['id']==根.id:#发给 Lead
            输入=创建用户消息({'content':内容,'source':来源})#用户消息
            根.转向(输入)#转向当前回合
            自身.activity.通知(关系['id'])#唤醒等待
            已转向=期约()#与子路径同形
            已转向.解决({'messageId':输入['id']})#消息号
            return 已转向#已接受
        def 已投递(消息号):
            '子路径接受后通知等待者'
            自身.activity.通知(关系['id'])#唤醒
            return {'messageId':消息号}#结果
        return 自身.ctx.subagents.投递提示(根,目标['id'],内容,来源,请求.get('signal'),'steer').然后(已投递)#转向子收件箱

    def _拆除运行时(自身):
        '在服务拆除完成前停止 Team 拥有的 live 分支并释放等待者。返回期约，有失败则以聚合错误拒绝'
        自身.lifecycle.关闭()#先关准入
        自身.activity.关闭()#释放等待
        失败列表=[]#各步失败
        def 记录停止失败(错误):#停止失败
            '记录失败后继续下一组'
            失败列表.append(错误)#记下
        def 停止一组(所属根,所属子标识列表,前一组结果=None):#前一组停完后
            '停止一个 Lead 的队友，失败记入失败列表'
            return 自身.roster.停止队友(所属根,所属子标识列表).捕获(记录停止失败)#继续
        def 停止全部队友(结算值):#已准入工作结算完
            '逐个 Lead 依次停止其队友'
            停止链=期约()#链起点
            停止链.解决(None)#第一组立即开始
            for 根,子标识列表 in 自身.roster.按根分组活子().items():#逐根
                停止链=停止链.然后(偏函数(停止一组,根,子标识列表))#排后
            return 停止链#全部
        def 汇总失败(停止结算值):#全部停止完
            '有失败则以聚合错误拒绝'
            if len(失败列表)>0:#有失败
                raise 聚合错误(失败列表,'智能体团队运行时拆除失败')#汇总
        return 自身.lifecycle.结算(自身.lifecycle.待定(),失败列表).然后(停止全部队友).然后(汇总失败)#先等已准入，再停队友

def 应用(上下文,配置值=None):
    '构造并登记团队服务'
    团队服务(上下文,配置值)

name=名称
inject=依赖
apply=应用
Config=配置
