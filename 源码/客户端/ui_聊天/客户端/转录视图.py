from ...存储 import 创建快照存储
from ..聊天设置 import (
    折叠时机字段,
    默认折叠时机,
    默认转录视图模式,
    遗留转录视图模式,
    遗留展开转录视图模式,
    转录视图字段,
)

__all__=['转录视图策略']


class 转录视图策略:
    '工作步骤展示和收起时机。两份都落在同一份宿主设置上'
    def __init__(自身,宿主,默认模式=默认转录视图模式):
        '先有客户端默认，再采纳宿主已经接受的值'
        自身.宿主=宿主
        自身.默认模式=默认模式
        自身.mode=创建快照存储(默认模式)
        自身.collapseTiming=创建快照存储(默认折叠时机)
        自身.退订=宿主.subscribe(自身.采纳)
        自身.采纳()

    def dispose(自身):
        '拆掉已接受值的订阅'
        自身.退订()

    def setMode(自身,模式):
        '公布并持久化用户选的展示档'
        if 自身.mode.getSnapshot()==模式:
            return
        自身.mode.set(模式)
        自身.宿主.set(转录视图字段,模式)

    def setCollapseTiming(自身,时机):
        '公布并持久化收起时机，不改展示档'
        if 自身.collapseTiming.getSnapshot()==时机:
            return
        自身.collapseTiming.set(时机)
        自身.宿主.set(折叠时机字段,时机)

    def 采纳(自身):
        '把最新已接受的宿主分区读进来，不写回去'
        快照=自身.宿主.getSnapshot()
        分区=快照['value'] if isinstance(快照,dict) else None
        if 分区 is None:
            return
        已存=分区.get('transcriptView') if isinstance(分区,dict) else None
        if 已存==遗留转录视图模式 or 已存==遗留展开转录视图模式:
            模式='detailed'
        elif 已存 is None:
            模式=自身.默认模式
        else:
            模式=已存
        if 自身.mode.getSnapshot()!=模式:
            自身.mode.set(模式)
        时机=分区.get('collapseTiming') if isinstance(分区,dict) else None
        if 时机 is None:
            时机=默认折叠时机
        if 自身.collapseTiming.getSnapshot()!=时机:
            自身.collapseTiming.set(时机)
