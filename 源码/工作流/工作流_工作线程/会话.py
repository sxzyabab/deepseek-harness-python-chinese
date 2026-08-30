"""引擎的 worker 侧半边：跑工人会话把一条消息端口接到一次工作流执行——钩子进度和子启动作为消息发出，运行控制与子生命周期从对面回来——并恰好投递一次运行终态结果。与 worker 入口分开，好让单元测试经同进程队列驱动会话。

会话先宣告就绪再等 go，因此与启动竞速的取消连脚本的同步前缀都能挡住。用取消代替 go 会放开闸门进入已取消的 drive，且不执行正文。
"""
import threading#消息泵线程
from concurrent.futures import Future as _原生Future#单次操作结果
from ...模型后端.llm import 断言永不#穷尽检查
from .协议 import 宿主到工人类型,工人到宿主类型#双向消息标签
from .领域 import 渲染抛出#抛出值渲染
from .运行时 import 工作流执行#worker 侧执行

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

class 待处理子:#飞行中的子 RPC 条目
    """一次飞行中的子 RPC 簿记（按 callId 索引）。"""
    def __init__(自身):#建三份承诺
        """建启动/结算/销毁三份承诺。"""
        自身.started=操作任务()#启动兑现子标识
        自身.启动=自身.started#中文别名
        自身.settled=操作任务()#结算兑现子结果
        自身.结算=自身.settled#中文别名
        自身.disposed=操作任务()#销毁确认
        自身.销毁确认=自身.disposed#中文别名

class 远程过程调用子句柄:#worker 侧子句柄
    """一个已启动子智能体的 worker 侧句柄：每个成员都是按本次 callId 键控的到宿主的 RPC。"""
    def __init__(自身,投递,调用号,条目,标识):#绑定一次子 RPC
        """绑定一次子 RPC。"""
        自身._post=投递#投递函数
        自身._callId=调用号#本次调用标识
        自身._entry=条目#对应簿记
        自身.id=标识#宿主发布的子标识
        自身.result=条目.settled#结果来自结算承诺

    def dispose(自身):#请求宿主销毁此子运行
        """请求宿主销毁此子运行。"""
        自身._post(工人到宿主类型.子销毁,{'callId':自身._callId})#发出销毁 RPC
        return 自身._entry.disposed#等待宿主确认

    def 销毁(自身):#中文别名
        """中文别名。"""
        return 自身.dispose()#委托

class 子远程过程调用桥:#子 RPC 桥
    """worker 侧子 RPC 桥：分配 callId，投递启动/销毁 RPC，并拥有会话消息处理经 onChild* 入口结算的按次待处理簿记。"""
    def __init__(自身,投递):#记住投递函数
        """记住投递函数。"""
        自身._post=投递#投递函数
        自身._nextCallId=0#下一个调用标识
        自身._pending={}#飞行中的 RPC 表

    def startAgent(自身,请求):#向宿主请求启动子运行
        """向宿主请求启动子运行。"""
        自身._nextCallId+=1#分配新的调用标识
        调用号=自身._nextCallId#本次调用标识
        条目=待处理子()#为本调用建簿记
        # 收容：异步提供方启动失败（或运行被拆除）时，结算承诺可能永远没有消费方——
        # 不得浮成未处理拒绝并杀死 worker。
        def 盯():#吞掉未处理拒绝
            """已消费：启动失败后无人等待的子结算。"""
            try:#等待
                条目.settled.等待()#等待结算
            except BaseException:#拒绝也算消费
                pass#吞掉
        线程=threading.Thread(target=盯)#后台观察
        线程.daemon=True#不挡住退出
        线程.start()#启动
        自身._pending[调用号]=条目#登记飞行中的 RPC
        自身._post(工人到宿主类型.子启动,{'callId':调用号,'request':请求})#发出启动 RPC
        子标识=条目.started.等待()#等待宿主发布
        return 远程过程调用子句柄(自身._post,调用号,条目,子标识)#返回绑定后的句柄

    def 启动子(自身,请求):#中文别名
        """中文别名。"""
        return 自身.startAgent(请求)#委托

    def onChildStarted(自身,调用号,子标识):#处理 ChildStarted
        """宿主已建立已发布子运行；放开 startAgent 的等待。"""
        条目=自身._pending.get(调用号)#取出簿记
        if 条目 is not None:#有条目
            条目.started.兑现(子标识)#兑现启动子标识

    def onChildStartError(自身,调用号,已渲染):#处理启动失败
        """异步提供方启动失败；拒绝并退休这条待处理 RPC。"""
        条目=自身._pending.pop(调用号,None)#取出并退休
        if 条目 is not None:#有条目
            条目.started.拒绝(Exception(已渲染))#拒绝启动等待

    def onChildSettled(自身,调用号,结果):#处理子结算
        """子运行的终态结果已到达。"""
        条目=自身._pending.get(调用号)#取出簿记
        if 条目 is not None:#有条目
            条目.settled.兑现(结果)#兑现子结果

    def onChildFailed(自身,调用号,已渲染):#处理子失败
        """子运行的 result 在宿主侧拒绝（基础设施故障，按致命错误转发）。"""
        条目=自身._pending.get(调用号)#取出簿记
        if 条目 is not None:#有条目
            条目.settled.拒绝(Exception(已渲染))#拒绝子结果

    def onChildDisposed(自身,调用号):#处理销毁确认
        """宿主确认了销毁；本次调用的簿记完成。"""
        条目=自身._pending.pop(调用号,None)#取出并退休
        if 条目 is not None:#有条目
            条目.disposed.兑现(None)#兑现销毁等待

def 要求父端口(端口):#要求真实父端口
    """收窄引导读到的可空父端口。主线程加载则失败。"""
    if 端口 is None:#无端口
        raise Exception('the workflow worker entry must be loaded inside a worker thread (no parentPort)')#主线程加载则失败
    return 端口#返回非空端口

def 跑工人会话(端口,初始化):#驱动一次 worker 会话
    """针对 port 把一份工作流脚本跑到结算，恰好投递一次终态结果消息；在那次投递之后兑现。永不拒绝：构造失败变成错误结果。"""
    def 投递(类型,载荷):#按标签向宿主投递
        """把标签与载荷打成一条消息。"""
        消息={'type':类型}#标签
        消息.update(载荷)#附带载荷
        端口.postMessage(消息)#发送

    子们=子远程过程调用桥(投递)#本会话的子 RPC 桥

    class _观察者:#把进度观察转成宿主消息
        """执行观察者实现。"""
        def phase(自身,标题):#转发阶段
            """转发阶段。"""
            投递(工人到宿主类型.阶段,{'title':标题})#转发阶段
        def log(自身,消息):#转发日志
            """转发日志。"""
            投递(工人到宿主类型.日志,{'message':消息})#转发日志
        def agentStart(自身,信息):#转发智能体开始
            """转发智能体开始。"""
            投递(工人到宿主类型.智能体开始,{'info':信息})#转发
        def agentEnd(自身,信息):#转发智能体结束
            """转发智能体结束。"""
            投递(工人到宿主类型.智能体结束,{'info':信息})#转发

    观察者=_观察者()#本会话观察者
    try:#构造执行（编译失败会抛）
        参数=初始化.get('args') if isinstance(初始化,dict) else getattr(初始化,'args',None)#取出 args
        执行=工作流执行(#按初始化载荷构造
            初始化['meta'] if isinstance(初始化,dict) else 初始化.meta,#meta
            初始化['body'] if isinstance(初始化,dict) else 初始化.body,#body
            参数,#args
            初始化['limits'] if isinstance(初始化,dict) else 初始化.limits,#limits
            观察者,#observer
            子们,#children
        )#结束构造
    except Exception as 错误:#构造失败
        投递(工人到宿主类型.结果,{'result':{'value':None,'stopReason':'error','error':渲染抛出(错误),'agentsStarted':0}})#直接报错误结果
        return#不再等待 go

    闸门=操作任务()#等待 go 或取消的闸门

    def 处理消息(消息):#分发宿主消息
        """按宿主消息类型分发。"""
        类型=消息.get('type') if isinstance(消息,dict) else getattr(消息,'type',None)#消息类型
        if 类型==宿主到工人类型.开始:#允许脚本开始
            闸门.兑现(None)#放开闸门
            return#结束 go 分支
        if 类型==宿主到工人类型.取消:#取消运行
            原因=消息.get('reason') if isinstance(消息,dict) else getattr(消息,'reason','')#取消原因
            执行.取消(原因)#标记执行为取消
            # 取消同时放开闸门：drive() 在跑正文前检查取消状态，因此脚本根本不会执行。
            闸门.兑现(None)#放开闸门进入已取消的 drive
            return#结束取消分支
        if 类型==宿主到工人类型.子已启动:#子运行已发布
            子们.onChildStarted(消息.get('callId'),消息.get('childId'))#兑现启动等待
            return#结束已启动分支
        if 类型==宿主到工人类型.子启动错误:#子启动失败
            子们.onChildStartError(消息.get('callId'),消息.get('rendered'))#拒绝启动等待
            return#结束启动失败分支
        if 类型==宿主到工人类型.子已结算:#子运行已结算
            子们.onChildSettled(消息.get('callId'),消息.get('result'))#兑现子结果
            return#结束子结算分支
        if 类型==宿主到工人类型.子失败:#子结果拒绝
            子们.onChildFailed(消息.get('callId'),消息.get('rendered'))#拒绝子结果
            return#结束子失败分支
        if 类型==宿主到工人类型.子已销毁:#销毁已确认
            子们.onChildDisposed(消息.get('callId'))#兑现销毁等待
            return#结束销毁确认分支
        断言永不(消息,'host-to-worker message')#未知消息类型失败

    端口.on('message',处理消息)#分发宿主消息
    投递(工人到宿主类型.就绪,{})#宣告就绪
    闸门.等待()#等待 go 或取消
    结果=执行.驱动()#驱动脚本直到结算
    投递(工人到宿主类型.结果,{'result':结果})#恰好投递一次终态结果
