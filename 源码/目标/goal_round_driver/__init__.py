"""叠在公开智能体、会话与目标服务上的同会话目标轮次驱动器。"""
import threading#串行驱动循环后台线程
from ...依赖 import cordis#外部依赖胶水
光纤状态=cordis.纤程状态#纤程状态，拆除时不再驱动
from ...模型后端.llm import 创建用户消息#铸造续跑用户消息
from .提示 import 渲染目标轮次提示#本包拥有的续跑提示渲染器

名称='goal-round-driver'#Cordis 插件名
注入=['agents','goals','sessions']#依赖智能体、目标与会话
name=名称#Cordis插件名
inject=注入#Cordis依赖声明

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待承诺
    return 值#同步值

def 深相等(左,右):#对齐 isDeepStrictEqual 的结构化比较
    """比较两条载荷是否深相等。"""
    return 左==右#结构化相等

def 是目标轮次来源(来源):#来源是否标识一次自动的、正数编号的目标轮次
    """正数目标轮次；排除轮次零。"""
    return 取字段(来源,'kind')=='goal' and 取字段(来源,'round')>0#排除轮次零

def 同轮次(来源,轮次身份):#把来源与一份预留身份比较
    """三键全等。"""
    return (取字段(来源,'goalId')==取字段(轮次身份,'goalId')#同一目标
        and 取字段(来源,'revision')==取字段(轮次身份,'revision')#同一修订
        and 取字段(来源,'round')==取字段(轮次身份,'round'))#同一轮次

def 同入队(正文,来源,尝试):#把完整入队记录与驱动器预约比较
    """来源加正文。"""
    return 是目标轮次来源(来源) and 同轮次(来源,尝试) and 深相等(正文,取字段(尝试,'content'))#身份与正文都对

def 目标引用(目标):#视图的精确当前引用
    """视图 → 比较交换引用。"""
    return {'id':取字段(目标,'id'),'revision':取字段(目标,'revision')}#身份加修订

def 渲染抛出(值):#日志用的人类可读意外值
    """错误文本；优先 Exception 消息。"""
    if isinstance(值,BaseException):#异常
        return str(值)#优先 message
    return str(值)#其它

def 信号已中止(信号):#对齐 signal.aborted
    """信号是否已中止。"""
    if 信号 is None:#无信号
        return False#未中止
    if 取字段(信号,'aborted') is True:#英文
        return True#已中止
    if 取字段(信号,'已中止') is True:#中文
        return True#已中止
    return False#未中止

def 应用(上下文):#安装同会话自动续跑及其竞态栅栏
    """注册驱动器。"""
    状态表={}#智能体 → 调度状态

    def 取状态(智能体):#为一个当前仍存活的精确智能体创建状态
        """懒创建调度状态。"""
        已有=状态表.get(智能体)#已有则用
        if 已有 is not None:#命中
            return 已有#命中
        状态={#新调度状态
            'agent':智能体,#所属智能体
            'attempt':None,#尚无预约
            'competingQueued':False,#尚无竞争提示
            'needsCheckpoint':False,#尚无检查点债
            'requested':False,#尚无驱动请求
            'run':None,#尚无在途任务
            'stopping':False,#未拆除
        }#结束新状态
        状态表[智能体]=状态#按实例记住
        return 状态#新状态

    def 当前目标(状态):#仅在精确智能体仍存活时读取
        """实时目标。"""
        if 上下文.agents.get(取字段(状态['agent'],'id')) is not 状态['agent']:#已换实例
            return None#已换实例
        return 上下文.goals.获取(状态['agent'])#当前视图

    def 可驱动(状态):#本精确生命周期是否静止且没有竞争提示
        """可否预约下一轮。"""
        return (上下文.fiber.state==光纤状态.已激活#插件纤程仍活跃
            and (not 状态['stopping'])#未拆除
            and 上下文.agents.get(取字段(状态['agent'],'id')) is 状态['agent']#仍是实时实例
            and 取字段(状态['agent'],'status')=='idle'#整智能体静止
            and (not 状态['competingQueued']))#没有竞争提示

    def 检查点后可驱动(状态):#再检查等待检查点期间可能已改变的每一项条件
        """检查点后仍可驱动。"""
        return 可驱动(状态) and (not 状态['needsCheckpoint'])#静止且没有新的检查点债

    def 解除武装(状态):#去掉自动权限，保留持久阶段
        """只在武装时解除。"""
        try:#域边界可能拒绝
            目标=当前目标(状态)#当前目标
            if 目标 is not None and 取字段(目标,'activation')=='armed':#只在武装时解除
                上下文.goals.解除武装(状态['agent'])#解除武装
        except Exception as 错误:#解除失败只记日志
            上下文.logger.warn('goal-round-driver: could not disarm agent "'+str(取字段(状态['agent'],'id'))+'": '+渲染抛出(错误))#不阻断拆除

    def 放回其它已领取(智能体,消息们,消息标识):#本驱动器只丢掉自己的轮次时，保留其它已领取的步骤上下文
        """把别人的消息放回。"""
        保留=[]#不是本轮、也不是轮次零
        for 消息 in 消息们:#筛选
            来源=取字段(消息,'source')#消息来源
            if 取字段(消息,'id')==消息标识:#本轮
                continue#丢掉本轮
            if 取字段(来源,'kind')=='goal' and 取字段(来源,'round')==0:#轮次零
                continue#也丢掉轮次零
            保留.append(消息)#保留
        for 消息 in reversed(保留):#逆序 prepend 以保持原顺序
            已在下一步=any(取字段(候选,'id')==取字段(消息,'id') for 候选 in 智能体.inbox.nextStep)#已在下一步
            已在下回合=any(取字段(候选,'id')==取字段(消息,'id') for 候选 in 智能体.inbox.nextTurn)#或已在下回合
            if 已在下一步 or 已在下回合:#已在收件箱
                continue#跳过
            智能体.inbox.prepend('next-step',消息)#放回下一步

    def 驱动(状态):#在静止时处理已接纳工作，然后最多再预约一轮
        """一次驱动扫描。"""
        智能体=状态['agent']#所属智能体
        if not 可驱动(状态):#条件不齐
            return#结束
        if 状态['needsCheckpoint']:#先刷持久化
            状态['needsCheckpoint']=False#清掉债，失败则不再预约
            try:#刷盘可能失败
                解开(上下文.sessions.flush(智能体.session))#把已提交事件落到存储
            except Exception as 错误:#检查点失败
                上下文.logger.warn('goal-round-driver: durability checkpoint failed for agent "'+str(取字段(智能体,'id'))+'": '+渲染抛出(错误))#记日志
                解除武装(状态)#去掉自动权限
                return#不再预约
            #检查点落定期间可能已有变更或普通提示到达。先让它们走自己的检查点/回合，再预约。
            if not 检查点后可驱动(状态):#落定后条件变了
                return#结束
        尝试=状态['attempt']#上一轮预约
        if 尝试 is not None:#上一轮还在账上：本扫描只清账
            状态['attempt']=None#丢掉已处理预约
            状态['needsCheckpoint']=True#下一扫描先刷盘
            状态['requested']=True#再请求一次驱动
            return#本扫描结束
        目标=当前目标(状态)#当前目标
        if 目标 is None or 取字段(目标,'phase')!='active' or 取字段(目标,'activation')!='armed':#不该自动续跑
            return#结束
        if 取字段(目标,'roundsStarted')>=取字段(目标,'maxGoalRounds'):#预算耗尽
            上下文.goals.阻塞(智能体,目标引用(目标),{#标为阻塞
                'code':'round-limit',#轮次上限
                'message':'Goal reached its configured limit of '+str(取字段(目标,'maxGoalRounds'))+' rounds.',#人类可读
            })#结束阻塞
            return#不再预约
        轮次=取字段(目标,'roundsStarted')+1#下一正数轮次
        正文=渲染目标轮次提示(目标,轮次)#本包拥有的提示正文
        消息=创建用户消息({#铸造续跑消息
            'content':正文,#渲染正文
            'source':{'kind':'goal','goalId':取字段(目标,'id'),'revision':取字段(目标,'revision'),'round':轮次},#钉死身份
        })#结束铸造
        预约={#入队前预留
            'goalId':取字段(目标,'id'),#所属目标
            'revision':取字段(目标,'revision'),#当前修订
            'round':轮次,#本轮号
            'messageId':取字段(消息,'id'),#消息 id
            'content':正文,#正文快照
            'phase':'queued',#已预约入队
            'cancelled':False,#尚未取消
            'stale':False,#尚未过时
        }#结束预约
        状态['attempt']=预约#先记账再 followup
        try:#followup 可能拒绝
            智能体.followup(消息)#入队下一回合
        except Exception as 错误:#入队失败
            状态['attempt']=None#清掉预约
            上下文.logger.warn('goal-round-driver: could not queue round '+str(轮次)+' for agent "'+str(取字段(智能体,'id'))+'": '+渲染抛出(错误))#记日志
            最新=当前目标(状态)#失败后的当前目标
            if (最新 is not None and 取字段(最新,'id')==取字段(目标,'id') and 取字段(最新,'revision')==取字段(目标,'revision')#仍是同一修订
                and 取字段(最新,'phase')=='active' and 取字段(最新,'activation')=='armed'):#仍武装
                上下文.goals.阻塞(智能体,目标引用(最新),{#入队失败则阻塞
                    'code':'queue-failed',#入队失败
                    'message':'Could not queue goal round '+str(轮次)+': '+渲染抛出(错误),#带原因
                })#结束阻塞

    def 请求驱动(状态):#把触发合并到每个智能体一份串行驱动器上
        """合并触发。"""
        if 状态['stopping']:#拆除中不再启动
            return#结束
        状态['requested']=True#记下待处理
        if 状态['run'] is not None:#已有在途任务会看到 requested
            return#合并
        def 循环体():#即将启动的串行任务
            """跑合并驱动循环。"""
            try:#withoutInitiator 可能拒绝
                def 跑():#不以本智能体为发起方
                    """合并期间到达的触发。"""
                    while 状态['requested'] and (not 状态['stopping']):#合并期间到达的触发
                        状态['requested']=False#本圈开始时清掉
                        try:#drive 可能抛
                            驱动(状态)#一次扫描
                        except Exception as 错误:#扫描失败
                            上下文.logger.warn('goal-round-driver: driver failed for agent "'+str(取字段(状态['agent'],'id'))+'": '+渲染抛出(错误))#记日志
                            解除武装(状态)#去掉自动权限
                结果=上下文.agents.withoutInitiator(跑)#不以本智能体为发起方
                解开(结果)#若可等待则等
            except Exception as 错误:#启动或任务失败
                上下文.logger.warn('goal-round-driver: could not start driver for agent "'+str(取字段(状态['agent'],'id'))+'": '+渲染抛出(错误))#记日志
                解除武装(状态)#去掉自动权限
            finally:#任务结束后允许再启动
                状态['run']=None#清掉在途
                if 状态['requested'] and (not 状态['stopping']):#尾触发再开一轮
                    请求驱动(状态)#重入
        try:#启动线程
            线程=threading.Thread(target=循环体,daemon=True)#后台串行任务
            状态['run']=线程#记下在途任务
            线程.start()#启动
        except Exception as 错误:#启动失败
            上下文.logger.warn('goal-round-driver: could not start driver for agent "'+str(取字段(状态['agent'],'id'))+'": '+渲染抛出(错误))#记日志
            解除武装(状态)#去掉自动权限
            状态['run']=None#没有在途任务

    def 装寿命():#一份复合 effect 把步骤栅栏一直装到本插件自己的调度任务落定
        """生命周期 effect：注册监听器，返回拆除闭包。"""
        def 智能体出错(载荷,*其余):#智能体出错
            """去掉自动权限。"""
            状态=取状态(取字段(载荷,'agent'))#拿到调度状态
            解除武装(状态)#去掉自动权限
        上下文.on('agent/error',智能体出错)#结束 agent/error
        def 智能体已创建(载荷,*其余):#新建时播种状态
            """新建时播种状态。"""
            取状态(取字段(载荷,'agent'))#播种
        上下文.on('agent/created',智能体已创建)#新建时播种状态
        def 智能体已拆除(载荷,*其余):#销毁时丢掉状态
            """销毁时丢掉状态。"""
            状态表.pop(取字段(载荷,'agent'),None)#丢掉状态
        上下文.on('agent/disposed',智能体已拆除)#销毁时丢掉状态
        def 会话开始(载荷,*其余):#会话开始边
            """不继承上一会话预约。"""
            状态=取状态(取字段(载荷,'agent'))#拿到调度状态
            状态['attempt']=None#不继承上一会话预约
            状态['competingQueued']=False#清空竞争标记
            状态['needsCheckpoint']=False#清空检查点债
        上下文.on('agent/session-start',会话开始)#结束 session-start
        def 状态翻转(载荷,*其余):#状态翻转
            """静止后尝试预约或清账。"""
            智能体=取字段(载荷,'agent')#所属智能体
            状态值=取字段(载荷,'status')#新状态
            状态=取状态(智能体)#拿到调度状态
            if 状态值=='idle':#回到静止
                状态['competingQueued']=False#静止后竞争提示已消费或清空
                尝试=状态['attempt']#当前预约
                目标=当前目标(状态)#当前目标
                相位=取字段(尝试,'phase') if 尝试 is not None else None#预约相位
                if ((相位=='queued' or 相位=='claimed' or (尝试 is not None and 尝试['cancelled']))#入队/领取/已取消
                    and 目标 is not None and 取字段(目标,'phase')=='active' and 取字段(目标,'activation')=='armed'):#仍武装
                    状态['attempt']=None#清掉未完成预约
                    try:#暂停可能拒绝
                        上下文.goals.暂停(智能体,目标引用(目标))#取消则暂停，避免立即再入队
                    except Exception as 错误:#暂停失败
                        上下文.logger.warn('goal-round-driver: could not pause cancelled goal for agent "'+str(取字段(智能体,'id'))+'": '+渲染抛出(错误))#记日志
                        解除武装(状态)#去掉自动权限
                请求驱动(状态)#静止后尝试预约或清账
        上下文.on('agent/status',状态翻转)#结束 agent/status
        def 目标变更(载荷,*其余):#目标变更
            """先刷盘再预约。"""
            状态=取状态(取字段(载荷,'agent'))#拿到调度状态
            状态['needsCheckpoint']=True#先刷盘再预约
            请求驱动(状态)#请求驱动
        上下文.on('goal/changed',目标变更)#结束 goal/changed
        def 收件箱插入(载荷,*其余):#收件箱插入
            """有竞争提示则标过时。"""
            智能体=取字段(载荷,'agent')#所属智能体
            消息=取字段(载荷,'message')#插入消息
            if not any(取字段(候选,'id')==取字段(消息,'id') for 候选 in 智能体.inbox.nextTurn):#不是下回合提示
                return#放过
            状态=取状态(智能体)#拿到调度状态
            尝试=状态['attempt']#当前预约
            if 尝试 is not None and 同入队(取字段(消息,'content'),取字段(消息,'source'),尝试):#就是本轮预约
                return#放过
            状态['competingQueued']=True#有竞争提示
            if 尝试 is not None and 取字段(尝试,'phase')=='queued':#尚未领取的本轮过时
                尝试['stale']=True#标过时
        上下文.on('agent/inbox/inserted',收件箱插入)#结束 inserted
        def 收件箱领取(载荷,*其余):#领取进入步骤
            """本轮进入已领取。"""
            智能体=取字段(载荷,'agent')#所属智能体
            消息=取字段(载荷,'message')#领取消息
            状态=取状态(智能体)#拿到调度状态
            尝试=状态['attempt']#当前预约
            if 尝试 is not None and 同入队(取字段(消息,'content'),取字段(消息,'source'),尝试):#就是本轮
                尝试['phase']='claimed'#进入已领取
        上下文.on('agent/inbox/claimed',收件箱领取)#结束 claimed
        def 收件箱丢弃(载荷,*其余):#丢弃
            """本轮记为取消。"""
            智能体=取字段(载荷,'agent')#所属智能体
            消息=取字段(载荷,'message')#丢弃消息
            状态=取状态(智能体)#拿到调度状态
            尝试=状态['attempt']#当前预约
            if 尝试 is not None and 同入队(取字段(消息,'content'),取字段(消息,'source'),尝试):#就是本轮
                尝试['cancelled']=True#记为取消
        上下文.on('agent/inbox/discarded',收件箱丢弃)#结束 discarded
        def 会话事件(会话,事件,*其余):#会话事件
            """只关心接纳与回合结束。"""
            智能体=上下文.agents.get(取字段(会话,'id'))#按会话 id 找智能体
            if 智能体 is None or 智能体.session is not 会话:#没有或已换会话
                return#放过
            状态=取状态(智能体)#拿到调度状态
            种类=取字段(事件,'type')#事件类型
            数据=取字段(事件,'data')#事件载荷
            if 种类=='user/message':#用户消息进入日志
                if 状态['attempt'] is not None and 取字段(数据,'id')==状态['attempt']['messageId']:#本轮消息被接纳
                    状态['attempt']['phase']='admitted'#进入已接纳
                return#其它用户消息忽略
            if 种类=='turn/end':#回合结束
                原因=取字段(数据,'reason')#结束原因
                if 取字段(原因,'kind')=='max-tokens':#打到 token 上限
                    解除武装(状态)#去掉自动权限
                    return#不再续跑
                if 取字段(原因,'kind')!='aborted':#正常结束交给静止驱动
                    return#放过
                尝试=状态['attempt']#当前预约
                相位=取字段(尝试,'phase') if 尝试 is not None else None#预约相位
                if 相位=='claimed' or 相位=='admitted':#本轮已进步骤
                    尝试['cancelled']=True#记为取消，静止时暂停
                else:#尚未进步骤则直接解除武装
                    解除武装(状态)#去掉自动权限
                return#中止处理完
            return#其它事件忽略
        上下文.on('session/event',会话事件)#结束 session/event

        def 有效预约(状态,正文,来源):#闭包失败，除非入队提示仍拥有精确实时修订
            """pre-step 前后都要过。"""
            尝试=状态['attempt']#当前预约
            目标=当前目标(状态)#当前目标
            return (上下文.fiber.state==光纤状态.已激活#纤程仍活跃
                and (not 状态['stopping']) and 尝试 is not None and 取字段(尝试,'phase')=='claimed'#已领取且未拆除
                and (not 尝试['stale']) and 同入队(正文,来源,尝试)#未过时且正文对得上
                and 目标 is not None and 取字段(目标,'id')==取字段(来源,'goalId') and 取字段(目标,'revision')==取字段(来源,'revision')#修订仍是入队时那份
                and 取字段(目标,'phase')=='active' and 取字段(目标,'activation')=='armed'#仍活跃且武装
                and 取字段(来源,'round')==取字段(目标,'roundsStarted')+1)#恰是下一轮

        def 步骤前(载荷,下一步,*其余):#步骤栅栏
            """目标轮次续跑的 pre-step 竞态栅栏。"""
            智能体=取字段(载荷,'agent')#所属智能体
            消息们=list(取字段(载荷,'messages') or [])#本步消息
            信号=取字段(载荷,'signal')#取消信号
            提交=None#本包续跑消息
            for 消息 in 消息们:#找目标轮次消息
                if 是目标轮次来源(取字段(消息,'source')):#正数目标轮次
                    提交=消息#找到
                    break#只取第一条
            if 提交 is None:#没有本包续跑则原样委托
                return 解开(下一步())#原样委托
            正文=取字段(提交,'content')#正文
            来源=取字段(提交,'source')#来源
            状态=取状态(智能体)#拿到调度状态
            有效=False#默认拒绝
            try:#校验可能抛
                有效=有效预约(状态,正文,来源)#入步骤前检查预约
            except Exception as 错误:#检查失败
                上下文.logger.warn('goal-round-driver: pre-step check failed for agent "'+str(取字段(智能体,'id'))+'": '+渲染抛出(错误))#记日志
                解除武装(状态)#去掉自动权限
            if not 有效:#预约已失效
                尝试=状态['attempt']#当前预约
                if 尝试 is not None and 同轮次(来源,尝试):#来源仍指向本预约
                    尝试['stale']=True#标过时
                    状态['attempt']=None#清掉预约
                放回其它已领取(智能体,消息们,取字段(提交,'id'))#把别人的消息放回
                请求驱动(状态)#稍后重调度
                return {'kind':'reject'}#拒绝本步
            try:#下游钩子可能抛
                判定=解开(下一步())#委托后续 pre-step
            except Exception as 错误:#下游抛错
                if 信号已中止(信号):#取消则原样抛
                    raise#原样抛
                #抛错的下游钩子会丢掉整份步骤提议。在平衡的无步骤回合回到 idle 前清掉预约，
                #好让下一次驱动扫描能重调度这一轮。
                状态['attempt']=None#清掉预约
                请求驱动(状态)#稍后重调度
                raise#继续抛
            if 信号已中止(信号):#下游返回后发现已取消
                if 取字段(判定,'kind')=='enter':#进入则放回别人的消息
                    放回其它已领取(智能体,取字段(判定,'messages') or [],取字段(提交,'id'))#放回
                return 判定#把取消后的判定交回去
            if 取字段(判定,'kind')=='reject':#下游拒绝本步
                状态['attempt']=None#清掉预约
                目标=当前目标(状态)#当前目标
                if (目标 is not None and 取字段(目标,'id')==取字段(来源,'goalId') and 取字段(目标,'revision')==取字段(来源,'revision')#仍是入队修订
                    and 取字段(目标,'phase')=='active' and 取字段(目标,'activation')=='armed'):#仍武装
                    上下文.goals.阻塞(智能体,目标引用(目标),{#提示被拒绝则阻塞
                        'code':'prompt-rejected',#步骤拒绝
                        'message':'Goal round was rejected before entering its step.',#人类可读
                    })#结束阻塞
                return 判定#交回拒绝
            try:#下游接受后再确认一次
                有效=有效预约(状态,正文,来源)#入步骤后检查预约
            except Exception as 错误:#检查失败
                上下文.logger.warn('goal-round-driver: post-decision check failed for agent "'+str(取字段(智能体,'id'))+'": '+渲染抛出(错误))#记日志
                解除武装(状态)#去掉自动权限
                有效=False#当作失效
            if not 有效:#接受后修订已变
                状态['attempt']=None#清掉预约
                放回其它已领取(智能体,取字段(判定,'messages') or [],取字段(提交,'id'))#放回别人的消息
                请求驱动(状态)#稍后重调度
                return {'kind':'reject'}#改口拒绝
            return 判定#预约仍有效，放行
        上下文.on('agent/pre-step',步骤前)#结束 pre-step

        #在已有智能体上加载生命周期驱动器时，从不继承先前生产者实例留下的隐藏自动权限。
        for 智能体 in 上下文.agents.list():#已存在的智能体
            状态=取状态(智能体)#播种状态
            解除武装(状态)#一律解除武装

        def 拆寿命():#拆除闭包
            """停止驱动、取消在途轮次，并等到调度任务落定。"""
            等待们=[]#等待在途工作
            for 状态 in list(状态表.values()):#每个智能体
                状态['stopping']=True#不再启动新驱动
                解除武装(状态)#去掉自动权限
                尝试=状态['attempt']#当前预约
                if 尝试 is not None:#还有在途轮次
                    尝试['stale']=True#标过时
                    if 取字段(状态['agent'],'status')=='running':#正在跑本轮
                        状态['agent'].cancel({'kind':'parent'})#父级取消
                        等待们.append(状态['agent'].whenIdle)#等到静止
                if 状态['run'] is not None:#还有驱动任务
                    等待们.append(状态['run'])#等到驱动任务结束
            for 等待 in 等待们:#成败都等完
                try:#allSettled 语义
                    if isinstance(等待,threading.Thread):#线程
                        等待.join()#等到结束
                    else:#可调用或可等待
                        解开(等待() if callable(等待) else 等待)#等 whenIdle 或承诺
                except Exception:#单个失败不挡其余
                    pass#吞掉：allSettled 语义
            状态表.clear()#丢掉全部调度状态
        return 拆寿命#拆除结束

    上下文.effect(装寿命,'goal-round-driver lifecycle')#effect 名

apply=应用#Cordis插件入口
default=应用#默认导出
默认=应用#中文默认导出

__all__=['名称','注入','应用','name','inject','apply','默认','default']#公开面
