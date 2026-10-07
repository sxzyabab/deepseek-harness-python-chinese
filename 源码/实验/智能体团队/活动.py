import threading
from ...基础设施.js特性 import PromiseEX as 期约#等待结果
from .生命周期 import 已中止
from .异常 import 团队错误

__all__=['团队活动']

class 团队活动:
    '拥有当前 Team 变更等待者，每个最多释放一次'
    def __init__(自身):
        '空等待表'
        自身._等待者={}
        自身._已关闭=False

    def 等待(自身,标识,超时毫秒,信号):
        '等待一次之后的 Team 域或成员状态变化。返回期约，兑现值是 {timedOut}'
        if (not isinstance(超时毫秒,int) or isinstance(超时毫秒,bool)
                or 超时毫秒<10_000 or 超时毫秒>3_600_000):
            raise 团队错误('timeoutMs 必须是 10000 到 3600000 的整数','TEAM_INVALID_TIMEOUT')
        if 已中止(信号):
            raise 团队错误('wait_agent 已中止','TEAM_WAIT_ABORTED')
        if 自身._已关闭:#运行时已关闭，不再等待
            已关闭结果=期约()#直接给出结果
            已关闭结果.解决({'timedOut':False})#未超时
            return 已关闭结果
        变化结果=期约()#等到变化兑现 True，超时兑现 False，取消则拒绝
        结算锁=threading.Lock()#超时、取消与通知可能并发，只允许一路结算
        已结算=False#是否已有一路结算
        等待集=自身._等待者[标识] if 标识 in 自身._等待者 else None
        if 等待集 is None:
            等待集=set()
            自身._等待者[标识]=等待集
        停止听=threading.Event()#通知取消盯梢线程收尾
        def 收尾(结算动作,结算值):
            '只结算一次：撤销定时器与盯梢、摘掉等待者，再用结算动作结算变化结果'
            nonlocal 已结算#标记已有一路结算
            with 结算锁:#并发只放行第一路
                if 已结算:
                    return
                已结算=True
            定时器.cancel()
            停止听.set()
            等待集.discard(唤醒)
            if len(等待集)==0:
                自身._等待者.pop(标识,None)
            结算动作(结算值)#解决或拒绝变化结果
        def 取消处理():
            '信号置位：以取消错误拒绝'
            收尾(变化结果.拒绝,团队错误('wait_agent 已中止','TEAM_WAIT_ABORTED'))
        def 唤醒():
            '变化通知：以已变化兑现'
            收尾(变化结果.解决,True)
        def 超时结算():
            '超时：以未变化兑现'
            收尾(变化结果.解决,False)
        定时器=threading.Timer(超时毫秒/1000,超时结算)#先建定时器，收尾才能撤销它
        定时器.daemon=True
        定时器.start()
        等待集.add(唤醒)#定时器就绪后才对通知可见
        def 监视中止():
            '信号置位则取消'
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
        def 转成等待结果(已变化):#变化结果结算后
            '把是否变化转成等待结果'
            return {'timedOut':not 已变化}
        return 变化结果.然后(转成等待结果)#等变化、超时或取消

    def 通知(自身,标识):
        '唤醒并移除一个团队的当前全部等待者'
        等待集=自身._等待者[标识] if 标识 in 自身._等待者 else None
        if 等待集 is None:
            return
        自身._等待者.pop(标识,None)
        for 唤醒 in list(等待集):
            唤醒()

    def 关闭(自身):
        '关闭准入，并在运行时拆除期间唤醒全部当前等待者'
        自身._已关闭=True
        for 等待集 in list(自身._等待者.values()):
            for 唤醒 in list(等待集):
                唤醒()
        自身._等待者.clear()
