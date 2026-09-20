import threading
from .生命周期 import 已中止
from .错误 import 团队错误

__all__=['团队活动']

class 团队活动:
    """拥有当前 Team 变更等待者，每个最多释放一次。"""
    def __init__(自身):
        """空等待表。"""
        自身._等待者={}
        自身._已关闭=False

    def 等待(自身,标识,超时毫秒,信号):
        """等待一次之后的 Team 域或成员状态变化。"""
        if (not isinstance(超时毫秒,int) or isinstance(超时毫秒,bool)
                or 超时毫秒<10_000 or 超时毫秒>3_600_000):
            raise 团队错误('timeoutMs 必须是 10000 到 3600000 的整数','TEAM_INVALID_TIMEOUT')
        if 已中止(信号):
            raise 团队错误('wait_agent 已中止','TEAM_WAIT_ABORTED')
        if 自身._已关闭:
            return {'timedOut':False}
        门=threading.Event()
        结果盒={'changed':None,'error':None}
        结算锁=threading.Lock()
        已结算=[False]
        等待集=自身._等待者[标识] if 标识 in 自身._等待者 else None
        if 等待集 is None:
            等待集=set()
            自身._等待者[标识]=等待集
        停止听=threading.Event()
        def 收尾(结算):
            """只结算一次。"""
            with 结算锁:
                if 已结算[0]:
                    return
                已结算[0]=True
            定时器.cancel()
            停止听.set()
            等待集.discard(唤醒)
            if len(等待集)==0:
                自身._等待者.pop(标识,None)
            结算()
            门.set()
        def 取消结算():
            """包装取消。"""
            结果盒['error']=团队错误('wait_agent 已中止','TEAM_WAIT_ABORTED')
        def 取消处理():
            """收尾并拒绝。"""
            收尾(取消结算)
        def 已变化结算():
            """记下已变化。"""
            结果盒['changed']=True
        def 唤醒():
            """变化结算。"""
            收尾(已变化结算)
        def 未变化结算():
            """记下未变化。"""
            结果盒['changed']=False
        def 超时结算():
            """超时结算。"""
            收尾(未变化结算)
        等待集.add(唤醒)
        定时器=threading.Timer(超时毫秒/1000,超时结算)
        定时器.daemon=True
        定时器.start()
        def 监视中止():
            """信号置位则取消。"""
            if 信号 is None:
                return
            while not 停止听.is_set():
                if 信号.is_set():
                    取消处理()
                    return
                停止听.wait(0.05)
        if 信号 is not None:
            threading.Thread(target=监视中止,daemon=True).start()
            if 信号.is_set():
                取消处理()
        门.wait()
        if 结果盒['error'] is not None:
            raise 结果盒['error']
        return {'timedOut':not 结果盒['changed']}

    def 通知(自身,标识):
        """唤醒并移除一个团队的当前全部等待者。"""
        等待集=自身._等待者[标识] if 标识 in 自身._等待者 else None
        if 等待集 is None:
            return
        自身._等待者.pop(标识,None)
        for 唤醒 in list(等待集):
            唤醒()

    def 关闭(自身):
        """关闭准入，并在运行时拆除期间唤醒全部当前等待者。"""
        自身._已关闭=True
        for 等待集 in list(自身._等待者.values()):
            for 唤醒 in list(等待集):
                唤醒()
        自身._等待者.clear()
