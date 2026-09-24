from ..聊天设置 import (
    默认转录视图模式,
    转录视图字段,
    遗留转录视图模式,
    遗留展开转录视图模式,
)

__all__=['转录视图策略']

class 转录视图策略:
    """Chat 与其设置行消费的实时 transcript 偏好。"""

    def __init__(自身,宿主):
        """Host 设置到达前默认为 Standard。"""
        自身._宿主=宿主
        自身._模式=默认转录视图模式
        自身._监听集合=set()
        def 读当前():
            """读当前模式。"""
            return 自身._模式
        自身.mode={
            'getSnapshot':读当前,
            'subscribe':自身._订阅,
            'set':自身._设本地,
        }
        def 宿主发布():
            """设置变更时采纳。"""
            自身._采纳()
        自身._退订=宿主.subscribe(宿主发布)
        自身._采纳()

    def 拆除(自身):
        """释放已接受值订阅。"""
        自身._退订()

    def _订阅(自身,监听):
        """返回退订。"""
        自身._监听集合.add(监听)
        def 退订():
            """取消。"""
            自身._监听集合.discard(监听)
        return 退订

    def _通知(自身):
        """逐个回调。"""
        for 监听 in list(自身._监听集合):
            监听()

    def _设本地(自身,模式):
        """更新快照并通知。"""
        自身._模式=模式
        自身._通知()

    def setMode(自身,模式):
        """发布并持久化一次显式用户选择。"""
        if 自身._模式==模式:
            return
        自身._设本地(模式)
        自身._宿主.set(转录视图字段,模式)

    def _采纳(自身):
        """采纳最新已接受的 Host 段，不写回。遗留值映射为当前模式。"""
        快=自身._宿主.getSnapshot()
        段=快['value'] if 快 is not None and 'value' in 快 else None
        if 段 is None:
            return
        视图=段['transcriptView'] if 'transcriptView' in 段 else None
        if 视图 is None:
            return
        if 视图==遗留转录视图模式:
            模式='standard'
        elif 视图==遗留展开转录视图模式:
            模式='detailed'
        else:
            模式=视图
        if 自身._模式==模式:
            return
        自身._设本地(模式)
