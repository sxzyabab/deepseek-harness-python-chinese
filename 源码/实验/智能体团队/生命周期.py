import threading#定时器与事件
from concurrent.futures import Future as 原生结果#单次操作结果
from .错误 import 团队错误#领域错误

__all__=['团队运行时生命周期','操作任务','已中止','若已中止则抛出','合成中止']#仅中文公开名

class 操作任务:#单次操作结果
    """单次操作的 Future 包装，只暴露 等待。"""
    def __init__(自身):#构造未决任务
        """构造未决任务。"""
        自身._future=原生结果()#底层 Future

    def 兑现(自身,值=None):#成功结算
        """成功结算。"""
        if not 自身._future.done():#尚未结算
            自身._future.set_result(值)#写入结果
        return 值#返回兑现值

    def 拒绝(自身,错误):#失败结算
        """失败结算。"""
        if not 自身._future.done():#尚未结算
            自身._future.set_exception(错误)#原样拒绝

    def 等待(自身,超时=None):#阻塞等待
        """阻塞等到结算。"""
        return 自身._future.result(timeout=超时)#取结果或抛错

def 已中止(信号):#信号是否已中止
    """信号是否已中止；信号是 threading.Event。"""
    if 信号 is None:#无信号
        return False#未中止
    return 信号.is_set()#事件置位

def 若已中止则抛出(信号):#已中止则抛
    """已中止则抛出领域拆除错误。"""
    if not 已中止(信号):#仍活
        return#返回
    raise 团队错误('Agent Teams service disposed','TEAM_DISPOSED')#拆除拒绝

def 合成中止(*信号列表):#任一置位则融合置位
    """把多路 Event 合成一路；空参得到永不置位的事件。"""
    有效=[信号 for 信号 in 信号列表 if 信号 is not None]#去掉缺席
    if len(有效)==0:#全缺席
        return threading.Event()#永不置位
    if len(有效)==1:#单路
        return 有效[0]#原样
    融合=threading.Event()#融合事件
    def 等待源置位(源):#一路置位则融合置位
        """阻塞到源置位后置位融合。"""
        源.wait()#等源
        融合.set()#融合置位
    for 源 in 有效:#先扫已置位
        if 源.is_set():#已中止
            融合.set()#立刻胜出
            return 融合#已中止的融合
        threading.Thread(target=等待源置位,args=(源,),daemon=True).start()#转发中止
    return 融合#融合事件

def 赛跑(*任务列表):#最先结算的那路胜出
    """最先结算的那路胜出。"""
    门=threading.Event()#完成门
    盒={'value':None,'error':None,'done':False}#结果盒
    锁=threading.Lock()#只结算一次
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
    def 等待一路结算(任务):#等待一路
        """等待一路并尝试胜出。"""
        try:#试跑
            结算成功(任务.等待())#成功
        except Exception as 错误:#等待的操作任务可能抛任意业务错误，契约未定所以收不窄
            结算失败(错误)#失败
    for 任务 in 任务列表:#每路一线程
        threading.Thread(target=等待一路结算,args=(任务,),daemon=True).start()#等待线程
    门.wait()#等胜出
    if 盒['error'] is not None:#失败
        raise 盒['error']#抛出
    return 盒['value']#成功值

def 全部结算(操作列表):#并发等全部落定
    """并发等全部落定，收集 fulfilled 与 rejected。"""
    结局列表=[None]*len(操作列表)#结果槽
    def 等待一路写入(下标,操作):#等待一路写入槽
        """等待一路写入槽。"""
        try:#试跑
            操作.等待()#等待
            结局列表[下标]={'status':'fulfilled'}#成功
        except Exception as 错误:#等待的操作任务可能抛任意业务错误，契约未定所以收不窄
            结局列表[下标]={'status':'rejected','reason':错误}#失败
    线程表=[]#工作线程
    for 下标,操作 in enumerate(操作列表):#每路一线程
        工作=threading.Thread(target=等待一路写入,args=(下标,操作),daemon=True)#工作线程
        工作.start()#启动
        线程表.append(工作)#登记
    for 工作 in 线程表:#等全部结束
        工作.join()#等到结束
    return 结局列表#全部

class 团队运行时生命周期:#运行时生命周期
    """拥有唯一的 Team 运行时取消事实与拆除超时。"""
    def __init__(自身,拆除超时毫秒):#构造
        """记录拆除超时。"""
        自身._拆除超时毫秒=拆除超时毫秒#超时毫秒
        自身._事件=threading.Event()#中止事件

    @property#只读
    def 信号(自身):#取消信号
        """恰好在 Team 运行时准入关闭时被中止的事件。"""
        return 自身._事件#中止事件

    @property#只读
    def 已拆除(自身):#是否已拆除
        """Team 运行时准入是否已关闭。"""
        return 自身._事件.is_set()#事件置位

    def _是否取消(自身,原因):#是否取消
        """拒绝是否为运行时取消，直接或经 __cause__ 链。"""
        已见=set()#防环
        当前=原因#当前节点
        while 当前 is not None and id(当前) not in 已见:#沿链
            if isinstance(当前,团队错误) and 当前.code=='TEAM_DISPOSED':#拆除错误码
                return True#是取消
            if not isinstance(当前,BaseException):#非异常断链
                return False#否
            已见.add(id(当前))#记已见
            当前=当前.__cause__#Python 链
        return False#环则否

    def 关闭(自身):#关闭准入
        """关闭 Team 运行时准入并取消已准入的可中断工作。"""
        自身._事件.set()#置位

    def 结算(自身,操作列表,失败列表):#结算操作
        """等待已准入操作，并保留除运行时取消以外的失败。"""
        if len(操作列表)==0:#无事可做
            return#返回
        def 收集():#有界结算体
            """并发结算全部操作。"""
            return 全部结算(操作列表)#allSettled
        try:#结算
            结局列表=自身.有界等待(收集)#有界 allSettled
            for 结局 in 结局列表:#遍历结果
                if 结局['status']=='rejected' and not 自身._是否取消(结局['reason']):#非取消失败
                    失败列表.append(结局['reason'])#收集
        except 团队错误 as 错误:#超时
            失败列表.append(错误)#收集

    def 有界等待(自身,动作):#有界等待
        """为一次运行时结算动作设界；动作是无参可调用。"""
        超时任务=操作任务()#超时拒绝
        def 到期():#定时拒绝
            """超时拒绝。"""
            超时任务.拒绝(团队错误(#超时拒绝
                'Agent Teams runtime disposal exceeded '+str(自身._拆除超时毫秒)+'ms',#文案
                'TEAM_DISPOSAL_TIMEOUT',#错误码
            ))#拒绝结束
        定时器=threading.Timer(自身._拆除超时毫秒/1000,到期)#定时器
        定时器.daemon=True#守护
        定时器.start()#启动
        工作=操作任务()#动作任务
        def 执行并结算():#后台执行动作
            """执行动作并结算。"""
            try:#试跑
                工作.兑现(动作())#成功
            except Exception as 错误:#拆除动作体什么都可能抛，契约未定所以收不窄
                工作.拒绝(错误)#失败
        threading.Thread(target=执行并结算,daemon=True).start()#动作线程
        try:#竞速
            return 赛跑(工作,超时任务)#竞速
        finally:#收尾
            定时器.cancel()#清定时器
