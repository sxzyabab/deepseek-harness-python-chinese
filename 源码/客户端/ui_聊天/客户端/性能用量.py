from ...存储 import 创建快照存储
from ..聊天设置 import 默认性能用量

__all__=['性能用量策略']


class 性能用量策略:
    '性能与用量档位。选择立刻生效，并与宿主已接受的设置对齐'
    def __init__(自身,宿主):
        '先订已接受值，再采纳当前快照'
        自身.宿主=宿主
        自身.mode=创建快照存储(默认性能用量)

        def 采纳():
            '宿主已接受的档位写回本地。没有值就保持现状'
            快照=宿主.getSnapshot()
            值=快照['value'] if isinstance(快照,dict) else None
            已接受=值['performanceUsage'] if isinstance(值,dict) else None
            if 已接受 is not None:
                自身.mode.set(已接受)

        自身.退订=宿主.subscribe(采纳)
        采纳()

    def dispose(自身):
        '拆掉已接受值的订阅'
        自身.退订()

    def setMode(自身,模式):
        '立刻公布选择，并把宿主写入排进队列'
        if 模式==自身.mode.getSnapshot():
            return
        自身.mode.set(模式)
        自身.宿主.set('performanceUsage',模式)
