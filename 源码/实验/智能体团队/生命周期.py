from threading import Event as 同步事件,Thread as 线程
from .错误 import 团队错误

__all__=['团队运行时生命周期','已中止','若已中止则抛出','合成中止']

def 已中止(信号):
    """信号是否已中止；信号是 threading.Event。"""
    if 信号 is None:
        return False
    return 信号.is_set()

def 若已中止则抛出(信号):
    """已中止则抛出领域拆除错误。"""
    if not 已中止(信号):
        return
    raise 团队错误('Agent Teams service disposed','TEAM_DISPOSED')

def 合成中止(*信号列表):
    """把多路 Event 合成一路；空参得到永不置位的事件。"""
    有效=[信号 for 信号 in 信号列表 if 信号 is not None]
    if len(有效)==0:
        return 同步事件()
    if len(有效)==1:
        return 有效[0]
    融合=同步事件()
    def 等待源置位(源):
        """阻塞到源置位后置位融合。"""
        源.wait()
        融合.set()
    for 源 in 有效:
        if 源.is_set():
            融合.set()
            return 融合
        线程(target=等待源置位,args=(源,),daemon=True).start()
    return 融合

def 等待飞行条目列表(条目列表):
    """线程扇出等待各飞行条目，收集 fulfilled 与 rejected。"""
    结局列表=[None]*len(条目列表)
    def 等待一路写入(下标,条目):
        """等待一路写入槽。"""
        条目['完成'].wait()
        错误=条目['错误']
        if 错误 is not None:
            结局列表[下标]={'status':'rejected','reason':错误}
        else:
            结局列表[下标]={'status':'fulfilled'}
    线程表=[]
    for 下标,条目 in enumerate(条目列表):
        工作=线程(target=等待一路写入,args=(下标,条目),daemon=True)
        工作.start()
        线程表.append(工作)
    for 工作 in 线程表:
        工作.join()
    return 结局列表

class 团队运行时生命周期:
    """拥有唯一的 Team 运行时取消事实与拆除超时。"""
    def __init__(自身,拆除超时毫秒):
        """记录拆除超时。"""
        自身._拆除超时毫秒=拆除超时毫秒
        自身._事件=同步事件()

    @property
    def 信号(自身):
        """恰好在 Team 运行时准入关闭时被中止的事件。"""
        return 自身._事件

    @property
    def 已拆除(自身):
        """Team 运行时准入是否已关闭。"""
        return 自身._事件.is_set()

    def _是否取消(自身,原因):
        """失败是否为运行时取消，直接或经 __cause__ 链。"""
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
        """关闭 Team 运行时准入并取消已准入的可中断工作。"""
        自身._事件.set()

    def 结算(自身,条目列表,失败列表):
        """等待已准入飞行，并保留除运行时取消以外的失败。"""
        if len(条目列表)==0:
            return
        def 收集():
            """并发结算全部飞行条目。"""
            return 等待飞行条目列表(条目列表)
        try:
            结局列表=自身.有界等待(收集)
            for 结局 in 结局列表:
                if 结局['status']=='rejected' and not 自身._是否取消(结局['reason']):
                    失败列表.append(结局['reason'])
        except 团队错误 as 错误:
            失败列表.append(错误)

    def 有界等待(自身,动作):
        """为一次运行时结算动作设界；动作是无参可调用。"""
        完成=同步事件()
        盒={'值':None,'错误':None}
        def 执行并结算():
            """执行动作并写入结果盒。"""
            try:
                盒['值']=动作()
            except Exception as 错误:#拆除动作体什么都可能抛，契约未定所以收不窄
                盒['错误']=错误
            finally:
                完成.set()
        线程(target=执行并结算,daemon=True).start()
        if not 完成.wait(自身._拆除超时毫秒/1000):
            raise 团队错误(
                'Agent Teams runtime disposal exceeded '+str(自身._拆除超时毫秒)+'ms',
                'TEAM_DISPOSAL_TIMEOUT',
            )
        if 盒['错误'] is not None:
            raise 盒['错误']
        return 盒['值']
