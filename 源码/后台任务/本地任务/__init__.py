"""后台任务能力缝（`ctx.jobs`）的进程内提供方。每条记录只存在内存里，对外只交新鲜快照，从不交出在线状态。

注册比生产者和控制器 fiber 活得更久。智能体或服务拆除会取消在线工作并等待合规生产者；抛错的拆除取消只强制失败记录，并报告可能的孤儿。
"""
import json,math,time,threading#JSON片段、有限数、纪元毫秒与后台线程
from ...依赖 import cordis#外部依赖胶水
from ...依赖.schemastery import 路径上节点,整数字段#配置字段
承诺=cordis.工具.承诺#承诺
是否thenable=cordis.工具.是否thenable#可等待判定
已兑现=cordis.工具.已兑现#立刻兑现
from ..作用域 import 匿名条目,作用域层集,获取作用域#匿名条目、作用域分层与取作用域
from ..超时 import 截止,取超时#截止与超时码判定
from ..任务 import 任务注册表,任务标识#任务注册表与任务 id

任务等待超时='TASK_WAIT_TIMEOUT'#等待超时码
默认每所有者并发=10#每所有者默认并发
安全整数上限=9007199254740991#Number.MAX_SAFE_INTEGER
配置=路径上节点({#进程内注册表配置
    'maxConcurrentJobsPerOwner':整数字段(步进=1,最小=1,最大=安全整数上限,默认值=默认每所有者并发),#每所有者并发上限
})#结束 Config 模式
Config=配置#Cordis配置模式

__all__=[#仅中文公开名；Cordis 槽英文别名不入表
    '任务等待超时','默认每所有者并发','安全整数上限','配置',
    '取字段','解开','是否安全整数','本地任务注册表','默认',
]#公开面结束

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

def 是否安全整数(值):#对齐 JS Number.isSafeInteger
    """对齐 JS Number.isSafeInteger，排除布尔。"""
    if isinstance(值,bool):#布尔不是数字
        return False#布尔不是安全整数
    if isinstance(值,int):#整数
        return abs(值)<=安全整数上限#在安全范围内
    if isinstance(值,float):#浮点
        if not math.isfinite(值) or not 值.is_integer():#非有限或非整
            return False#不是安全整数
        return abs(值)<=安全整数上限#在安全范围内
    return False#其它类型

def 是否终态(状态):#三个终态 JobStatus 值为真
    """三个终态 JobStatus 值为真。"""
    return 状态=='completed' or 状态=='killed' or 状态=='failed'#完成、杀死或失败

def 信号已中止(信号):#对齐 signal?.aborted
    """英文 aborted 或中文 已中止 任一为真则视为已中止。"""
    if 信号 is None:#无信号
        return False#未中止
    if getattr(信号,'aborted',False) is True:#英文旗标
        return True#已中止
    if getattr(信号,'已中止',False) is True:#中文旗标
        return True#已中止
    return False#未中止

def 后台观察拒绝(值,记拒绝):#在后台等到 thenable 落定
    """在后台等到 thenable 落定，拒绝时记日志。"""
    def 观察():#收住拒绝
        """收住拒绝。"""
        try:#等待结算
            if hasattr(值,'等待'):#本库承诺
                值.等待()#等待结算
            else:#普通 thenable
                值.then(None,None)#等待结算
        except BaseException as 错误:#拒绝
            记拒绝(错误)#记拒绝
    线程=threading.Thread(target=观察)#后台观察
    线程.daemon=True#不挡住退出
    线程.start()#启动

class 任务层:#一层作用域的贡献
    """一层作用域的贡献：从它挂接的任务控制器，以及在那里注册的完成监听器。两张表都匿名，因为贡献由自己的 disposer 标识，从不靠第二个注册者能遮蔽的名字。"""
    def __init__(自身,_作用域=None):#建空层
        """建空层；作用域键由层集持有，本层不存。"""
        自身.控制器=匿名条目()#该层挂接的控制器
        自身.监听器=匿名条目()#该层完成监听器
        自身.变化=匿名条目()#该层变化观察者

    def 是否空(自身):#三表皆空才算空层
        """三表皆空才算空层。"""
        return 自身.控制器.是否空() and 自身.监听器.是否空() and 自身.变化.是否空()#控制器、监听器、观察者都空

class 本地任务注册表(任务注册表):#进程内任务注册表
    """内存里的 `jobs` 注册表。所有权、隔离与生命周期语义见 `@deepseek-ai/dsh-jobs` 的 Service Definition 约定，本实现遵守它们。"""
    Config=配置#配置模式

    def __init__(自身,上下文,配置值):#构造进程内注册表
        """构造进程内注册表。Schemastery 在构造服务前校验并填入默认值。"""
        super().__init__(上下文)#注册为 jobs 服务
        自身.maxConcurrentJobsPerOwner=取字段(配置值,'maxConcurrentJobsPerOwner')#并发上限
        自身.每所有者并发上限=自身.maxConcurrentJobsPerOwner#中文别名
        自身.store={}#按 id 存记录
        自身.存储=自身.store#中文别名
        自身.counters={}#按种类的序号计数
        自身.计数器=自身.counters#中文别名
        def 建层(作用域):#层工厂
            """新建一层贡献。"""
            return 任务层(作用域)#建层
        def 空变更():#变更通知为空操作
            """没有从一层派生缓存，因此变更通知是空操作。"""
            return#空操作
        自身.layers=作用域层集(建层,空变更)#按作用域分层
        自身.层集=自身.layers#中文别名
        自身.listenersClosed=False#拆除后不再跑监听器
        自身.监听器已关=False#中文别名
        自身.ownerCleanups={}#所有者拆除清理
        自身.所有者清理=自身.ownerCleanups#中文别名
        自身.selfCtx=上下文#自用上下文
        自身.自用上下文=上下文#中文别名
        def 拆除体():#登记服务拆除
            """拆除时清全部任务。"""
            def 拆除():#服务拆除回调
                """拆除整份注册表。"""
                自身.拆除全部()#清全部任务
            return 拆除#返回拆除器
        上下文.effect(拆除体,'jobs teardown')#拆除时清全部任务

    def 启动(自身,规格):#启动并登记任务
        """启动并原子登记任务，返回签发的 id。"""
        if not 自身.服务所有者(取字段(规格,'owner')):#没有控制器服务该所有者
            raise Exception('background jobs unavailable: no job controller serves this agent (load @deepseek-ai/dsh-tool-jobs in its composition)')#拒绝开工
        种类=取字段(规格,'kind')#种类
        if 种类 is None or len(种类)==0:#种类非空
            raise Exception('invalid job kind: expected a non-empty string')#种类非空
        标签=取字段(规格,'label')#标签
        if 标签 is None or len(标签)==0:#标签非空
            raise Exception('invalid job label: expected a non-empty string')#标签非空
        输出上限=取字段(规格,'outputLimitBytes')#输出上限
        if 输出上限 is not None and ((not 是否安全整数(输出上限)) or 输出上限<=0):#非正安全整数
            raise Exception('invalid outputLimitBytes: expected a positive safe integer, got '+json.dumps(输出上限,ensure_ascii=False))#上限非法
        所有者=取字段(规格,'owner')#精确所有者
        if 所有者 is not None:#有主则挂所有者清理
            自身.确保所有者清理(所有者)#挂所有者清理
        活跃=自身.活跃任务数(所有者)#该所有者活跃数
        if 活跃>=自身.每所有者并发上限:#已达并发上限
            raise Exception('background job limit reached for this owner (limit: '+str(自身.每所有者并发上限)+'); use job_kill to stop an unneeded job, wait for it to finish, then retry')#提示先停再试
        钩子=取字段(规格,'run')()#同步启动生产者
        序号=自身.计数器.get(种类,0)+1#该种类下一个序号
        自身.计数器[种类]=序号#记下序号
        标识=任务标识(种类+'-'+str(序号))#签发 <kind>-N
        已结算=承诺()#结算完成承诺
        def 标记已结算():#结算决议器
            """兑现结算承诺。"""
            已结算.兑现(None)#兑现
        任务={#可变在线记录
            'id':标识,#任务 id
            'kind':种类,#种类
            'label':标签,#标签
            'outputLimitBytes':输出上限,#输出上限
            'owner':所有者,#精确所有者
            'cancel':取字段(钩子,'cancel'),#取消
            'readOutput':取字段(钩子,'readOutput'),#增量读
            'status':'running',#刚登记为运行中
            'detail':None,#尚无细节
            'output':None,#尚无终态输出
            'startedAt':int(time.time()*1000),#登记时刻
            'finishedAt':None,#尚未结束
            'reported':False,#尚未报告
            'settled':已结算,#结算承诺
            'markSettled':标记已结算,#结算决议器
            'waiters':0,#尚无等待者
            'waitResolvers':set(),#空决议器集
        }#结束 job
        自身.存储[标识]=任务#写入存储
        def 跟进生产者():#生产者结算后续
            """等到 done 再结算；拒绝则强制失败。"""
            try:#正常结局
                结局=解开(取字段(钩子,'done'))#等待生产者
                自身.结算(任务,结局)#正常结局
            except BaseException as 错误:#done 拒绝
                自身.自用上下文.logger.warn('jobs: job '+str(任务['id'])+' producer done promise rejected (producer contract violation): '+str(错误))#记录约定违反
                自身.结算(任务,{'status':'failed','detail':str(错误)})#强制失败
        线程=threading.Thread(target=跟进生产者)#后台跟进
        线程.daemon=True#不挡住退出
        线程.start()#启动跟进
        自身.通知变化(任务['owner'])#宣布可见集合变化
        return 标识#返回签发的 id

    def 列出(自身,调用方=None):#列出可见任务
        """列出调用方可见任务的新鲜快照。"""
        会话=None if 调用方 is None else 取字段(调用方,'id')#调用方会话
        结果=[]#快照列表
        for 任务 in list(自身.存储.values()):#全部记录
            所有者=任务['owner']#精确所有者
            if 所有者 is None or 取字段(所有者,'id')==会话:#无主或同会话
                结果.append(自身.快照(任务))#投影快照
        return 结果#可见快照

    def 获取(自身,标识,调用方=None):#取非消费快照
        """取非消费快照。"""
        任务=自身.期望(标识)#查找或大声失败
        自身.断言访问(任务,调用方)#会话隔离围栏
        return 自身.快照(任务)#新鲜快照

    def 读取(自身,标识,调用方=None):#读取输出
        """读取输出增量或终态。"""
        任务=自身.期望(标识)#查找或大声失败
        自身.断言访问(任务,调用方)#会话隔离围栏
        if 任务['readOutput'] is not None:#有增量读钩子
            文本=任务['readOutput']()#消费增量
        elif 是否终态(任务['status']):#终态用最终输出
            文本=任务['output'] if 任务['output'] is not None else ''#最终输出
        else:#在线则空
            文本=''#空
        if 是否终态(任务['status']):#终态读取标为已报告
            任务['reported']=True#已报告
        return {'text':文本,'snapshot':自身.快照(任务)}#文本加读后快照

    def 终止(自身,标识,调用方=None,原因=None):#请求取消
        """请求取消，返回 requested 或 already-finished。"""
        任务=自身.期望(标识)#查找或大声失败
        自身.断言访问(任务,调用方)#会话隔离围栏
        if 是否终态(任务['status']):#已经终态
            任务['reported']=True#标为已报告
            return 'already-finished'#无需再取消
        任务['cancel'](原因)#请求生产者停止
        任务['status']='stopping'#转入停止中
        任务['reported']=True#kill 声称报告
        自身.通知变化(任务['owner'])#宣布 stopping 转移
        return 'requested'#已请求取消

    def 等待(自身,标识,超时毫秒,调用方=None,信号=None):#等待结算
        """等待结算或超时，返回当时快照。"""
        任务=自身.期望(标识)#查找或大声失败
        自身.断言访问(任务,调用方)#会话隔离围栏
        if (isinstance(超时毫秒,bool) or not isinstance(超时毫秒,(int,float))
            or not math.isfinite(超时毫秒) or 超时毫秒<=0):#超时非法
            raise Exception('invalid wait timeout: expected a positive number of milliseconds, got '+json.dumps(超时毫秒,ensure_ascii=False))#拒绝非法超时
        if not 是否终态(任务['status']):#仍在线才需要等
            if 信号已中止(信号):#已中止则立刻拒绝
                raise Exception('wait aborted')#已中止
            任务['waiters']+=1#计入等待者
            仍计数=[True]#是否仍计在 waiters 里
            def 减计数():#摘掉本次计数
                """摘掉本次计数。"""
                if not 仍计数[0]:#已经摘过
                    return#只摘一次
                仍计数[0]=False#只摘一次
                任务['waiters']-=1#减等待者
            截止对象=截止(信号,超时毫秒,任务等待超时)#作用域截止
            try:#有界等待
                等待承诺=承诺()#等到结算或中止
                停止监视=threading.Event()#停掉中止监视
                def 已结算时():#任务结算
                    """任务结算唤醒。"""
                    任务['waitResolvers'].discard(已结算时)#注销决议器
                    停止监视.set()#停中止监视
                    等待承诺.兑现(None)#等待成功
                def 监视中止():#截止或调用方中止
                    """监视截止信号。"""
                    while not 停止监视.is_set():#尚未停
                        if 信号已中止(截止对象.信号):#已中止
                            任务['waitResolvers'].discard(已结算时)#注销决议器
                            if 取超时(截止对象.信号,任务等待超时) is not None:#是有界超时
                                等待承诺.兑现(None)#超时仍返回当前快照
                            else:#调用方取消
                                减计数()#立刻摘掉等待者
                                等待承诺.拒绝(Exception('wait aborted'))#拒绝本次等待
                            停止监视.set()#停监视
                            return#结束
                        停止监视.wait(0.01)#短暂让出
                任务['waitResolvers'].add(已结算时)#登记结算唤醒
                监视线程=threading.Thread(target=监视中止)#中止监视线程
                监视线程.daemon=True#不挡住退出
                监视线程.start()#启动监视
                try:#等到决议
                    等待承诺.等待()#阻塞到结算或中止
                finally:#无论成败都停监视
                    停止监视.set()#停中止监视
            finally:#无论成败都摘计数并释放截止
                减计数()#退出时减等待者
                截止对象.释放()#清定时器
        if 是否终态(任务['status']):#等到终态则标已报告
            任务['reported']=True#已报告
        return 自身.快照(任务)#返回当时快照

    def 任务完成时(自身,监听器):#注册完成监听
        """注册完成监听器，返回拆除器。"""
        def 追加(层):#记入本上下文那一层
            """追加完成监听器。"""
            return 层.监听器.追加(监听器)#追加
        return 自身.层集.副作用(自身.ctx,追加,{'标签':'jobs.onJobDone()'})#记入本层

    def 任务变化时(自身,监听器):#注册列表变化监听
        """注册列表变化观察者，返回拆除器。"""
        def 追加(层):#记入本上下文那一层
            """追加变化观察者。"""
            return 层.变化.追加(监听器)#追加
        return 自身.层集.副作用(自身.ctx,追加,{'标签':'jobs.onJobsChanged()'})#记入本层

    def 挂接控制器(自身,名称):#挂接控制器
        """挂接控制器，返回拆除器。"""
        令牌=object()#本次控制器令牌
        def 追加(层):#记入本上下文那一层
            """追加控制器。"""
            return 层.控制器.追加(令牌)#追加
        return 自身.层集.副作用(自身.ctx,追加,{'标签':'jobs.attachController()'})#记入本层

    def 服务所有者(自身,所有者=None):#是否有控制器服务该所有者
        """已挂接的任务控制器能否收集并停止 owner 拥有的工作。"""
        if not 自身.层集.全局.控制器.是否空():#全局层服务所有人
            return True#全局可达
        作用域=None if 所有者 is None else 获取作用域(所有者.ctx)#所有者作用域
        for 层 in 自身.层集.链上层(作用域):#沿所有者作用域链
            if not 层.控制器.是否空():#任一层有控制器即可
                return True#可达
        return False#无控制器

    def 活跃任务数(自身,所有者):#活跃任务数
        """统计一个精确所有者或共享无主桶里的权威活跃记录。"""
        计数=0#计数
        for 任务 in 自身.存储.values():#扫全部记录
            if 任务['owner'] is 所有者 and (任务['status']=='running' or 任务['status']=='stopping'):#同所有者且未终态
                计数+=1#加一
        return 计数#活跃数

    def 完成监听器们(自身,所有者=None):#该所有者的完成监听器
        """拥有 owner 通知的完成监听器：先全局层，再沿所有者链。"""
        for 监听器 in 自身.层集.全局.监听器.诸值():#先全局层
            yield 监听器#产出
        作用域=None if 所有者 is None else 获取作用域(所有者.ctx)#所有者作用域
        for 层 in 自身.层集.链上层(作用域):#再沿链展开
            for 监听器 in 层.监听器.诸值():#本层监听器
                yield 监听器#产出

    def 期望(自身,标识):#按 id 取记录
        """查找任务，找不到则大声失败。"""
        任务=自身.存储.get(标识)#查存储
        if 任务 is None:#未知任务
            raise Exception('unknown job '+str(标识))#未知任务
        return 任务#找到的记录

    def 断言访问(自身,任务,调用方=None):#会话隔离检查
        """有主任务只对会话 id 匹配的调用方可达。"""
        所有者=任务['owner']#精确所有者
        if 所有者 is not None and 取字段(所有者,'id')!=(None if 调用方 is None else 取字段(调用方,'id')):#有主且会话不符
            raise Exception('job '+str(任务['id'])+' belongs to another session')#外会话拒绝

    def 快照(自身,任务):#投影快照
        """从可变记录投影一份新鲜只读快照。"""
        所有者会话=None if 任务['owner'] is None else 取字段(任务['owner'],'id')#所有者会话
        结果={#只读投影
            'id':任务['id'],#任务 id
            'kind':任务['kind'],#种类
            'label':任务['label'],#标签
            'status':任务['status'],#当前状态
            'startedAt':任务['startedAt'],#开始时间
            'reported':任务['reported'],#是否已报告
        }#骨架
        if 任务['outputLimitBytes'] is not None:#有上限才带
            结果['outputLimitBytes']=任务['outputLimitBytes']#输出上限
        if 所有者会话 is not None:#有主才带会话
            结果['ownerSession']=所有者会话#所有者会话
        if 任务['detail'] is not None:#有细节才带
            结果['detail']=任务['detail']#细节
        if 任务['finishedAt'] is not None:#有结束才带
            结果['finishedAt']=任务['finishedAt']#结束时间
        return 结果#结束快照

    def 变化观察者们(自身,所有者=None):#该所有者的变化观察者
        """拥有 owner 更新的变化观察者，解析方式与完成监听器相同。"""
        for 观察者 in 自身.层集.全局.变化.诸值():#先全局层
            yield 观察者#产出
        作用域=None if 所有者 is None else 获取作用域(所有者.ctx)#所有者作用域
        for 层 in 自身.层集.链上层(作用域):#再沿链展开
            for 观察者 in 层.变化.诸值():#本层观察者
                yield 观察者#产出

    def 通知变化(自身,所有者):#通知可见集合变化
        """宣布一个所有者的可见集合变了。"""
        for 监听器 in 自身.变化观察者们(所有者):#该所有者的观察者
            try:#包含一次回调
                监听器(所有者)#投递所有者
            except BaseException as 错误:#观察者抛错
                自身.自用上下文.logger.warn('jobs: onJobsChanged listener threw: '+str(错误))#记下但不传播

    def 结算(自身,任务,结局):#记录终态并通知
        """记录第一次终态结局，释放等待者，然后宣布完成。"""
        if 是否终态(任务['status']):#已终态则先到先得
            return#先到先得
        任务['status']=取字段(结局,'status')#写入终态
        任务['detail']=取字段(结局,'detail')#写入细节
        任务['output']=取字段(结局,'output')#写入最终输出
        任务['finishedAt']=int(time.time()*1000)#结算时刻
        if 任务['waiters']>0:#有等待者则标已报告
            任务['reported']=True#已报告
        快照=自身.快照(任务)#终态快照
        等待决议器=list(任务['waitResolvers'])#拷贝等待决议器
        任务['waitResolvers'].clear()#清空集合
        for 决议 in 等待决议器:#唤醒每个等待
            决议()#唤醒
        任务['markSettled']()#兑现结算承诺
        自身.通知变化(任务['owner'])#宣布可见集合变化
        if 自身.listenersClosed or 自身.监听器已关:#拆除后不再通知完成
            return#不再通知
        for 监听器 in 自身.完成监听器们(任务['owner']):#该所有者的完成监听器
            try:#包含一次回调
                返回=监听器(快照,任务['owner'])#投递快照与精确所有者
                if 是否thenable(返回):#观察返回的 Promise 但不等待
                    def 记拒绝(错误,标识=任务['id']):#记下拒绝
                        """记下拒绝。"""
                        自身.自用上下文.logger.warn('jobs: onJobDone listener rejected for '+str(标识)+': '+str(错误))#记下拒绝
                    后台观察拒绝(返回,记拒绝)#后台观察
            except BaseException as 错误:#监听器同步抛错
                自身.自用上下文.logger.warn('jobs: onJobDone listener threw for '+str(任务['id'])+': '+str(错误))#记下但不传播

    def 确保所有者清理(自身,所有者):#确保所有者拆除清理
        """经精确所有者的作用域挂接一次被等待的清理。"""
        所有者标识=取字段(所有者,'id')#所有者智能体 id
        智能体们=自身.自用上下文.get('agents')#智能体注册表
        if 智能体们 is None:#没有智能体服务
            raise Exception('background job ownership requires the agent registry (load @deepseek-ai/dsh-agent)')#所有权需要智能体注册表
        取=getattr(智能体们,'get',None)#英文 get
        if 取 is None:#中文获取
            取=智能体们.获取#中文方法
        if 取(所有者标识) is not 所有者:#不是当前注册实例
            raise Exception('agent "'+str(所有者标识)+'" is not the registered agent instance (background job owner must be live)')#所有者必须在线
        if 所有者 in 自身.所有者清理:#已经挂过
            return#已经挂过
        def 执行体():#所有者作用域拆除
            """挂接所有者清理。"""
            def 拆除():#所有者拆除回调
                """取消并丢掉其任务。"""
                自身.所有者清理.pop(所有者,None)#先摘记账
                自身.拆除所属(所有者)#取消并丢掉其任务
            return 拆除#返回拆除器
        拆下=所有者.ctx.effect(执行体,'jobs.ownerCleanup()')#诊断标签
        自身.所有者清理[所有者]=拆下#记下 disposer

    def 拆除所属(自身,所有者):#拆除一名所有者的任务
        """取消、等待终态记录，并丢掉一个精确智能体生命周期拥有的每一条任务。"""
        已拥有=[任务 for 任务 in list(自身.存储.values()) if 任务['owner'] is 所有者]#该所有者的记录
        自身.拆除取消(已拥有,'owner disposed')#拆除取消
        for 任务 in 已拥有:#等待全部结算
            解开(任务['settled'])#等待结算
        for 任务 in 已拥有:#从存储丢掉
            自身.存储.pop(任务['id'],None)#丢掉
        if len(已拥有)>0:#有丢掉才通知
            自身.通知变化(所有者)#宣布移除

    def 拆除全部(自身):#拆除整份注册表
        """关闭监听器、取消在线任务、等待结算，并拆掉所有者 effect。"""
        自身.listenersClosed=True#此后不再跑完成监听
        自身.监听器已关=True#中文旗标
        全部=list(自身.存储.values())#当时全部记录
        自身.拆除取消(全部,'jobs service disposed')#拆除取消
        for 任务 in 全部:#等待全部结算
            解开(任务['settled'])#等待结算
        已清空=set()#刚被清空的所有者
        for 任务 in 全部:#收集所有者
            已清空.add(任务['owner'])#记下所有者
        自身.存储.clear()#丢掉全部记录
        for 所有者 in 已清空:#逐个宣布清空
            自身.通知变化(所有者)#宣布清空
        所有者清理们=list(自身.所有者清理.values())#拷贝 disposer
        自身.所有者清理.clear()#先清空记账
        for 清理 in 所有者清理们:#拆掉跨 fiber effect
            解开(清理())#等待拆除

    def 拆除取消(自身,任务们,原因):#拆除取消
        """拆除期间按任务包含地取消。"""
        for 任务 in 任务们:#逐条处理
            if 是否终态(任务['status']):#已终态则跳过
                continue#跳过
            任务['reported']=True#拆除声称已报告
            try:#包含一次 cancel
                任务['cancel'](原因)#请求生产者停止
                任务['status']='stopping'#转入停止中
                自身.通知变化(任务['owner'])#宣布 stopping 转移
            except BaseException as 错误:#cancel 抛错
                细节='cancel threw during teardown; work may be orphaned: '+str(错误)#可能孤儿
                自身.自用上下文.logger.warn('jobs: cancel of '+str(任务['id'])+' threw during teardown; job record forced failed and work may be orphaned: '+str(错误))#记下强制失败
                自身.结算(任务,{'status':'failed','detail':细节})#强制失败记录

默认=本地任务注册表#默认导出
default=本地任务注册表#Cordis默认导出
