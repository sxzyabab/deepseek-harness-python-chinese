"""Team 运行时的共享准入截止与有界结算。

对齐上游 `agent-team/src/lifecycle.ts`。公开面仅中文名。
"""
import threading#定时器
from ...内核.智能体循环.辅助 import 解开,操作任务#等待与任务
from .错误 import 团队错误#领域错误

__all__=['团队运行时生命周期']#仅中文公开名

class 团队运行时生命周期:#运行时生命周期
    """拥有唯一的 Team 运行时取消事实与处置超时。"""
    def __init__(自身,处置超时毫秒):#构造
        """记录处置超时。"""
        自身._处置超时毫秒=处置超时毫秒#超时毫秒
        自身._控制器=_中止控制器()#取消控制器

    @property#只读
    def signal(自身):#取消信号
        """恰好在 Team 运行时准入关闭时被中止的信号。"""
        return 自身._控制器.信号#控制器信号

    @property#只读
    def 信号(自身):#中文别名
        """取消信号中文别名。"""
        return 自身.signal#同信号

    @property#只读
    def disposed(自身):#是否已处置
        """Team 运行时准入是否已关闭。"""
        return 自身.信号.已中止#看信号

    @property#只读
    def 已处置(自身):#中文别名
        """已处置中文别名。"""
        return 自身.disposed#同旗标

    @property#只读
    def reason(自身):#取消原因
        """用于区分预期处置拒绝的确切取消原因。"""
        return 自身.信号.原因#原样返回

    @property#只读
    def 原因(自身):#中文别名
        """取消原因中文别名。"""
        return 自身.reason#同原因

    def _是否取消(自身,原因):#是否取消
        """拒绝是否为运行时取消，直接或经 Error cause 链。"""
        已见=set()#防环
        当前=原因#当前节点
        while 当前 is not None and id(当前) not in 已见:#沿链
            if 自身.已处置 and 当前 is 自身.原因:#同一原因
                return True#是取消
            if 自身.已处置 and isinstance(当前,团队错误) and 当前.code=='TEAM_DISPOSED':#处置错误码
                return True#是取消
            if not isinstance(当前,BaseException):#非异常断链
                return False#否
            已见.add(id(当前))#记已见
            下一=getattr(当前,'cause',None)#TS cause
            if 下一 is None:#无 TS cause
                下一=getattr(当前,'__cause__',None)#Python 链
            当前=下一#前进
        return False#环则否

    def 关闭(自身):#关闭准入
        """关闭 Team 运行时准入并取消已准入的可中断工作。"""
        自身._控制器.中止(团队错误('Agent Teams service disposed','TEAM_DISPOSED'))#带领域原因

    def 结算(自身,操作们,失败们):#结算操作
        """等待已准入操作，并保留除运行时取消以外的失败。"""
        if len(操作们)==0:#无事可做
            return#返回
        try:#结算
            结局们=自身.有界等待(_全部结算(操作们))#有界 allSettled
            for 结局 in 结局们:#遍历结果
                if 结局['status']=='rejected' and not 自身._是否取消(结局['reason']):#非取消失败
                    失败们.append(结局['reason'])#收集
        except Exception as 错误:#超时等
            失败们.append(错误)#收集

    def 有界等待(自身,操作):#有界等待
        """为一次运行时结算操作设界。"""
        超时任务=操作任务()#超时拒绝
        def 到期():#定时拒绝
            """超时拒绝。"""
            超时任务.拒绝(团队错误(#超时拒绝
                'Agent Teams runtime disposal exceeded '+str(自身._处置超时毫秒)+'ms',#文案
                'TEAM_DISPOSAL_TIMEOUT',#错误码
            ))#拒绝结束
        定时器=threading.Timer(自身._处置超时毫秒/1000,到期)#定时器
        定时器.daemon=True#守护
        定时器.start()#启动
        try:#竞速
            return _竞速(操作,超时任务)#竞速
        finally:#收尾
            定时器.cancel()#清定时器

class _中止控制器:#本地 AbortController
    """对应 AbortController。"""
    def __init__(自身):#构造
        """一对控制器与信号。"""
        自身._事件=threading.Event()#中止事件
        自身._原因=None#中止原因
        自身.信号=_中止信号(自身)#对外信号

    def 中止(自身,原因=None):#发出中止
        """发出中止；重复调用忽略。"""
        if 自身._事件.is_set():#已中止
            return#忽略
        自身._原因=原因#记下原因
        自身._事件.set()#置位

class _中止信号:#本地 AbortSignal
    """对应 AbortSignal。"""
    def __init__(自身,控制器):#绑控制器
        """绑到控制器。"""
        自身._控制器=控制器#控制器

    @property#只读
    def 已中止(自身):#是否已中止
        """是否已经中止。"""
        return 自身._控制器._事件.is_set()#事件

    @property#只读
    def aborted(自身):#英文别名
        """已中止英文别名。"""
        return 自身.已中止#同旗标

    @property#只读
    def 原因(自身):#中止原因
        """中止原因。"""
        return 自身._控制器._原因#原因

    @property#只读
    def reason(自身):#英文别名
        """原因英文别名。"""
        return 自身.原因#同原因

    def throwIfAborted(自身):#已中止则抛
        """对齐 AbortSignal.throwIfAborted。"""
        if not 自身.已中止:#仍活
            return#返回
        原因=自身.原因#原因
        if isinstance(原因,BaseException):#已是异常
            raise 原因#原样抛
        raise 团队错误('Agent Teams service disposed','TEAM_DISPOSED')#包装

def _全部结算(操作们):#Promise.allSettled
    """结算全部操作，收集 fulfilled/rejected。"""
    结局们=[]#结果表
    for 操作 in 操作们:#逐个
        try:#试跑
            解开(操作)#等待
            结局们.append({'status':'fulfilled'})#成功
        except Exception as 错误:#失败
            结局们.append({'status':'rejected','reason':错误})#失败
    return 结局们#全部

def _竞速(操作,超时任务):#Promise.race
    """操作与超时竞速。"""
    门=threading.Event()#完成门
    盒={'value':None,'error':None,'done':False}#结果盒
    锁=threading.Lock()#竞态锁
    def 结算成功(值):#成功
        """只记一次成功。"""
        with 锁:#竞态
            if 盒['done']:#已结算
                return#忽略
            盒['done']=True#标记
            盒['value']=值#记下
        门.set()#放行
    def 结算失败(错误):#失败
        """只记一次失败。"""
        with 锁:#竞态
            if 盒['done']:#已结算
                return#忽略
            盒['done']=True#标记
            盒['error']=错误#记下
        门.set()#放行
    def 跑操作():#后台跑操作
        """等待操作。"""
        try:#试跑
            结算成功(解开(操作))#成功
        except Exception as 错误:#失败
            结算失败(错误)#失败
    def 跑超时():#后台跑超时
        """等待超时任务。"""
        try:#试跑
            解开(超时任务)#超时会拒绝
            结算成功(None)#不应到达
        except Exception as 错误:#超时
            结算失败(错误)#失败
    threading.Thread(target=跑操作,daemon=True).start()#操作线程
    threading.Thread(target=跑超时,daemon=True).start()#超时线程
    门.wait()#等胜出
    if 盒['error'] is not None:#失败
        raise 盒['error']#抛出
    return 盒['value']#成功值
