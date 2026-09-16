from threading import Event as 同步事件,Thread as 线程#中止广播与后台线程
from .错误 import 团队错误#领域错误

__all__=['团队运行时生命周期','已中止','若已中止则抛出','合成中止']#仅中文公开名

def 已中止(信号):#信号是否已中止
    """信号是否已中止；信号是 threading.Event。"""
    if 信号 is None:#无信号
        return False#未中止
    return 信号.is_set()#事件置位

def 若已中止则抛出(信号):#已中止则抛
    """已中止则抛出领域拆除错误。"""
    if not 已中止(信号):#仍活
        return#返回
    raise 团队错误('Agent Teams service disposed','TEAM_DISPOSED')#拆除错误

def 合成中止(*信号列表):#任一置位则融合置位
    """把多路 Event 合成一路；空参得到永不置位的事件。"""
    有效=[信号 for 信号 in 信号列表 if 信号 is not None]#去掉缺席
    if len(有效)==0:#全缺席
        return 同步事件()#永不置位
    if len(有效)==1:#单路
        return 有效[0]#原样
    融合=同步事件()#融合事件
    def 等待源置位(源):#一路置位则融合置位
        """阻塞到源置位后置位融合。"""
        源.wait()#等源
        融合.set()#融合置位
    for 源 in 有效:#先扫已置位
        if 源.is_set():#已中止
            融合.set()#立刻胜出
            return 融合#已中止的融合
        线程(target=等待源置位,args=(源,),daemon=True).start()#转发中止
    return 融合#融合事件

def 等待飞行条目列表(条目列表):#并发等全部飞行落定
    """线程扇出等待各飞行条目，收集 fulfilled 与 rejected。"""
    结局列表=[None]*len(条目列表)#结果槽
    def 等待一路写入(下标,条目):#等待一路写入槽
        """等待一路写入槽。"""
        条目['完成'].wait()#等落定
        错误=条目['错误']#失败
        if 错误 is not None:#失败
            结局列表[下标]={'status':'rejected','reason':错误}#失败
        else:#成功
            结局列表[下标]={'status':'fulfilled'}#成功
    线程表=[]#工作线程
    for 下标,条目 in enumerate(条目列表):#每路一线程
        工作=线程(target=等待一路写入,args=(下标,条目),daemon=True)#工作线程
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
        自身._事件=同步事件()#中止事件

    @property#只读
    def 信号(自身):#取消信号
        """恰好在 Team 运行时准入关闭时被中止的事件。"""
        return 自身._事件#中止事件

    @property#只读
    def 已拆除(自身):#是否已拆除
        """Team 运行时准入是否已关闭。"""
        return 自身._事件.is_set()#事件置位

    def _是否取消(自身,原因):#是否取消
        """失败是否为运行时取消，直接或经 __cause__ 链。"""
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

    def 结算(自身,条目列表,失败列表):#结算飞行
        """等待已准入飞行，并保留除运行时取消以外的失败。"""
        if len(条目列表)==0:#无事可做
            return#返回
        def 收集():#有界结算体
            """并发结算全部飞行条目。"""
            return 等待飞行条目列表(条目列表)#扇出等待
        try:#结算
            结局列表=自身.有界等待(收集)#有界结算
            for 结局 in 结局列表:#遍历结果
                if 结局['status']=='rejected' and not 自身._是否取消(结局['reason']):#非取消失败
                    失败列表.append(结局['reason'])#收集
        except 团队错误 as 错误:#超时
            失败列表.append(错误)#收集

    def 有界等待(自身,动作):#有界等待
        """为一次运行时结算动作设界；动作是无参可调用。"""
        完成=同步事件()#完成门
        盒={'值':None,'错误':None}#结果盒
        def 执行并结算():#后台执行动作
            """执行动作并写入结果盒。"""
            try:#试跑
                盒['值']=动作()#成功
            except Exception as 错误:#拆除动作体什么都可能抛，契约未定所以收不窄
                盒['错误']=错误#失败
            finally:#无论成败
                完成.set()#放行
        线程(target=执行并结算,daemon=True).start()#动作线程
        if not 完成.wait(自身._拆除超时毫秒/1000):#超时未完成
            raise 团队错误(#超时
                'Agent Teams runtime disposal exceeded '+str(自身._拆除超时毫秒)+'ms',#文案
                'TEAM_DISPOSAL_TIMEOUT',#错误码
            )#抛出
        if 盒['错误'] is not None:#失败
            raise 盒['错误']#原样抛
        return 盒['值']#成功值
