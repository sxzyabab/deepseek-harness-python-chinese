"""一次工作流运行的宿主侧。第一份 worker 结果、意外死亡、或取消宽限到期拥有结算权并关闭消息准入。待启动项共享一条中止信号；已发布的子运行共享幂等清理，静止等待两者，并对缺失的结束事件做合成。"""
import os,queue,tempfile,threading,time#平台、队列、临时目录、线程与宽限睡眠
from concurrent.futures import Future as _原生Future#单次操作结果
from ...模型后端.llm import 断言永不#穷尽检查
from ...内核.会话 import 快照json值#JSON 无损快照
from ..工作流.运行时类型 import 工作流运行#存活运行协议
from .领域 import 渲染抛出#抛出值渲染
from .协议 import 宿主到工人类型,工人到宿主类型#双向消息标签
from .会话 import 跑工人会话#worker 侧会话

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

class 操作任务:#单次异步结果
    def __init__(自身):#构造未决任务
        自身._future=_原生Future()#底层 Future
    def 兑现(自身,值=None):#成功结算
        if not 自身._future.done():#尚未结算
            自身._future.set_result(值)#写入结果
        return 值#返回兑现值
    def 拒绝(自身,错误):#失败结算
        if not 自身._future.done():#尚未结算
            if isinstance(错误,BaseException):#已是异常
                自身._future.set_exception(错误)#原样拒绝
            else:#非异常
                自身._future.set_exception(Exception(错误))#包装拒绝
    def wait(自身,超时=None):#阻塞等待
        return 自身._future.result(timeout=超时)#取结果或抛错
    def 等待(自身,超时=None):#兼容外来调用
        return 自身.wait(超时)#转发

def _是否thenable(值):#判定可等待对象
    if 值 is None:#空不是
        return False#不是
    if callable(getattr(值,'wait',None)):#Future 风格
        return True#可等待
    return callable(getattr(值,'等待',None))#外来 thenable

def _等待(值):#统一阻塞到结算
    if callable(getattr(值,'wait',None)):#Future 风格
        return 值.wait()#等待
    return 值.等待()#外来 thenable

def 解开(值):#可等待则等待否则原样
    """可等待则等待，否则原样返回。"""
    if _是否thenable(值):#可等待
        return _等待(值)#等待
    return 值#同步值

class 中止信号:#可监听的取消通道
    """对应 AbortSignal。"""
    def __init__(自身,已中止旗=False):#创建一条取消通道
        """创建一条取消通道。"""
        自身.aborted=已中止旗#英文旗标
        自身.已中止=已中止旗#中文旗标
        自身.reason=None#英文原因
        自身.原因=None#中文原因
        自身._监听=[]#回调表
        自身._锁=threading.Lock()#并发锁
    def 触发(自身,原因=None):#标记中止并通知
        """标记中止并通知。"""
        with 自身._锁:#只触发一次
            if 自身.aborted:#已经中止
                return#忽略
            自身.aborted=True#英文旗标
            自身.已中止=True#中文旗标
            自身.reason=原因#英文原因
            自身.原因=原因#中文原因
            回调们=list(自身._监听)#拷贝
            自身._监听=[]#清空
        for 回调,_一次 in 回调们:#逐个通知
            回调()#通知
    def addEventListener(自身,事件名,回调,选项=None):#登记 abort 回调
        """登记 abort 回调。"""
        if 事件名!='abort':#只支持 abort
            return#忽略其它事件
        立刻=False#是否已中止
        一次=bool(isinstance(选项,dict) and 选项.get('once'))#once
        with 自身._锁:#回调表锁
            if 自身.aborted:#已经中止
                立刻=True#锁外调用
            else:#仍活着
                自身._监听.append((回调,一次))#登记
        if 立刻:#立刻通知
            回调()#通知
    def removeEventListener(自身,事件名,回调,选项=None):#去掉 abort 回调
        """去掉 abort 回调。"""
        if 事件名!='abort':#只支持 abort
            return#忽略
        with 自身._锁:#按引用删除
            自身._监听=[项 for 项 in 自身._监听 if 项[0] is not 回调]#按引用删除

class 中止控制器:#发出中止的控制器
    """对应 AbortController。"""
    def __init__(自身):#创建配套信号
        """创建配套信号。"""
        自身.信号=中止信号()#本控制器的信号
        自身.signal=自身.信号#AbortController 协议
    def abort(自身,原因=None):#AbortController.abort
        """中止配套信号。"""
        自身.信号.触发(原因)#触发一次
    def 中止(自身,原因=None):#中文别名
        """中文别名。"""
        自身.abort(原因)#委托

class 队列端口:#同进程队列消息端口
    """把双向队列收成 MessagePort 形态，供会话与宿主共用。"""
    def __init__(自身,入队,出队,关闭旗):#绑定队列
        """绑定入队/出队与关闭旗。"""
        自身._入=入队#收到的消息
        自身._出=出队#发出的消息
        自身._关闭=关闭旗#关闭旗
        自身._处理=None#message 回调
        自身._泵=None#泵线程
    def postMessage(自身,消息):#投递一条消息
        """投递一条消息。"""
        if 自身._关闭.is_set():#已关闭
            return#无处可投
        自身._出.put(消息)#入出队
    def on(自身,事件,回调):#登记事件回调
        """登记 message 回调并启动泵。"""
        if 事件!='message':#只支持 message
            return#忽略
        自身._处理=回调#记住回调
        def 泵():#后台读入队
            """后台读入队直到关闭。"""
            while not 自身._关闭.is_set():#未关闭
                try:#带超时取消息
                    消息=自身._入.get(timeout=0.05)#取一条
                except queue.Empty:#暂时没有
                    continue#再试
                if 消息 is None:#毒丸
                    break#结束
                if 自身._处理 is not None:#有回调
                    try:#分发
                        自身._处理(消息)#调用
                    except Exception:#回调失败不得杀死泵
                        pass#收容
        自身._泵=threading.Thread(target=泵)#泵线程
        自身._泵.daemon=True#不挡住退出
        自身._泵.start()#启动

class 线程工人:#对齐 node:worker_threads.Worker 的最小宿主面
    """拉起跑工人会话的守护线程，并经队列交换协议消息。"""
    def __init__(自身,初始化):#按初始化拉起
        """按初始化拉起。"""
        自身._到工人=queue.Queue()#宿主→工人
        自身._到宿主=queue.Queue()#工人→宿主
        自身._关闭=threading.Event()#关闭旗
        自身._消息回调=None#message 回调
        自身._错误回调=None#error 回调
        自身._退出回调=None#exit 回调
        自身._初始化=初始化#保存初始化（工人线程使用）
        自身._线程=threading.Thread(target=自身._主循环)#工人线程
        自身._线程.daemon=True#不挡住退出
        自身._泵=threading.Thread(target=自身._宿主泵)#宿主侧读泵
        自身._泵.daemon=True#不挡住退出
        自身._线程.start()#启动工人
        自身._泵.start()#启动宿主泵
    def _主循环(自身):#工人线程主体
        """在工人线程跑会话。"""
        端口=队列端口(自身._到工人,自身._到宿主,自身._关闭)#工人侧端口
        码=0#退出码
        try:#跑会话
            跑工人会话(端口,自身._初始化)#驱动会话
        except Exception as 错误:#工人失败
            码=1#非零退出
            if 自身._错误回调 is not None:#有错误回调
                try:#通知
                    自身._错误回调(错误)#回调
                except Exception:#回调失败
                    pass#收容
        finally:#无论如何退出
            自身._关闭.set()#关闭
            自身._到宿主.put(None)#毒丸结束宿主泵
            if 自身._退出回调 is not None:#有退出回调
                try:#通知
                    自身._退出回调(码)#回调
                except Exception:#回调失败
                    pass#收容
    def _宿主泵(自身):#宿主侧读工人消息
        """宿主侧读工人消息直到关闭。"""
        while True:#直到毒丸
            消息=自身._到宿主.get()#阻塞取
            if 消息 is None:#毒丸
                break#结束
            if 自身._消息回调 is not None:#有回调
                try:#分发
                    自身._消息回调(消息)#调用
                except Exception:#回调失败
                    pass#收容
    def on(自身,事件,回调):#登记事件回调
        """登记 message/error/exit/messageerror 回调。"""
        if 事件=='message':#消息
            自身._消息回调=回调#记住
        elif 事件=='error':#错误
            自身._错误回调=回调#记住
        elif 事件=='exit':#退出
            自身._退出回调=回调#记住
        elif 事件=='messageerror':#反序列化失败
            pass#本端口只传普通 dict，无独立 messageerror 源
    def postMessage(自身,消息):#向工人投递
        """向工人投递一条消息。"""
        if 自身._关闭.is_set():#已关闭
            raise Exception('worker is gone')#投递失败
        自身._到工人.put(消息)#入队
    def terminate(自身):#终止工人
        """终止工人线程（协作：关闭旗 + 毒丸）。"""
        完成=操作任务()#终止任务
        def 收尾():#后台等待
            """置关闭并等待线程结束。"""
            自身._关闭.set()#关闭
            自身._到工人.put(None)#毒丸结束工人泵
            自身._到宿主.put(None)#毒丸结束宿主泵
            if 自身._线程.is_alive() and threading.current_thread() is not 自身._线程:#不能 join 自己
                自身._线程.join(timeout=1.0)#有界等待
            完成.兑现(None)#兑现
        线程=threading.Thread(target=收尾)#后台
        线程.daemon=True#不挡住退出
        线程.start()#启动
        return 完成#返回承诺

def 工人启动环境(平台=None,tsconfig路径=None):#构造清洗后的 worker 环境
    """清洗后的 worker 环境：无环境凭证、无 loader 标志。Windows 必须显式注入临时目录。未构建形态还会转发 TSX_TSCONFIG_PATH。"""
    if 平台 is None:#默认当前平台
        平台=os.name#nt 或 posix
    环境={}#从空环境开始
    if 平台=='nt' or 平台=='win32':#Windows 必须显式注入临时目录
        临时=tempfile.gettempdir()#取宿主真实临时路径
        环境['TMP']=临时#写入 TMP
        环境['TEMP']=临时#写入 TEMP
    if tsconfig路径 is not None:#未构建时转发 tsconfig 钉
        环境['TSX_TSCONFIG_PATH']=tsconfig路径#写入
    return 环境#返回清洗后的环境

class 子记录:#已发布子运行记录
    """一条已发布的子运行及其共享的静止期销毁事务。"""
    def __init__(自身,运行):#绑定运行句柄
        """绑定运行句柄。"""
        自身.run=运行#子智能体运行句柄
        自身.disposal=None#进行中的销毁承诺

class 工人运行(工作流运行):#宿主侧一次工作流运行
    """一次活着的 worker 引擎运行——能力缝的工作流运行，由 start() 直接返回。拥有工人、子运行登记表和结果结算；result 永不拒绝。"""
    def __init__(自身,上下文,子智能体,标识,元数据,父智能体,初始化,提供方,销毁宽限毫秒,观察者,信号):#构造一次宿主侧运行
        """构造一次宿主侧运行。"""
        自身.ctx=上下文#插件上下文
        自身.上下文=上下文#中文别名
        自身.subagents=子智能体#子智能体运行时
        自身.子智能体=子智能体#中文别名
        自身.id=标识#运行标识
        自身.meta=元数据#工作流身份
        自身.parent=父智能体#父智能体
        自身.父=父智能体#中文别名
        自身.provider=提供方#子智能体提供方名
        自身.提供方=提供方#中文别名
        自身.disposeGraceMs=销毁宽限毫秒#销毁宽限毫秒
        自身.销毁宽限毫秒=销毁宽限毫秒#中文别名
        自身.observer=观察者#执行观察者
        自身.观察者=观察者#中文别名
        自身.result=操作任务()#运行结果任务
        自身.结果=自身.result#中文别名
        自身._settled=False#是否已经结算
        自身._terminalClaimed=False#终态是否已被占用
        自身._workerDeathObserved=False#是否已观察到 worker 死亡
        自身._cancelReason=None#取消原因，先到者获胜
        自身._graceTimer=None#取消宽限线程
        自身._workerGone=False#线程是否已退出
        自身._hostStarted=0#宿主已接受的启动子次数
        自身._children={}#已发布子运行表
        自身._pendingStarts=set()#进行中的启动子事务
        自身._liveAgents={}#未配对的开始账本
        自身._quiescenceWaiters=[]#等待子运行静止的回调
        自身._controller=中止控制器()#共享中止控制器
        自身._inputSignal=None#外部启动信号
        自身._inputSignalAbort=None#装在外部信号上的回调
        自身._disposed=None#公开销毁事务
        自身._锁=threading.Lock()#状态锁
        自身.worker=线程工人(初始化)#拉起工作线程
        自身.工人=自身.worker#中文别名
        自身.worker.on('message',自身._收消息)#分发 worker 消息
        自身.worker.on('error',lambda 错误: 自身._工人死亡('workflow worker failed: '+渲染抛出(错误),False))#错误视为死亡
        自身.worker.on('exit',lambda 码: 自身._退出(码))#线程退出
        if 信号 is not None and (取字段(信号,'aborted') is True or 取字段(信号,'已中止') is True):#启动时信号已中止
            自身.取消('workflow start signal already aborted')#立即取消
        elif 信号 is not None:#有尚未中止的外部信号
            def 外部中止():#外部中止回调
                """外部中止回调。"""
                自身._卸外部信号()#先卸掉监听，避免重入
                自身.取消('workflow signal aborted')#再取消运行
            自身._inputSignal=信号#记住外部信号
            自身._inputSignalAbort=外部中止#记住精确回调
            if hasattr(信号,'addEventListener'):#可监听
                信号.addEventListener('abort',外部中止,{'once':True})#只监听一次中止

    def _退出(自身,码):#线程退出
        """标记线程已不在并按退出码结算死亡。"""
        自身._workerGone=True#标记线程已不在
        自身._工人死亡('workflow worker exited before the run settled (exit code '+str(码)+')',True)#按退出码结算死亡

    def 取消(自身,原因=None):#取消本次运行
        """取消本次运行：告知 worker，中止每个子启动共用的必需信号，并启动宽限定时器。幂等；第一条原因获胜。"""
        with 自身._锁:#检查可否取消
            if 自身._settled or 自身._terminalClaimed or 自身._cancelReason is not None:#已结算、已占终态或已取消则忽略
                return#忽略
            自身._cancelReason=原因 if 原因 is not None else 'workflow cancelled'#先到的原因获胜
        自身._投递(宿主到工人类型.取消,{'reason':自身._cancelReason})#通知 worker 取消
        自身._中止子们(自身._cancelReason)#中止共享子信号
        def 宽限到期():#宽限到期后强制收尾
            """宽限到期后强制收尾。"""
            time.sleep(自身.disposeGraceMs/1000.0)#按配置宽限
            with 自身._锁:#占用终态
                自身._terminalClaimed=True#占用终态
            自身._结束搁浅智能体()#合成缺失的结束事件
            自身._结算结果(自身._取消结果(自身._hostStarted))#强制结算为取消
            解开(自身.worker.terminate())#终止工作线程
        宽限=threading.Thread(target=宽限到期)#宽限线程
        宽限.daemon=True#不阻止进程退出
        自身._graceTimer=宽限#记住
        宽限.start()#启动

    def 销毁(自身):#销毁本次运行
        """取消 + 有界结算 + 终止。幂等；每条路径都安全。"""
        if 自身._disposed is not None:#已有销毁事务则加入
            return 自身._disposed#返回同一份
        公开=操作任务()#公开销毁的结算器
        自身._disposed=公开#对外暴露同一份事务
        def 主体():#销毁事务主体
            """销毁事务主体。"""
            try:#主体
                自身._卸外部信号()#卸掉外部启动信号
                自身.取消('workflow disposed')#走取消路径
                自身._收割子们('workflow disposed')#立即收割已登记子运行
                截止=time.time()+自身.disposeGraceMs/1000.0#宽限截止
                while time.time()<截止:#结果静止与宽限竞速
                    if 自身._settled and 自身._已静止():#已结算且静止
                        break#结束等待
                    time.sleep(0.02)#短睡
                解开(自身.worker.terminate())#无条件终止线程
                自身._收割子们('workflow disposed')#终止后再收割残留
                公开.兑现(None)#销毁成功
            except Exception as 错误:#销毁失败
                公开.拒绝(错误)#拒绝
        线程=threading.Thread(target=主体)#后台
        线程.daemon=True#不挡住退出
        线程.start()#启动
        return 自身._disposed#返回同一份销毁承诺

    def _投递(自身,类型,载荷):#向 worker 发消息
        """向 worker 投递一条消息（载荷按标签查表），容忍线程已经不在。"""
        if 自身._workerGone or 自身._workerDeathObserved:#线程已不在或死亡后不再投递
            return#忽略
        try:#尝试投递
            消息={'type':类型}#标签
            消息.update(载荷)#附带载荷
            自身.worker.postMessage(消息)#发送
        except Exception as 错误:#投递抛错
            自身.ctx.logger.warn('workflow-worker-thread: postMessage failed: '+渲染抛出(错误))#记录投递失败

    def _收消息(自身,消息):#分发一条 worker 消息
        """分发一条 worker 消息。"""
        if 自身._workerDeathObserved:#死亡后拒绝准入
            return#忽略
        类型=消息.get('type') if isinstance(消息,dict) else None#消息类型
        if 类型==工人到宿主类型.就绪:#worker 已就绪
            自身._投递(宿主到工人类型.开始,{})#允许脚本开始
            return#结束就绪分支
        if 类型==工人到宿主类型.阶段:#阶段叙述
            if 自身._cancelReason is None:#未取消才转发阶段
                自身.observer.phase(消息.get('title'))#转发
            return#结束阶段分支
        if 类型==工人到宿主类型.日志:#日志叙述
            if 自身._cancelReason is None:#未取消才转发日志
                自身.observer.log(消息.get('message'))#转发
            return#结束日志分支
        if 类型==工人到宿主类型.智能体开始:#智能体开始
            信息=消息.get('info')#开始信息
            自身._liveAgents[取字段(信息,'seq')]=信息#记入未配对账本
            自身.observer.agentStart(信息)#转发给观察者
            return#结束开始分支
        if 类型==工人到宿主类型.智能体结束:#智能体结束
            自身._结束智能体(消息.get('info'))#经配对门转发结束
            return#结束结束分支
        if 类型==工人到宿主类型.子启动:#请求启动子运行
            自身._子启动(消息.get('callId'),消息.get('request'))#处理启动子请求
            return#结束启动子分支
        if 类型==工人到宿主类型.子销毁:#请求销毁子运行
            自身._子销毁(消息.get('callId'))#处理销毁请求
            return#结束销毁分支
        if 类型==工人到宿主类型.结果:#脚本结果
            自身._收结果(消息.get('result'))#处理运行结果
            return#结束结果分支
        断言永不(消息,'worker-to-host message')#未知消息类型失败

    def _子准入失败(自身):#查询子准入失败原因
        """一份就绪的提供方结果为何不再允许进入 worker。"""
        if 自身._cancelReason is not None:#运行已取消
            return {'reason':自身._cancelReason,'rendered':'workflow run cancelled: '+自身._cancelReason}#返回取消原因
        if 自身._workerDeathObserved:#worker 已死亡
            return {'reason':'workflow worker gone','rendered':'workflow worker is no longer available'}#返回 worker 不可用
        if 自身._terminalClaimed:#终态已被占用
            return {'reason':'workflow settled','rendered':'workflow run already settled'}#返回已结算
        return None#仍允许准入

    def _子启动(自身,调用号,请求):#处理一条启动子请求
        """处理一条启动子请求。"""
        初始失败=自身._子准入失败()#先查当前准入
        if 初始失败 is not None:#终态边界之后拒绝
            自身._投递(宿主到工人类型.子启动错误,{'callId':调用号,'rendered':初始失败['rendered']})#回报启动失败
            return#不再启动
        自身._hostStarted+=1#计入已接受的启动子
        任务=操作任务()#启动提供方事务
        自身._pendingStarts.add(任务)#登记进行中的启动
        def 跑():#后台启动
            """启动并发布一个子运行。"""
            try:#启动
                自身._真正启动子(调用号,请求)#启动
                任务.兑现(None)#成功
            except Exception as 错误:#失败
                任务.拒绝(错误)#拒绝
            finally:#退休事务
                自身._pendingStarts.discard(任务)#从进行中集合删除
                自身._通知静止()#可能释放静止等待者
        线程=threading.Thread(target=跑)#后台
        线程.daemon=True#不挡住退出
        线程.start()#启动

    def _真正启动子(自身,调用号,请求):#启动并发布一个子运行
        """等待一次提供方拥有的启动事务，并只在仍被准入时发布。"""
        try:#调用提供方启动
            启动参数={#按提供方名启动子智能体
                'prompt':[{'type':'text','text':请求.get('prompt')}],#把提示打成文本块
                'parent':自身.parent,#归属父智能体
                'signal':自身._controller.signal,#带上本运行的共享中止
            }#结束基础参数
            if 请求.get('schema') is not None:#有模式才传入
                启动参数['outputSchema']=请求['schema']#写入模式
            if 请求.get('provider') is not None or 请求.get('model') is not None:#有覆盖才组装 agentOptions
                选项={}#智能体选项
                if 请求.get('provider') is not None:#可选提供方覆盖
                    选项['provider']=请求['provider']#写入
                if 请求.get('model') is not None:#可选模型覆盖
                    选项['model']=请求['model']#写入
                启动参数['agentOptions']=选项#写入选项
            运行=解开(自身.subagents.启动(自身.provider,启动参数))#调用启动
        except Exception as 错误:#提供方启动失败
            失败=自身._子准入失败()#启动期间可能已关闭准入
            自身._投递(宿主到工人类型.子启动错误,{#回报启动失败
                'callId':调用号,#对应的调用标识
                'rendered':失败['rendered'] if 失败 is not None else 渲染抛出(错误),#优先报准入失败，否则报抛出值
            })#结束失败消息
            return#不发布
        失败=自身._子准入失败()#启动完成后再次检查准入
        if 失败 is not None:#期间关闭了准入
            自身._投递(宿主到工人类型.子启动错误,{'callId':调用号,'rendered':失败['rendered']})#回报不再准入
            try:#丢掉已经拉起的子运行
                解开(运行.dispose() if hasattr(运行,'dispose') else 运行.销毁())#立即销毁
            except Exception as 错误:#销毁失败
                自身.ctx.logger.warn('workflow-worker-thread: refused child dispose failed: '+渲染抛出(错误))#记录拒绝后的销毁失败
            return#不发布
        记录=子记录(运行)#组装已发布记录
        自身._children[调用号]=记录#登记到子运行表
        def 转发():#把子结果编成稍后投递
            """把子结果编成稍后投递。"""
            try:#等待子结果
                结果=解开(取字段(运行,'result'))#子运行兑现
                try:#快照必须能无损跨线程
                    快照对象={'output':取字段(结果,'output'),'stopReason':取字段(结果,'stopReason')}#把子结果打成 JSON 快照
                    结构化=取字段(结果,'structured')#结构化值
                    if 结构化 is not None:#有结构化才带上
                        快照对象['structured']=结构化#写入
                    快照=快照json值(快照对象)#无损快照
                    if 快照 is None:#无法无损序列化则失败
                        raise TypeError('child result is not losslessly JSON-serializable')#失败
                    自身._投递(宿主到工人类型.子已结算,{'callId':调用号,'result':快照})#投递结算
                except Exception as 错误:#快照或序列化失败
                    已渲染='workflow child result could not cross the worker boundary: '+渲染抛出(错误)#跨界失败文案
                    自身._投递(宿主到工人类型.子失败,{'callId':调用号,'rendered':已渲染})#投递失败
            except Exception as 错误:#子运行拒绝
                自身._投递(宿主到工人类型.子失败,{'callId':调用号,'rendered':渲染抛出(错误)})#投递失败
        自身._投递(宿主到工人类型.子已启动,{'callId':调用号,'childId':取字段(运行,'id')})#先发布子句柄
        线程=threading.Thread(target=转发)#再投递结算或失败
        线程.daemon=True#不挡住退出
        线程.start()#启动

    def _子销毁(自身,调用号):#处理 worker 的销毁 RPC
        """处理 worker 的销毁 RPC。"""
        记录=自身._children.get(调用号)#查找已发布记录
        if 记录 is None:#宿主侧已经销毁
            自身._投递(宿主到工人类型.子已销毁,{'callId':调用号})#仍回确认
            return#结束
        def 确认():#销毁后再确认
            """销毁后再确认。"""
            解开(自身._销毁子(调用号,记录))#销毁
            自身._投递(宿主到工人类型.子已销毁,{'callId':调用号})#确认
        线程=threading.Thread(target=确认)#后台
        线程.daemon=True#不挡住退出
        线程.start()#启动

    def _销毁子(自身,调用号,记录):#销毁或加入已有销毁
        """启动（或加入）一个已登记子运行的销毁；登记条目在结算时离开。"""
        if 记录.disposal is not None:#已有事务则加入
            return 记录.disposal#返回同一份
        事务=操作任务()#新销毁事务
        记录.disposal=事务#记住
        def 跑():#后台销毁
            """调用子运行销毁并离表。"""
            try:#销毁
                解开(记录.run.dispose() if hasattr(记录.run,'dispose') else 记录.run.销毁())#调用子运行销毁
            except Exception as 错误:#收容销毁拒绝
                自身.ctx.logger.warn('workflow-worker-thread: child dispose failed: '+渲染抛出(错误))#记录销毁失败
            自身._children.pop(调用号,None)#从登记表删除
            自身._通知静止()#可能释放静止等待者
            事务.兑现(None)#兑现
        线程=threading.Thread(target=跑)#后台
        线程.daemon=True#不挡住退出
        线程.start()#启动
        return 事务#返回同一份销毁承诺

    def _已静止(自身):#是否已静止
        """待启动与已发布子运行是否都已结束。"""
        return len(自身._children)==0 and len(自身._pendingStarts)==0#已静止

    def _通知静止(自身):#检查并释放静止等待者
        """只在待启动与已发布子运行都结束后才释放等待者。"""
        if not 自身._已静止():#仍有工作则继续等
            return#继续等
        等待们=list(自身._quiescenceWaiters)#快照
        自身._quiescenceWaiters.clear()#清空
        for 等待 in 等待们:#唤醒全部等待者
            等待()#唤醒

    def _收割子们(自身,原因):#收割全部已登记子运行
        """中止并销毁每个已登记子运行；销毁被收容，不等待。"""
        自身._中止子们(自身._cancelReason if 自身._cancelReason is not None else 原因)#中止共享信号
        for 调用号,记录 in list(自身._children.items()):#快照后遍历
            自身._销毁子(调用号,记录)#启动或加入销毁，不等待

    def _中止子们(自身,原因):#中止共享子信号
        """中止待启动与已发布子运行共用的那一条规范信号。"""
        if not 自身._controller.signal.aborted:#尚未中止才 abort
            自身._controller.abort(原因)#中止

    def _收结果(自身,结果):#处理 worker 送来的运行结果
        """处理 worker 送来的运行结果。"""
        if 自身._terminalClaimed:#终态已被占用则忽略
            return#忽略
        取消已请求=自身._cancelReason is not None#记录到达时是否已请求取消
        自身._terminalClaimed=True#占用终态
        自身._收割子们('workflow settled')#开始清理子运行
        if not 取消已请求:#到达时没有外部取消
            自身._结算结果(结果)#采用 worker 结果
            return#结束
        停止原因=结果.get('stopReason') if isinstance(结果,dict) else None#停止原因
        if 停止原因!='cancelled':#脚本在取消穿越线程边界时结算
            已开始=结果.get('agentsStarted') if isinstance(结果,dict) else 0#智能体计数
            自身._结算结果(自身._取消结果(已开始))#改报取消
            return#结束
        自身._结算结果(结果)#worker 自己已经报取消

    def _工人死亡(自身,消息,是否退出):#处理 worker 死亡
        """处理 error/messageerror/exit 信号；exit 还做最后一次销毁清扫。"""
        if not 自身._workerDeathObserved:#第一份死亡信号
            自身._workerDeathObserved=True#关闭消息准入
            结局已占=自身._terminalClaimed#死亡到达前终态是否已被占用
            取消已请求=自身._cancelReason is not None#死亡到达前是否已请求取消
            if not 结局已占:#死亡作为终态源时占住
                自身._terminalClaimed=True#占住
            if len(自身._children)>0 or len(自身._pendingStarts)>0:#有残留则收割
                自身._收割子们('workflow worker gone')#收割
            自身._结束搁浅智能体()#合成缺失的结束事件
            if not 结局已占:#死亡赢得终态
                if 取消已请求:#死亡前已请求取消
                    自身._结算结果(自身._取消结果(自身._hostStarted))#报取消
                else:#死亡前未取消
                    自身._结算结果({'value':None,'stopReason':'error','error':消息,'agentsStarted':自身._hostStarted})#报错误
        if not 是否退出:#非 exit 不做物理清扫
            return#结束
        for 调用号,记录 in list(自身._children.items()):#对残留子运行启动销毁
            自身._销毁子(调用号,记录)#启动销毁
        自身._结束搁浅智能体()#exit 清扫时再合成一次

    def _结束智能体(自身,结束):#经配对门转发一次结束
        """唯一的智能体结束发射门：仅当其开始仍在账本里未配对时才转发 end。"""
        序号=取字段(结束,'seq')#取出序号
        if 序号 not in 自身._liveAgents:#已经配对或不在账本则忽略
            return#忽略
        自身._liveAgents.pop(序号,None)#配对离表
        自身.observer.agentEnd(结束)#转发给观察者

    def _结束搁浅智能体(自身):#合成所有搁浅开始的结束
        """为每个已开始但未配对的智能体合成缺失的 agent-end，结局为 cancelled。"""
        for 信息 in list(自身._liveAgents.values()):#快照后遍历未配对账本
            自身._结束智能体({**信息,'outcome':'cancelled'})#按取消结局合成结束

    def _取消结果(自身,已开始):#组装取消结局
        """组装取消结局。"""
        原因=自身._cancelReason if 自身._cancelReason is not None else 'workflow cancelled'#取取消原因
        return {'value':None,'stopReason':'cancelled','error':'workflow run cancelled: '+原因,'agentsStarted':已开始}#返回取消结果

    def _卸外部信号(自身):#卸掉外部启动信号
        """卸掉装在调用方启动信号上的那条精确中止回调。"""
        信号=自身._inputSignal#取出外部信号
        回调=自身._inputSignalAbort#取出精确回调
        if 信号 is None or 回调 is None:#没有安装则忽略
            return#忽略
        自身._inputSignal=None#忘掉信号
        自身._inputSignalAbort=None#忘掉回调
        if hasattr(信号,'removeEventListener'):#可卸掉
            信号.removeEventListener('abort',回调)#卸掉监听

    def _结算结果(自身,结果):#结算运行结果
        """第一次结算获胜；解除宽限定时器并释放调用方信号。"""
        if 自身._settled:#已经结算则忽略
            return#忽略
        自身._terminalClaimed=True#占住终态
        自身._settled=True#标记已结算
        自身._卸外部信号()#卸掉外部信号
        自身.result.兑现(结果)#兑现结果承诺
