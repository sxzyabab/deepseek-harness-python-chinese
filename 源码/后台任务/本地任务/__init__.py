"""jobs 服务的进程内提供方。记录只存在内存里，对外只交新鲜快照，从不交出在线状态。"""
import json,math,time,threading,weakref
from concurrent.futures import Future as 原生结果
from ...依赖.schemastery import 整数字段
from ...内核.作用域 import 作用域层集,获取作用域
from ...工具.超时 import 截止,取超时,已中止
from ..后台任务 import 任务注册表,任务标识
from .事件 import 任务层,任务事件枢纽
from .泵送 import 启动泵送
from .环 import 输出环

任务等待超时='TASK_WAIT_TIMEOUT'
默认每所有者并发=10
默认保留字节=256*1024
默认结算保留字节=16*1024
默认泵送轮询毫秒=150
安全整数上限=9007199254740991
配置={
    'maxConcurrentJobsPerOwner':整数字段(默认值=默认每所有者并发),
    'retainBytes':整数字段(默认值=默认保留字节),
    'settledRetainBytes':整数字段(默认值=默认结算保留字节),
    'pumpPollMs':整数字段(默认值=默认泵送轮询毫秒),
}

class 本地任务错误(Exception):
    """本地任务入参、所有权或组合非法。"""
    def __init__(自身,消息):
        """用原样英文消息构造。"""
        super().__init__(消息)

class 操作任务:
    """单次操作的 Future 包装，只留等待。"""
    def __init__(自身):
        """构造未决任务。"""
        自身._未来=原生结果()

    def 兑现(自身,值=None):
        """成功结算。"""
        if not 自身._未来.done():
            自身._未来.set_result(值)
        return 值

    def 拒绝(自身,错误):
        """失败结算。"""
        if not 自身._未来.done():
            if isinstance(错误,BaseException):
                自身._未来.set_exception(错误)
            else:
                自身._未来.set_exception(本地任务错误(错误))

    def 等待(自身,超时=None):
        """阻塞到结算。"""
        return 自身._未来.result(timeout=超时)

def 是否终态(状态):
    """三个终态 JobStatus 值为真。"""
    return 状态=='completed' or 状态=='killed' or 状态=='failed'

def 取配置整数(配置值,键,缺省):
    """读已填默认的整数配置。"""
    return 配置值[键] if 键 in 配置值 and 配置值[键] is not None else 缺省

class 本地任务注册表(任务注册表):
    """内存里的 jobs 注册表。"""
    Config=配置

    def __init__(自身,上下文,配置值):
        """构造进程内注册表。配置是 dict。"""
        super().__init__(上下文)
        自身.每所有者并发上限=取配置整数(配置值,'maxConcurrentJobsPerOwner',默认每所有者并发)
        自身.保留字节=取配置整数(配置值,'retainBytes',默认保留字节)
        自身.结算保留字节=取配置整数(配置值,'settledRetainBytes',默认结算保留字节)
        自身.泵送轮询毫秒=取配置整数(配置值,'pumpPollMs',默认泵送轮询毫秒)
        自身.存储={}
        自身.计数器={}
        def 建层(作用域):
            """新建一层贡献。"""
            return 任务层(作用域)
        def 空变更():
            """没有从一层派生缓存。"""
            return
        自身.层集=作用域层集(建层,空变更)
        自身.枢纽=任务事件枢纽(自身.层集,lambda 消息:上下文.日志.警告(消息))
        自身.所有者清理=weakref.WeakKeyDictionary()
        自身.自用上下文=上下文
        def 拆除体():
            """拆除时清全部任务。"""
            def 拆除():
                """拆除整份注册表。"""
                自身.拆除全部()
            return 拆除
        上下文.副作用(拆除体,'jobs teardown')

    @property
    def 事件(自身):
        """绑定访问上下文的事件流。"""
        登记方=自身.ctx
        def 订阅(过滤,监听器):
            """登记一次监听。"""
            return 自身.枢纽.订阅(登记方,过滤,监听器)
        return {'订阅':订阅,'subscribe':订阅}

    def 启动(自身,规格):
        """启动并原子登记任务，返回签发的 id。规格是 dict。"""
        所有者=自身.解析所有者(规格['owner'] if 'owner' in 规格 else None)
        if not 自身.服务所有者(所有者):
            raise 本地任务错误('background jobs unavailable: no job controller serves this agent (load @deepseek-ai/dsh-tool-jobs in its composition)')
        种类=规格['kind'] if 'kind' in 规格 else None
        if 种类 is None or len(种类)==0:
            raise 本地任务错误('invalid job kind: expected a non-empty string')
        标签=规格['label'] if 'label' in 规格 else None
        if 标签 is None or len(标签)==0:
            raise 本地任务错误('invalid job label: expected a non-empty string')
        输出上限=规格['outputLimitBytes'] if 'outputLimitBytes' in 规格 else None
        if 输出上限 is not None:
            if isinstance(输出上限,bool):
                合法=False
            elif isinstance(输出上限,int):
                合法=输出上限>0 and 输出上限<=安全整数上限
            elif isinstance(输出上限,float) and 输出上限.is_integer():
                合法=输出上限>0 and 输出上限<=安全整数上限
            else:
                合法=False
            if not 合法:
                raise 本地任务错误('invalid outputLimitBytes: expected a positive safe integer, got '+json.dumps(输出上限,ensure_ascii=False,separators=(',',':'),allow_nan=False))
            输出上限=int(输出上限)
        if 所有者 is not None:
            自身.确保所有者清理(所有者)
        if 自身.活跃任务数(所有者)>=自身.每所有者并发上限:
            raise 本地任务错误('background job limit reached for this owner (limit: '+str(自身.每所有者并发上限)+'); use job_kill to stop an unneeded job, wait for it to finish, then retry')
        序号=自身.计数器[种类]+1 if 种类 in 自身.计数器 else 1
        自身.计数器[种类]=序号
        标识=任务标识(种类+'-'+str(序号))
        环=输出环()
        状态={'progress':None,'job':None}
        def 追加(文本,选项=None):
            """生产者追加一块。"""
            自身.追加环(状态,环,文本,选项,'producer')
        def 更新进度(行):
            """替换进度行。"""
            自身.更新进度(状态,行)
        句柄={'id':标识,'append':追加,'updateProgress':更新进度}
        钩子=规格['run'](句柄)
        已结算=操作任务()
        def 标记已结算():
            """兑现结算承诺。"""
            已结算.兑现(None)
        任务={
            'id':标识,
            'kind':种类,
            'label':标签,
            'outputLimitBytes':输出上限,
            'owner':所有者,
            'cancel':钩子['cancel'] if isinstance(钩子,dict) else 钩子.cancel,
            'status':'running',
            'ring':环,
            'modelCursor':0,
            'resultDelivered':False,
            'state':状态,
            'detail':None,
            'result':None,
            'startedAt':int(time.time()*1000),
            'finishedAt':None,
            'killReason':None,
            'settleCause':None,
            'settled':已结算,
            'markSettled':标记已结算,
            'waitResolvers':set(),
            'pump':None,
            'spillPaths':[],
        }
        状态['job']=任务
        自身.存储[标识]=任务
        自身.发出({'type':'registered','job':自身.快照(任务)},所有者)
        def 生产者完成():
            """等到 done；拒绝则强制失败。"""
            try:
                完成=钩子['done'] if isinstance(钩子,dict) else 钩子.done
                if hasattr(完成,'等待'):
                    return 完成.等待()
                return 完成
            except BaseException as 错误:
                自身.自用上下文.日志.警告('jobs: job '+str(任务['id'])+' producer done promise rejected (producer contract violation): '+str(错误))
                return {'status':'failed','detail':str(错误)}
        生产者任务=操作任务()
        泵直到=操作任务()
        def 盯泵直到(任务):
            """生产者或注册表结算任一完成即停泵。"""
            try:
                任务.等待()
            except BaseException:
                pass
            泵直到.兑现(None)
        def 跟进生产者():
            """后台等到生产者再结算。"""
            结局=生产者完成()
            生产者任务.兑现(结局)
            泵=任务['pump']
            if 泵 is not None:
                泵.等待()
            自身.结算(任务,结局,任务['settleCause'] if 任务['settleCause'] is not None else 'producer')
        输出=规格['output'] if 'output' in 规格 else None
        if 输出 is not None and len(输出)>0:
            def 泵追加(文本,选项=None):
                """泵写入环。"""
                自身.追加环(状态,环,文本,选项,'pump')
            def 泵溢出(下标,路径):
                """记下源当前溢出文件。"""
                while len(任务['spillPaths'])<=下标:
                    任务['spillPaths'].append(None)
                任务['spillPaths'][下标]=路径
            threading.Thread(target=盯泵直到,args=(生产者任务,),daemon=True).start()
            threading.Thread(target=盯泵直到,args=(已结算,),daemon=True).start()
            任务['pump']=启动泵送(
                [自身.守护源(任务,源) for 源 in 输出],
                {'append':泵追加,'spill':泵溢出},
                自身.泵送轮询毫秒,
                泵直到,
            )
        线程=threading.Thread(target=跟进生产者,daemon=True)
        线程.start()
        return 标识

    def 列出(自身,调用方=None):
        """列出调用方可见任务的新鲜快照。调用方是会话标识。"""
        结果=[]
        for 任务 in list(自身.存储.values()):
            所有者=任务['owner']
            if 所有者 is None or 所有者.id==调用方:
                结果.append(自身.快照(任务))
        return 结果

    def 获取(自身,标识,调用方=None):
        """取非消费快照。"""
        return 自身.快照(自身.期望(标识,调用方))

    def 读取(自身,标识,调用方=None):
        """从模型游标消费输出环。"""
        return 自身.读取任务(自身.期望(标识,调用方))

    def 按偏移读取(自身,标识,起点,调用方=None):
        """不移动模型游标的保留输出读取。"""
        任务=自身.期望(标识,调用方)
        if isinstance(起点,bool) or not isinstance(起点,(int,float)):
            raise 本地任务错误('invalid output read offset: expected a non-negative safe integer, got '+json.dumps(起点,ensure_ascii=False,separators=(',',':'),allow_nan=False))
        if isinstance(起点,float):
            if (not 起点.is_integer()) or 起点<0 or 起点>安全整数上限:
                raise 本地任务错误('invalid output read offset: expected a non-negative safe integer, got '+json.dumps(起点,ensure_ascii=False,separators=(',',':'),allow_nan=False))
            起点=int(起点)
        elif 起点<0 or 起点>安全整数上限:
            raise 本地任务错误('invalid output read offset: expected a non-negative safe integer, got '+json.dumps(起点,ensure_ascii=False,separators=(',',':'),allow_nan=False))
        return 任务['ring'].从偏移读取(起点)

    def 终止(自身,标识,调用方=None,原因=None):
        """请求取消。"""
        return 自身.终止任务(自身.期望(标识,调用方),原因)

    def 等待(自身,标识,超时毫秒,调用方=None,信号=None):
        """等待结算或超时。"""
        return 自身.等待任务(自身.期望(标识,调用方),超时毫秒,信号)

    def 移除(自身,标识,调用方=None):
        """丢掉一条已结算记录。"""
        任务=自身.期望(标识,调用方)
        if not 是否终态(任务['status']):
            raise 本地任务错误('job '+str(标识)+' is still '+str(任务['status'])+'; kill it and wait for settlement before removing it')
        自身.丢掉([任务])

    def 挂接控制器(自身,名称):
        """挂接控制器，返回拆除器。"""
        令牌=object()
        def 追加(层):
            """追加控制器。"""
            return 层.控制器.追加(令牌)
        return 自身.层集.副作用(自身.ctx,追加,{'标签':'jobs.attachController()'})

    def 解析所有者(自身,会话):
        """把规格的所有者会话解析成在线智能体。"""
        if 会话 is None:
            return None
        智能体表=自身.自用上下文.获取服务('agents',False)
        if 智能体表 is None:
            raise 本地任务错误('background job ownership requires the agent registry (load @deepseek-ai/dsh-agent)')
        所有者=智能体表.获取(会话) if hasattr(智能体表,'获取') else 智能体表.get(会话)
        if 所有者 is None:
            raise 本地任务错误('session "'+str(会话)+'" has no live agent (background job owner must be live)')
        return 所有者

    def 服务所有者(自身,所有者=None):
        """已挂接的任务控制器能否收集并停止 owner 拥有的工作。"""
        if not 自身.层集.全局.控制器.是否空():
            return True
        作用域=None if 所有者 is None else 获取作用域(所有者.ctx)
        for 层 in 自身.层集.链上层(作用域):
            if not 层.控制器.是否空():
                return True
        return False

    def 活跃任务数(自身,所有者):
        """统计一个精确所有者或共享无主桶里的权威活跃记录。"""
        计数=0
        for 任务 in 自身.存储.values():
            if 任务['owner'] is 所有者 and (任务['status']=='running' or 任务['status']=='stopping'):
                计数+=1
        return 计数

    def 期望(自身,标识,调用方=None):
        """查找并检查访问。"""
        if 标识 not in 自身.存储:
            raise 本地任务错误('unknown job '+str(标识))
        任务=自身.存储[标识]
        自身.断言访问(任务,调用方)
        return 任务

    def 断言访问(自身,任务,调用方=None):
        """有主任务只对会话 id 匹配的调用方可达。"""
        所有者=任务['owner']
        if 所有者 is not None and 所有者.id!=调用方:
            raise 本地任务错误('job '+str(任务['id'])+' belongs to another session')

    def 快照(自身,任务):
        """从可变记录投影一份新鲜只读快照。"""
        所有者会话=None if 任务['owner'] is None else 任务['owner'].id
        溢出路径=[]
        已见=set()
        for 路径 in 任务['spillPaths']:
            if 路径 is None or 路径 in 已见:
                continue
            已见.add(路径)
            溢出路径.append(路径)
        输出={'total':任务['ring'].总量,'earliest':任务['ring'].最早}
        if len(溢出路径)>0:
            输出['spillPaths']=溢出路径
        结果={
            'id':任务['id'],
            'kind':任务['kind'],
            'label':任务['label'],
            'status':任务['status'],
            'startedAt':任务['startedAt'],
            'output':输出,
        }
        if 所有者会话 is not None:
            结果['owner']=所有者会话
        if 任务['outputLimitBytes'] is not None:
            结果['outputLimitBytes']=任务['outputLimitBytes']
        进度=任务['state']['progress']
        if 进度 is not None:
            结果['progress']=进度
        if 任务['detail'] is not None:
            结果['detail']=任务['detail']
        if 任务['finishedAt'] is not None:
            结果['finishedAt']=任务['finishedAt']
        return 结果

    def 发出(自身,事件,所有者):
        """投递一次事件。"""
        自身.枢纽.发出(事件,所有者)

    def 读取任务(自身,任务):
        """从模型游标消费环。"""
        读=任务['ring'].从偏移读取(任务['modelCursor'])
        任务['modelCursor']=任务['ring'].总量
        结果=None
        if 是否终态(任务['status']) and (not 任务['resultDelivered']):
            结果=任务['result']
        if 结果 is not None:
            任务['resultDelivered']=True
        if 是否终态(任务['status']):
            任务['ring'].修剪(自身.结算保留字节)
        返回={'chunks':读['chunks'],'lossy':读['lossy'],'job':自身.快照(任务)}
        if 结果 is not None:
            返回['result']=结果
        return 返回

    def 终止任务(自身,任务,原因=None):
        """请求取消。"""
        if 是否终态(任务['status']):
            return 'already-finished'
        任务['cancel'](原因)
        任务['status']='stopping'
        if 原因 is not None:
            任务['killReason']=原因
        任务['settleCause']='kill'
        自身.发出({'type':'stopping','job':自身.快照(任务)},任务['owner'])
        return 'requested'

    def 等待任务(自身,任务,超时毫秒,信号=None):
        """等待结算或超时。"""
        if (isinstance(超时毫秒,bool) or not isinstance(超时毫秒,(int,float))
            or not math.isfinite(超时毫秒) or 超时毫秒<=0):
            raise 本地任务错误('invalid wait timeout: expected a positive number of milliseconds, got '+json.dumps(超时毫秒,ensure_ascii=False,separators=(',',':'),allow_nan=False))
        if not 是否终态(任务['status']):
            if 已中止(信号):
                raise 本地任务错误('wait aborted')
            截止对象=截止(信号,超时毫秒,任务等待超时)
            try:
                等待任务=操作任务()
                停止监视=threading.Event()
                def 已结算时():
                    """任务结算唤醒。"""
                    任务['waitResolvers'].discard(已结算时)
                    停止监视.set()
                    等待任务.兑现(None)
                def 监视中止():
                    """监视截止信号。"""
                    while not 停止监视.is_set():
                        if 已中止(截止对象.信号):
                            任务['waitResolvers'].discard(已结算时)
                            if 取超时(截止对象.信号,任务等待超时) is not None:
                                等待任务.兑现(None)
                            else:
                                等待任务.拒绝(本地任务错误('wait aborted'))
                            停止监视.set()
                            return
                        停止监视.wait(0.01)
                任务['waitResolvers'].add(已结算时)
                监视线程=threading.Thread(target=监视中止,daemon=True)
                监视线程.start()
                try:
                    等待任务.等待()
                finally:
                    停止监视.set()
            finally:
                截止对象.释放()
        return 自身.快照(任务)

    def 追加环(自身,状态,环,文本,选项,写方):
        """追加一块。已结算的生产者写入记日志并丢掉。"""
        任务=状态['job']
        if 任务 is not None and 是否终态(任务['status']):
            if 写方=='producer':
                自身.自用上下文.日志.警告('jobs: append to settled job '+str(任务['id'])+' dropped')
            return
        if not 环.追加(文本,选项,自身.保留字节):
            return
        if 任务 is not None:
            自身.发出输出(任务)

    def 守护源(自身,任务,源):
        """包含失败的拉取源：首次抛错后读作已耗尽。"""
        已失败=[False]
        通道=源['channel'] if isinstance(源,dict) and 'channel' in 源 else getattr(源,'channel',None)
        def 读取(起点):
            """读增量。"""
            if 已失败[0]:
                return {'text':'','nextOffset':起点,'lossy':False}
            try:
                if isinstance(源,dict):
                    return 源['read'](起点)
                return 源.read(起点)
            except BaseException as 错误:
                已失败[0]=True
                自身.自用上下文.日志.警告('jobs: output source for '+str(任务['id'])+' failed; its stream stops here: '+str(错误))
                return {'text':'','nextOffset':起点,'lossy':False}
        结果={'read':读取}
        if 通道 is not None:
            结果['channel']=通道
        return 结果

    def 发出输出(自身,任务):
        """宣布环前进。"""
        所有者会话=None if 任务['owner'] is None else 任务['owner'].id
        事件={'type':'output','id':任务['id'],'total':任务['ring'].总量}
        if 所有者会话 is not None:
            事件['owner']=所有者会话
        自身.发出(事件,任务['owner'])

    def 更新进度(自身,状态,行):
        """替换进度行。"""
        任务=状态['job']
        if 任务 is not None and 是否终态(任务['status']):
            自身.自用上下文.日志.警告('jobs: progress update on settled job '+str(任务['id'])+' dropped')
            return
        状态['progress']=行
        if 任务 is not None:
            自身.发出({'type':'progress','job':自身.快照(任务)},任务['owner'])

    def 结算(自身,任务,结局,起因):
        """记录第一次终态结局，释放等待者，然后宣布完成。"""
        if 是否终态(任务['status']):
            return
        任务['status']=结局['status']
        if 结局['status']=='killed' and 任务['killReason'] is not None:
            细节=结局['detail'] if 'detail' in 结局 else None
            任务['detail']=(细节+'; '+任务['killReason']) if 细节 is not None else 任务['killReason']
        elif 'detail' in 结局 and 结局['detail'] is not None:
            任务['detail']=结局['detail']
        任务['state']['progress']=None
        任务['result']=结局['result'] if 'result' in 结局 else None
        任务['finishedAt']=int(time.time()*1000)
        未消费=任务['ring'].总量-任务['modelCursor']
        任务['ring'].修剪(max(自身.结算保留字节,未消费))
        等待决议器=list(任务['waitResolvers'])
        任务['waitResolvers'].clear()
        for 决议 in 等待决议器:
            决议()
        任务['markSettled']()
        自身.发出(
            {'type':'settled','job':自身.快照(任务),'cause':起因,'awaited':len(等待决议器)>0},
            任务['owner'],
        )
        自身.发出输出(任务)

    def 确保所有者清理(自身,所有者):
        """经精确所有者的作用域挂接一次被等待的清理。"""
        if 所有者 in 自身.所有者清理:
            return
        def 执行体():
            """挂接所有者清理。"""
            def 拆除():
                """取消并丢掉其任务。"""
                自身.所有者清理.pop(所有者,None)
                自身.拆除所属(所有者)
            return 拆除
        拆下=所有者.ctx.副作用(执行体,'jobs.ownerCleanup()')
        自身.所有者清理[所有者]=拆下

    def 拆除所属(自身,所有者):
        """取消、等待终态记录，并丢掉一个精确智能体生命周期拥有的每一条任务。"""
        已拥有=[任务 for 任务 in list(自身.存储.values()) if 任务['owner'] is 所有者]
        自身.拆除取消(已拥有,'owner disposed')
        for 任务 in 已拥有:
            任务['settled'].等待()
        自身.丢掉(已拥有)

    def 丢掉(自身,任务列表):
        """丢掉已结算记录并宣布每条 removed。"""
        for 任务 in 任务列表:
            自身.存储.pop(任务['id'],None)
            自身.发出({'type':'removed','job':自身.快照(任务)},任务['owner'])

    def 拆除全部(自身):
        """取消在线任务、等待结算，并拆掉所有者 effect。"""
        全部=list(自身.存储.values())
        自身.拆除取消(全部,'jobs service disposed')
        for 任务 in 全部:
            任务['settled'].等待()
        自身.丢掉(全部)
        所有者清理列表=list(自身.所有者清理.values())
        自身.所有者清理.clear()
        for 清理 in 所有者清理列表:
            清理()

    def 拆除取消(自身,任务列表,原因):
        """拆除期间按任务包含地取消。"""
        for 任务 in 任务列表:
            if 是否终态(任务['status']):
                continue
            任务['settleCause']='teardown'
            try:
                任务['cancel'](原因)
                任务['status']='stopping'
                自身.发出({'type':'stopping','job':自身.快照(任务)},任务['owner'])
            except BaseException as 错误:
                细节='cancel threw during teardown; work may be orphaned: '+str(错误)
                自身.自用上下文.日志.警告('jobs: cancel of '+str(任务['id'])+' threw during teardown; job record forced failed and work may be orphaned: '+str(错误))
                自身.结算(任务,{'status':'failed','detail':细节},'teardown')

__all__=[
    '任务等待超时','默认每所有者并发','默认保留字节','默认结算保留字节',
    '默认泵送轮询毫秒','安全整数上限','配置',
    '本地任务错误','操作任务','本地任务注册表',
]
Config=配置
default=本地任务注册表
