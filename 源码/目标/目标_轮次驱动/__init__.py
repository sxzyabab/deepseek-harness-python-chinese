"""同会话目标轮次驱动器：经公开智能体、会话与目标服务自动续跑。"""
import threading#串行驱动线程
from ...依赖 import cordis#外部依赖胶水
光纤状态=cordis.纤程状态#纤程生命周期
from ...内核.智能体 import 下一步#收件箱下一步目标
from ...模型后端.llm import 创建用户消息#构造轮次提示
from .提示 import 渲染目标轮次提示#轮次指令

__all__=('名称','注入','应用','默认','渲染目标轮次提示')#仅中文公开名

名称='goal-round-driver'#插件名
注入=['agents','goals','sessions']#依赖

def 是否目标轮次来源(来源):#是否自动正数轮次
    """来源是否标识一次自动、正数编号的目标轮次。"""
    return 来源['kind']=='goal' and 来源['round']>0#目标且正数轮

def 同一轮次(来源,身份):#来源对上预订
    """比较来源与一份已预订身份。"""
    return 来源['goalId']==身份['goalId'] and 来源['revision']==身份['revision'] and 来源['round']==身份['round']#三键对齐

def 同一排队(内容,来源,尝试):#完整排队记录
    """比较排队内容与驱动器预订。"""
    return 是否目标轮次来源(来源) and 同一轮次(来源,尝试) and 内容==尝试['content']#来源加内容

def 目标引用(目标):#视图 → 引用
    """视图的精确当前引用。"""
    return {'id':目标['id'],'revision':目标['revision']}#比较交换身份

def 渲染抛出(值):#日志可读
    """把意外值收成人类可读日志。"""
    if isinstance(值,BaseException):#异常
        return str(值)#消息
    return str(值)#其它

def 应用(上下文对象):#安装自动续跑
    """安装同会话自动续跑及其竞态围栏。"""
    状态表={}#智能体 → 驱动状态

    def 状态于(智能体):#精确当前生命周期
        """为精确当前在线智能体创建或取出状态。"""
        已有=状态表.get(智能体)#已有
        if 已有 is not None:#命中
            return 已有#复用
        状态={#新状态
            'agent':智能体,#主体
            'attempt':None,#预订
            'competingQueued':False,#有竞争提示
            'needsCheckpoint':False,#需要落盘
            'requested':False,#请求再跑
            'run':None,#驱动线程
            'stopping':False,#正在拆除
        }#结束状态
        状态表[智能体]=状态#记下
        return 状态#新状态

    def 当前目标(状态):#只在精确实例仍在线时读
        """精确 Agent 仍在线时读当前目标。"""
        if 上下文对象.agents.获取(状态['agent'].id) is not 状态['agent']:#已换实例
            return None#无
        return 上下文对象.goals.获取(状态['agent'])#当前视图

    def 可以驱动(状态):#静止且无竞争
        """本生命周期是否静止且无竞争提示。"""
        return (上下文对象.纤程.state==光纤状态.已激活
            and not 状态['stopping']
            and 上下文对象.agents.获取(状态['agent'].id) is 状态['agent']
            and 状态['agent'].状态=='idle'
            and not 状态['competingQueued'])#全部成立

    def 检查点后可以(状态):#检查点后再核
        """再核检查点等待期间可能变化的条件。"""
        return 可以驱动(状态) and not 状态['needsCheckpoint']#仍可驱动

    def 解除武装(状态):#去掉自动权限
        """去掉自动权限，保留持久阶段。"""
        try:#解除可能失败
            目标=当前目标(状态)#当前
            if 目标 is not None and 目标['activation']=='armed':#仍武装
                上下文对象.goals.解除武装(状态['agent'])#解除
        except Exception as 错误:#失败只记日志
            上下文对象.日志.警告('goal-round-driver: could not disarm agent "'+str(状态['agent'].id)+'": '+渲染抛出(错误))#警告

    def 恢复其它已领取(智能体,消息列表,消息身份):#丢掉本轮时保留其它
        """本驱动只丢掉自己的轮次时，保留其它已领取步骤上下文。"""
        保留=[]#其它消息
        for 消息 in 消息列表:#逐条
            if 消息['id']==消息身份:#本轮
                continue#丢掉
            来源=消息['source']#来源
            if 来源['kind']=='goal' and 来源['round']==0:#轮次零
                continue#丢掉
            保留.append(消息)#留下
        for 消息 in reversed(保留):#逆序前置
            已在=False#是否已在收件箱
            for 候选 in 智能体.inbox.下一步队列:#下一步
                if 候选['id']==消息['id']:#已在
                    已在=True#记下
                    break#停
            if not 已在:#再看下一轮
                for 候选 in 智能体.inbox.下一轮队列:#下一轮
                    if 候选['id']==消息['id']:#已在
                        已在=True#记下
                        break#停
            if 已在:#已在
                continue#跳过
            智能体.inbox.前置(下一步,消息)#前置回下一步

    def 驱动(状态):#处理已接纳工作再预订下一轮
        """在静止时处理已接纳工作，然后最多预订一轮。"""
        智能体=状态['agent']#主体
        if not 可以驱动(状态):#未就绪
            return#结束
        if 状态['needsCheckpoint']:#需要落盘
            状态['needsCheckpoint']=False#清掉
            try:#落盘
                上下文对象.sessions.flush(智能体.session)#刷会话
            except Exception as 错误:#失败
                上下文对象.日志.警告('goal-round-driver: durability checkpoint failed for agent "'+str(智能体.id)+'": '+渲染抛出(错误))#警告
                解除武装(状态)#解除
                return#结束
            if not 检查点后可以(状态):#等待期间有变
                return#结束
        尝试=状态['attempt']#预订
        if 尝试 is not None:#有已接纳工作
            状态['attempt']=None#清掉
            状态['needsCheckpoint']=True#下次先落盘
            状态['requested']=True#再跑
            return#结束
        目标=当前目标(状态)#当前
        if 目标 is None or 目标['phase']!='active' or 目标['activation']!='armed':#不可续
            return#结束
        if 目标['roundsStarted']>=目标['maxGoalRounds']:#预算耗尽
            上下文对象.goals.阻塞(智能体,目标引用(目标),{#阻塞
                'code':'round-limit',#码
                'message':'Goal reached its configured limit of '+str(目标['maxGoalRounds'])+' rounds.',#说明
            })#结束阻塞
            return#结束
        轮次=目标['roundsStarted']+1#下一轮
        内容=渲染目标轮次提示(目标,轮次)#提示
        消息=创建用户消息({#用户消息
            'content':内容,#内容
            'source':{'kind':'goal','goalId':目标['id'],'revision':目标['revision'],'round':轮次},#来源
        })#结束消息
        预订={#预订记录
            'goalId':目标['id'],#目标
            'revision':目标['revision'],#修订
            'round':轮次,#轮次
            'messageId':消息['id'],#消息
            'content':内容,#内容
            'phase':'queued',#已排队
            'cancelled':False,#未取消
            'stale':False,#未过期
        }#结束预订
        状态['attempt']=预订#记下
        try:#入队
            智能体.后续(消息)#下一轮并唤醒
        except Exception as 错误:#入队失败
            状态['attempt']=None#清掉
            上下文对象.日志.警告('goal-round-driver: could not queue round '+str(轮次)+' for agent "'+str(智能体.id)+'": '+渲染抛出(错误))#警告
            最新=当前目标(状态)#再读
            if (最新 is not None and 最新['id']==目标['id'] and 最新['revision']==目标['revision']
                and 最新['phase']=='active' and 最新['activation']=='armed'):#仍是这一份
                上下文对象.goals.阻塞(智能体,目标引用(最新),{#阻塞
                    'code':'queue-failed',#码
                    'message':'Could not queue goal round '+str(轮次)+': '+渲染抛出(错误),#说明
                })#结束阻塞

    def 请求驱动(状态):#合并到一条智能体本地串行驱动
        """把触发合并到一条智能体本地串行驱动。"""
        if 状态['stopping']:#拆除中
            return#结束
        状态['requested']=True#请求
        if 状态['run'] is not None:#已有线程
            return#结束
        def 跑():#串行循环
            """在隐藏发起方的边界内串行驱动。"""
            try:#启动可能失败
                def 循环():#请求循环
                    """消化 requested 闩。"""
                    while 状态['requested'] and not 状态['stopping']:#还有请求
                        状态['requested']=False#清掉
                        try:#一次驱动
                            驱动(状态)#驱动
                        except Exception as 错误:#失败
                            上下文对象.日志.警告('goal-round-driver: driver failed for agent "'+str(状态['agent'].id)+'": '+渲染抛出(错误))#警告
                            解除武装(状态)#解除
                上下文对象.agents.无发起方(循环)#隐藏发起方
            except Exception as 错误:#启动失败
                上下文对象.日志.警告('goal-round-driver: could not start driver for agent "'+str(状态['agent'].id)+'": '+渲染抛出(错误))#警告
                解除武装(状态)#解除
            finally:#退役
                状态['run']=None#清掉线程
                if 状态['requested'] and not 状态['stopping']:#还有请求
                    请求驱动(状态)#再开
        工作=threading.Thread(target=跑)#驱动线程
        工作.daemon=True#不挡住退出
        状态['run']=工作#记下
        工作.start()#启动

    def 安装():#监听与拆除
        """登记监听，拆除时先停驱动再摘监听。"""
        def 智能体错误(载荷,*位置参数):#错误则解除
            """错误则解除武装。"""
            解除武装(状态于(载荷['agent']))#解除
        上下文对象.监听('agent/error',智能体错误)#错误
        def 智能体已拆除(载荷,*位置参数):#生命周期结束
            """生命周期结束则丢掉状态。"""
            状态表.pop(载荷['agent'],None)#删除
        上下文对象.监听('agent/disposed',智能体已拆除)#拆除
        def 智能体已创建(载荷,*位置参数):#新生命周期
            """新生命周期不继承预订。"""
            状态=状态于(载荷['agent'])#状态
            状态['attempt']=None#清预订
            状态['competingQueued']=False#无竞争
            状态['needsCheckpoint']=False#无检查点
        上下文对象.监听('agent/created',智能体已创建)#创建
        def 智能体状态(载荷,*位置参数):#空闲边
            """空闲时处理取消预订并请求驱动。"""
            智能体=载荷['agent']#主体
            状态名=载荷['status']#状态
            状态=状态于(智能体)#驱动状态
            if 状态名!='idle':#非空闲
                return#结束
            状态['competingQueued']=False#空闲清竞争
            尝试=状态['attempt']#预订
            目标=当前目标(状态)#当前
            if (尝试 is not None
                and (尝试['phase']=='queued' or 尝试['phase']=='claimed' or 尝试['cancelled'])
                and 目标 is not None and 目标['phase']=='active' and 目标['activation']=='armed'
                and 尝试['goalId']==目标['id'] and 尝试['revision']==目标['revision']):#取消打到本修订
                状态['attempt']=None#清掉
                try:#暂停
                    上下文对象.goals.暂停(智能体,目标引用(目标))#暂停
                except Exception as 错误:#失败
                    上下文对象.日志.警告('goal-round-driver: could not pause cancelled goal for agent "'+str(智能体.id)+'": '+渲染抛出(错误))#警告
                    解除武装(状态)#解除
            请求驱动(状态)#再跑
        上下文对象.监听('agent/status',智能体状态)#状态
        def 目标已变更(载荷,*位置参数):#变更边
            """变更后先检查点；宿主暂停则取消在跑轮次。"""
            智能体=载荷['agent']#主体
            变更=载荷['change']#变更
            状态=状态于(智能体)#驱动状态
            状态['needsCheckpoint']=True#需要落盘
            if 变更['operation']=='pause' and 智能体.状态=='running' and 上下文对象.agents.当前发起方() is not 智能体:#宿主暂停
                智能体.取消({'kind':'user'},{'keepInbox':True})#取消本轮
            请求驱动(状态)#再跑
        上下文对象.监听('goal/changed',目标已变更)#目标变更
        def 收件箱插入(载荷,*位置参数):#插入边
            """非本预订的下一轮提示视为竞争。"""
            智能体=载荷['agent']#主体
            消息=载荷['message']#消息
            在下一轮=False#是否下一轮
            for 候选 in 智能体.inbox.下一轮队列:#下一轮
                if 候选['id']==消息['id']:#命中
                    在下一轮=True#记下
                    break#停
            if not 在下一轮:#不是下一轮
                return#结束
            状态=状态于(智能体)#驱动状态
            尝试=状态['attempt']#预订
            if 尝试 is not None and 同一排队(消息['content'],消息['source'],尝试):#本预订
                return#结束
            状态['competingQueued']=True#竞争
            if 尝试 is not None and 尝试['phase']=='queued':#排队中
                尝试['stale']=True#过期
        上下文对象.监听('agent/inbox/inserted',收件箱插入)#插入
        def 收件箱领取(载荷,*位置参数):#领取边
            """本预订进入领取。"""
            智能体=载荷['agent']#主体
            消息=载荷['message']#消息
            状态=状态于(智能体)#驱动状态
            尝试=状态['attempt']#预订
            if 尝试 is not None and 同一排队(消息['content'],消息['source'],尝试):#本预订
                尝试['phase']='claimed'#领取
        上下文对象.监听('agent/inbox/claimed',收件箱领取)#领取
        def 收件箱丢弃(载荷,*位置参数):#丢弃边
            """本预订被丢弃。"""
            智能体=载荷['agent']#主体
            消息=载荷['message']#消息
            状态=状态于(智能体)#驱动状态
            尝试=状态['attempt']#预订
            if 尝试 is not None and 同一排队(消息['content'],消息['source'],尝试):#本预订
                尝试['cancelled']=True#取消
        上下文对象.监听('agent/inbox/discarded',收件箱丢弃)#丢弃
        def 会话事件(会话,事件,*位置参数):#日志边
            """接纳与中止边。"""
            智能体=上下文对象.agents.获取(会话.id)#按会话
            if 智能体 is None or 智能体.session is not 会话:#不是这份
                return#结束
            状态=状态于(智能体)#驱动状态
            类型=事件['type']#类型
            if 类型=='user/message':#用户消息
                if 状态['attempt'] is not None and 事件['data']['id']==状态['attempt']['messageId']:#本预订
                    状态['attempt']['phase']='admitted'#已接纳
                return#结束
            if 类型=='turn/end':#轮次结束
                原因=事件['data']['reason']#原因
                if 原因['kind']=='max-tokens':#打到上限
                    解除武装(状态)#解除
                    return#结束
                if 原因['kind']!='aborted':#非中止
                    return#结束
                尝试=状态['attempt']#预订
                if 尝试 is not None and (尝试['phase']=='claimed' or 尝试['phase']=='admitted'):#已领取或已接纳
                    尝试['cancelled']=True#取消
                else:#其它
                    解除武装(状态)#解除
                return#结束
        上下文对象.监听('session/event',会话事件)#日志
        def 预订仍有效(状态,内容,来源):#失败即关
            """排队提示仍拥有精确在线修订才有效。"""
            尝试=状态['attempt']#预订
            目标=当前目标(状态)#当前
            return (上下文对象.纤程.state==光纤状态.已激活
                and not 状态['stopping'] and 尝试 is not None and 尝试['phase']=='claimed'
                and not 尝试['stale'] and 同一排队(内容,来源,尝试)
                and 目标 is not None and 目标['id']==来源['goalId'] and 目标['revision']==来源['revision']
                and 目标['phase']=='active' and 目标['activation']=='armed'
                and 来源['round']==目标['roundsStarted']+1)#全部成立
        def 预步骤(载荷,下一):#步骤围栏
            """失败即关：排队提示必须仍拥有精确在线修订。"""
            智能体=载荷['agent']#主体
            消息列表=载荷['messages']#提议消息
            信号=载荷['signal'] if 'signal' in 载荷 else None#取消
            提交=None#目标轮次消息
            for 消息 in 消息列表:#逐条
                if 是否目标轮次来源(消息['source']):#命中
                    提交=消息#记下
                    break#停
            if 提交 is None:#没有目标轮次
                return 下一()#放行
            内容=提交['content']#内容
            来源=提交['source']#来源
            状态=状态于(智能体)#驱动状态
            有效=False#默认无效
            try:#检查
                有效=预订仍有效(状态,内容,来源)#核预订
            except Exception as 错误:#检查失败
                上下文对象.日志.警告('goal-round-driver: pre-step check failed for agent "'+str(智能体.id)+'": '+渲染抛出(错误))#警告
                解除武装(状态)#解除
            if not 有效:#无效
                尝试=状态['attempt']#预订
                if 尝试 is not None and 同一轮次(来源,尝试):#同一轮
                    尝试['stale']=True#过期
                    状态['attempt']=None#清掉
                恢复其它已领取(智能体,消息列表,提交['id'])#保留其它
                请求驱动(状态)#再跑
                return {'kind':'reject'}#拒绝
            try:#下游钩子
                决定=下一()#下游
            except Exception as 错误:#下游抛错
                if 信号 is not None and 信号.is_set():#调用方中止
                    raise 错误#原样
                状态['attempt']=None#清预订
                请求驱动(状态)#再跑
                raise 错误#再抛
            if 信号 is not None and 信号.is_set():#中止
                if 决定['kind']=='enter':#已进入
                    恢复其它已领取(智能体,决定['messages'],提交['id'])#保留其它
                return 决定#原决定
            if 决定['kind']=='reject':#下游拒绝
                状态['attempt']=None#清掉
                目标=当前目标(状态)#当前
                if (目标 is not None and 目标['id']==来源['goalId'] and 目标['revision']==来源['revision']
                    and 目标['phase']=='active' and 目标['activation']=='armed'):#仍是这一份
                    上下文对象.goals.阻塞(智能体,目标引用(目标),{#阻塞
                        'code':'prompt-rejected',#码
                        'message':'Goal round was rejected before entering its step.',#说明
                    })#结束阻塞
                return 决定#拒绝
            try:#决定后再核
                有效=预订仍有效(状态,内容,来源)#再核
            except Exception as 错误:#失败
                上下文对象.日志.警告('goal-round-driver: post-decision check failed for agent "'+str(智能体.id)+'": '+渲染抛出(错误))#警告
                解除武装(状态)#解除
                有效=False#无效
            if not 有效:#无效
                状态['attempt']=None#清掉
                恢复其它已领取(智能体,决定['messages'],提交['id'])#保留其它
                请求驱动(状态)#再跑
                return {'kind':'reject'}#拒绝
            下一决定=dict(决定)#拆离
            下一决定['startsRequestSeries']=True#开请求系列
            return 下一决定#进入
        上下文对象.监听('agent/pre-step',预步骤)#预步骤
        for 智能体 in 上下文对象.agents.列出():#已有智能体
            解除武装(状态于(智能体))#不继承自动权限
        def 拆除():#先停驱动
            """先停驱动再清表。"""
            等待=[]#待等线程
            for 状态 in list(状态表.values()):#逐个
                状态['stopping']=True#停止
                解除武装(状态)#解除
                尝试=状态['attempt']#预订
                if 尝试 is not None:#有预订
                    尝试['stale']=True#过期
                    if 状态['agent'].状态=='running':#还在跑
                        状态['agent'].取消({'kind':'parent'})#父取消
                        等待.append(状态['agent'])#等空闲
                if 状态['run'] is not None:#有线程
                    等待.append(状态['run'])#等线程
            for 项 in 等待:#逐个等
                if hasattr(项,'等到空闲'):#智能体
                    项.等到空闲()#等空闲
                elif hasattr(项,'join'):#线程
                    项.join()#等结束
            状态表.clear()#清表
        return 拆除#拆除器

    上下文对象.副作用(安装,'goal-round-driver lifecycle')#复合副作用

默认=应用#中文默认导出
default=应用#Cordis 默认导出
name=名称#框架槽
inject=注入#框架槽
apply=应用#框架槽
