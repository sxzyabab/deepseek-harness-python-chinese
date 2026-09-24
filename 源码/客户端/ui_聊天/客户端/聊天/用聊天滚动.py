from .用聊天导航 import 用聊天导航
from .用聊天读取 import 用聊天读取
from .用聊天视口 import 用聊天视口

__all__=['用聊天滚动']

class 聊天滚动席位:
    """提交后协调滚动策略；新提交输入覆盖待采样读者。"""
    def __init__(自身,输入):
        """输入为 dict。"""
        视口面=用聊天视口()
        自身.视口=视口面['viewport']
        自身.列表引用=视口面['listRef']
        自身.列引用=视口面['columnRef']
        已加载=输入['loadedTurns']
        末回合=已加载[-1]['turn'] if len(已加载)>0 else None
        读取面=用聊天读取(自身.视口,输入['chatScroll'],末回合)
        自身.读取=读取面['reading']
        自身.状态=读取面['state']
        导航输入={
            'firstSeq':输入['firstSeq'],
            'loadingOlder':输入['loadingOlder'],
            'hasMore':输入['hasMore'],
            'loadOlder':输入['loadOlder'],
            'loadThrough':输入['loadThrough'],
        }
        导航面=用聊天导航(自身.视口,自身.读取,导航输入)
        自身.导航=导航面['navigation']
        自身.忙回合=导航面['busyTurn']
        自身.内容={'input':输入,'applied':None,'opened':False}
        自身.已连=False

    def 连接(自身):
        """接视口与读取。"""
        if 自身.已连:
            return
        def 滚动结束():
            """滚动结束。"""
            自身.读取.滚动结束()
            自身.导航.读者已结算()
        def 交互():
            """取消导航。"""
            自身.导航.取消()
        def 尺寸():
            """布局变化。"""
            if not 自身.导航.内容已提交():
                自身.读取.尺寸变化()
            自身.导航.对齐()
        自身.拆视口=自身.视口.连接({
            'scroll':自身.读取.滚动,
            'scrollEnd':滚动结束,
            'interact':交互,
            'resize':尺寸,
        })
        def 采样(样本):
            """已结算阅读观察。"""
            自身.导航.读者已采样(样本)
            自身.处理内容()
        自身.拆读取=自身.读取.连接(采样)
        自身.已连=True

    def 拆除(自身):
        """断开并重开。"""
        if not 自身.已连:
            return
        自身.拆视口()
        自身.拆读取()
        自身.内容['opened']=False
        自身.内容['applied']=None
        自身.已连=False

    def 处理内容(自身):
        """内容提交后的滚动所有权。"""
        当前=自身.内容['input']
        先前=自身.内容['applied']
        自有输入=((当前['lastIsUser'] and (先前 is None or 当前['lastKey']!=先前['lastKey']))
            or (当前['steeringId'] is not None and 先前 is not None and 当前['steeringId']!=先前['steeringId']
                and 当前['steeringId']!=先前['submissionId'])
            or (当前['submissionId'] is not None and 先前 is not None and 当前['submissionId']!=先前['submissionId']
                and 当前['submissionId']!=先前['steeringId']))
        if 先前 is None:
            自有输入=当前['lastIsUser'] or 当前['steeringId'] is not None or 当前['submissionId'] is not None
        if 自身.读取.pending and not 自有输入:
            return
        自身.内容['applied']=当前
        if 当前['ready'] and not 自身.内容['opened']:
            自身.内容['opened']=True
            自身.导航.重置()
            自身.读取.恢复()
            return
        if 自有输入:
            自身.导航.取消()
            自身.读取.跟随尾()
            return
        if 自身.导航.内容已提交():
            自身.导航.对齐()
            return
        尖变=(先前 is None or 当前['ready']!=先前['ready']
            or 当前['firstSeq']!=先前['firstSeq'] or 当前['lastKey']!=先前['lastKey']
            or len(当前['order'])!=len(先前['order']) or 当前['running']!=先前['running']
            or 当前['steeringId']!=先前['steeringId'] or 当前['submissionId']!=先前['submissionId'])
        if 尖变 and 自身.读取.followingTail:
            自身.导航.取消()
            自身.读取.跟随尾()
        else:
            自身.导航.对齐()

    def 提交输入(自身,输入):
        """采纳新提交并处理。"""
        先前=自身.内容['input']
        导航输入={
            'firstSeq':输入['firstSeq'],
            'loadingOlder':输入['loadingOlder'],
            'hasMore':输入['hasMore'],
            'loadOlder':输入['loadOlder'],
            'loadThrough':输入['loadThrough'],
        }
        自身.导航.设输入(导航输入)
        自身.内容['input']=输入
        自身.视口.更新回合(输入['loadedTurns'])
        布局变=先前['order'] is not 输入['order'] or 先前['ready']!=输入['ready']
        if 布局变:
            自身.视口.作废()
        自身.处理内容()
        if 布局变:
            自身.读取.刷新活动回合()

    def 回到底部(自身):
        """取消导航并跟随尾。"""
        自身.导航.取消()
        自身.读取.跟随尾()

def 用聊天滚动(输入):
    """铸造滚动席位。输入为 dict。"""
    席=聊天滚动席位(输入)
    席.连接()
    列表=席.列表引用['current']
    列=席.列引用['current']
    if 列表 is not None and 列 is not None:
        席.视口.附着(列表,列)
    return {
        'listRef':席.列表引用,
        'columnRef':席.列引用,
        'initialized':席.状态['initialized'],
        'followingTail':席.状态['followingTail'],
        'activeTurn':席.状态['activeTurn'],
        'busyTurn':席.忙回合['值'],
        'navigateToTurn':席.导航.导航到回合,
        'loadEarlier':席.导航.加载更早,
        'returnToBottom':席.回到底部,
        'seat':席,
    }
