"""订阅 + 批通知原语（Session 与 SessionManager 共用）。

对齐上游 `runtime/src/client/sessions/notifier.ts`。公开面仅中文名。
语义：N 次标脏收成一次微任务 flush，N 次标帧脏收成一次动画帧 flush；
flush 在通知之前重建快照缓存。没有监听器时跳过重建，只立脏位；
下一次确保新鲜惰性重建。新鲜度与通知是分开的两位。
"""
import threading#微任务近似

__all__=['通知器']#仅中文公开名

class 通知器:#订阅 + 批通知原语
    """Session 与 SessionManager 共用的订阅与批通知。"""

    def __init__(自身,重建):#拥有方注入快照重建
        """记下重建函数。"""
        自身._重建=重建#写入拥有方 snapshotCache
        自身._监听们=set()#订阅者
        自身._脏=False#快照是否过期
        自身._待通知=False#是否还有未发出的通知
        自身._排期='none'#none / microtask / frame
        自身._排期世代=0#作废过期回调

    def 订阅(自身,监听器):#uSES 订阅入口
        """登记监听器，返回取消函数。"""
        自身._监听们.add(监听器)#加入集
        def 取消():#取消订阅
            """从表删除。"""
            自身._监听们.discard(监听器)#删除
        return 取消#退订

    def 标脏(自身):#状态变更入口
        """标脏并排期微任务批 flush。"""
        自身._脏=True#快照过期
        自身._待通知=True#还要通知
        if 自身._排期=='microtask':#已有微任务排期
            return#幂等
        自身._排期一次('microtask')#排微任务

    def 标帧脏(自身):#流变更入口
        """标脏，每帧最多发布一次累计状态。"""
        自身._脏=True#快照过期
        自身._待通知=True#还要通知
        if 自身._排期!='none':#已有任一排期
            return#幂等
        窗口=globals()#浏览器全局
        有帧=callable(窗口.get('requestAnimationFrame'))#有 rAF
        自身._排期一次('frame' if 有帧 else 'microtask')#有 rAF 用帧，否则微任务

    def 立刻通知(自身):#同步 flush
        """本拍立刻重建并通知（受控输入同拍）。"""
        自身._脏=True#快照过期
        自身._待通知=True#还要通知
        自身._作废排期()#作废已排期回调
        自身._冲刷()#本拍 flush

    def 确保新鲜(自身):#getSnapshot 前检查
        """脏时同步重建；通知保持挂起。"""
        if not 自身._脏:#已新
            return#跳过
        自身._脏=False#清脏
        自身._重建()#重建缓存，不发通知

    def _排期一次(自身,种类):#排一次 flush
        """记下种类并挂回调。"""
        自身._排期世代+=1#新世代
        世代=自身._排期世代#闭包世代
        自身._排期=种类#记下种类
        def 发布():#到期回调
            """世代仍有效则冲刷。"""
            if 世代!=自身._排期世代:#已被作废
                return#丢弃
            自身._排期='none'#清排期
            自身._冲刷()#真正 flush
        if 种类=='frame':#动画帧
            globals()['requestAnimationFrame'](发布)#下一帧
        else:#微任务
            threading.Timer(0,发布).start()#近似 queueMicrotask

    def _作废排期(自身):#作废已排期回调
        """抬世代并清排期标记。"""
        自身._排期世代+=1#抬世代
        自身._排期='none'#无排期

    def _冲刷(自身):#重建并通知
        """有待通知且有监听器时重建后扇出。"""
        if not 自身._待通知:#没有待通知
            return#跳过
        if len(自身._监听们)==0:#无人观察：脏位留给下次确保新鲜
            return#惰性
        自身._待通知=False#清待通知
        if 自身._脏:#快照过期
            自身._脏=False#清脏
            自身._重建()#先重建
        for 监听 in list(自身._监听们):#再通知
            监听()#回调
