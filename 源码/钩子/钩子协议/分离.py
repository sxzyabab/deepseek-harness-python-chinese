"""跟踪发出型、没有扩展点等待的钩子运行的静止。桥接层跟踪运行及其后续，把跟踪器信号传入执行，并在拆除时排空，使进程或迟到回调不会活过该 fiber。"""
import threading#后台盯落地
from cordis.工具 import 已兑现,是否thenable#立刻兑现与可等待判定

分离运行=dict#一座桥的分离钩子运行登记（运行时为跟踪器对象）

class 中止控制器:#发出中止的控制器
    """对应 AbortController：一对控制器与信号。"""
    def __init__(自身):#创建配套信号
        """创建配套信号。"""
        自身.信号=_中止信号()#本控制器的信号
        自身.signal=自身.信号#AbortController 协议
    def 中止(自身,原因=None):#中止配套信号
        """中止配套信号。"""
        自身.信号.触发(原因)#触发一次
    def abort(自身,原因=None):#AbortController.abort
        """AbortController.abort。"""
        自身.中止(原因)#委托中文入口

class _中止信号:#一次中止信号
    """对应 AbortSignal。"""
    def __init__(自身):#初始未中止
        """初始未中止。"""
        自身.aborted=False#AbortSignal 协议旗标
        自身.已中止=False#中文旗标
        自身.reason=None#AbortSignal 协议原因
        自身.原因=None#中文原因
    def 触发(自身,原因=None):#触发一次中止
        """触发一次中止。"""
        if 自身.aborted:#已中止
            return#幂等
        自身.aborted=True#AbortSignal 协议旗标
        自身.已中止=True#中文旗标
        自身.reason=原因#AbortSignal 协议原因
        自身.原因=原因#中文原因

class _分离跟踪器:#一座桥的分离钩子运行登记
    """在飞登记；接线方式见模块文档。"""
    def __init__(自身):#创建空登记
        """创建空登记与中止控制器。"""
        自身._在飞=set()#在飞的运行链
        自身._控制器=中止控制器()#排空时中止仍在跑的钩子
        自身.signal=自身._控制器.signal#交给 runHook 的中止信号
        自身.信号=自身.signal#中文别名
    def 登记(自身,运行):#登记一条分离链直到落地
        """登记一条分离运行直到落地。传入整条链——钩子运行及其后续/错误处理。"""
        自身._在飞.add(运行)#记入在飞集合
        def 落地(*_参数):#落地后从集合删掉
            """落地后从集合删掉。"""
            自身._在飞.discard(运行)#剔除
        if 是否thenable(运行):#可等待则后台盯落地（避免阻塞调用方）
            def 盯():#等待结算
                """等待结算后清登记。"""
                try:#成功失败都清登记
                    运行.等待()#阻塞到落地
                except BaseException:#拒绝也算落地
                    pass#吸收，记账在此
                落地()#清登记
            工作=threading.Thread(target=盯)#后台线程
            工作.daemon=True#不挡住退出
            工作.start()#启动
        else:#非 thenable 立刻落地
            落地()#清登记
    def 排空(自身):#中止并等到全部落地
        """中止信号，然后等到每条已跟踪链都落地——包括排空进行中新登记的链。"""
        自身._控制器.中止(Exception('hook bridge disposed'))#拆桥时杀掉仍在跑的钩子
        while len(自身._在飞)>0:#还有在飞就再等一波
            快照=list(自身._在飞)#当前快照
            for 链 in 快照:#逐条等待
                if not 是否thenable(链):#非 thenable
                    自身._在飞.discard(链)#直接剔除
                    continue#下一条
                try:#等当前快照落地
                    链.等待()#阻塞
                except BaseException:#拒绝也算落地
                    pass#allSettled 语义
        return 已兑现()#全部落地后兑现

def 创建分离运行():#创建分离运行跟踪器
    """创建分离运行跟踪器（每个桥的 apply() 一个）；已落地的运行会被剔除，避免长会话堆积。"""
    return _分离跟踪器()#跟踪器对象
