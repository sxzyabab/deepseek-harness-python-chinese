from ...工具.超时 import 已中止
import threading,time

__all__=['输出等待者','休眠']

class 输出等待者:
    """唤醒旗：等待之间到达的唤醒不会丢失。"""
    def __init__(自身):
        """空旗。"""
        自身._脏=False
        自身._事件=threading.Event()

    def 唤醒(自身):
        """记下一次唤醒。"""
        自身._脏=True
        自身._事件.set()

    def 等待(自身,信号):
        """下一唤醒、已有唤醒或中止时返回。"""
        if 自身._脏 or 已中止(信号):
            自身._脏=False
            自身._事件.clear()
            return
        while True:
            if 已中止(信号) or 自身._脏:
                自身._脏=False
                自身._事件.clear()
                return
            自身._事件.wait(0.05)

def 休眠(毫秒,信号):
    """合并窗口睡眠；中止则立刻返回。"""
    if 已中止(信号):
        return
    截止点=time.time()+毫秒/1000.0
    while not 已中止(信号):
        剩余=截止点-time.time()
        if 剩余<=0:
            return
        time.sleep(min(剩余,0.05))
