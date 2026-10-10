from threading import Event as 同步事件,Thread as 线程,Timer as 定时器
from ...基础设施.js特性 import PromiseEX as 期约#结算与有界等待的异步结果
from .异常 import 团队错误

__all__=['团队运行时生命周期','已中止','若已中止则抛出','合成中止']

def 已中止(信号):
    '信号是否已中止；信号是 threading.Event'
    if 信号 is None:
        return False
    return 信号.is_set()

def 若已中止则抛出(信号):
    '已中止则抛出领域拆除错误'
    if not 已中止(信号):
        return
    raise 团队错误('Agent Teams service disposed','TEAM_DISPOSED')

def 合成中止(*信号列表):
    '把多路 Event 合成一路；空参得到永不置位的事件'
    有效=[信号 for 信号 in 信号列表 if 信号 is not None]
    if len(有效)==0:
        return 同步事件()
    if len(有效)==1:
        return 有效[0]
    融合=同步事件()
    def 等待源置位(源):
        '阻塞到源置位后置位融合'
        源.wait()
        融合.set()
    for 源 in 有效:
        if 源.is_set():
            融合.set()
            return 融合
        线程(target=等待源置位,args=(源,),daemon=True).start()
    return 融合

class 团队运行时生命周期:
    '拥有唯一的 Team 运行时取消事实与拆除超时'
    def __init__(自身,拆除超时毫秒):
        '记录拆除超时'
        自身._拆除超时毫秒=拆除超时毫秒
        自身._事件=同步事件()
        自身._操作=set()#已准入、尚未结算的期约

    @property
    def 信号(自身):
        '恰好在 Team 运行时准入关闭时被中止的事件'
        return 自身._事件

    @property
    def 已拆除(自身):
        'Team 运行时准入是否已关闭'
        return 自身._事件.is_set()

    def _是否取消(自身,原因):
        '失败是否为运行时取消，直接或经 __cause__ 链'
        已见=set()
        当前=原因
        while 当前 is not None and id(当前) not in 已见:
            if isinstance(当前,团队错误) and 当前.code=='TEAM_DISPOSED':
                return True
            if not isinstance(当前,BaseException):
                return False
            已见.add(id(当前))
            当前=当前.__cause__
        return False

    def 关闭(自身):
        '关闭 Team 运行时准入并取消已准入的可中断工作'
        自身._事件.set()

    def 跟踪(自身,操作):
        '记下一次已准入的发送或创建，直到它结算。返回同一个期约'
        自身._操作.add(操作)#计入
        def 摘掉(_值=None):
            '结算后移出待定集合'
            自身._操作.discard(操作)#摘掉
        操作.然后(摘掉,摘掉)#成败都摘
        return 操作#原期约

    def 待定(自身):
        '关闭准入之后仍在等的已准入工作'
        return list(自身._操作)#快照

    def 结算(自身,操作列表,失败列表):
        '等待已准入操作，并保留除运行时取消以外的失败。操作列表是期约列表；返回期约，失败追加到失败列表'
        if len(操作列表)==0:#没有已准入操作
            无操作结果=期约()#无事可等
            无操作结果.解决(None)#视为已结算
            return 无操作结果
        def 收集失败(结算表):#全部结算后
            '收集各操作的失败；运行时取消不算失败'
            for 操作 in 操作列表:#逐个操作
                if 操作.状态=='rejected' and not 自身._是否取消(操作.数据):#被拒且不是运行时取消
                    失败列表.append(操作.数据)#记下失败原因
        def 记录等待失败(错误):#等待超时或收集出错
            '等待本身失败也计入失败列表'
            失败列表.append(错误)#记下
        return 自身.有界等待(期约.全部已结算(操作列表)).然后(收集失败).捕获(记录等待失败)#全部结算后统一收集

    def 有界等待(自身,操作):
        '为一次运行时结算操作设界；操作是期约。返回期约，超过拆除超时则拒绝'
        超时=期约()#超时到期时拒绝
        def 到期():#计时到期
            '拒绝超时'
            超时.拒绝(团队错误(f'Agent Teams 运行时拆除超过 {自身._拆除超时毫秒}ms','TEAM_DISPOSAL_TIMEOUT'))#超时错误
        计时=定时器(自身._拆除超时毫秒/1000,到期)#拆除超时计时器
        计时.daemon=True#不阻止进程退出
        计时.start()#开始计时
        return 期约.竞速([操作,超时]).最终(计时.cancel)#无论谁先结算都撤销计时
