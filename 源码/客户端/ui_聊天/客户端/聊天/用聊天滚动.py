from .用聊天导航 import 聊天导航
from .用聊天读取 import 聊天读取,跟随阈值
from .用滚动跟随 import 用滚动跟随
from .用聊天视口 import 聊天视口

__all__=['聊天滚动']


class 聊天滚动:
    '把视口、阅读和历史导航接在一次提交上'
    def __init__(自身,窗口):
        '先造视口。阅读要等第一次有存储时再造'
        自身.窗口=窗口
        自身.视口=聊天视口()
        自身.阅读=None
        自身.导航=None
        自身.已开=False
        自身.已应用=None
        自身.上次输入=None
        自身.上次视图=None
        自身.列表=None
        自身.列=None
        自身.状态={'initialized':False,'followingTail':True,'activeTurn':None}
        自身.忙回合值=None
        自身.已连接=False

    def 当状态(自身,状态):
        '阅读状态变了就留下，并请视图再画一次'
        自身.状态=dict(状态)
        if callable(getattr(自身,'重画',None)):
            自身.重画()

    def 当忙(自身,回合):
        '导航忙的回合'
        自身.忙回合值=回合

    def 确保(自身,存储,初始回合):
        '第一次看到滚动记忆时造阅读和导航'
        if 自身.阅读 is not None:
            自身.阅读.设存储(存储)
            return
        贴底=True
        if 存储 is not None and callable(getattr(存储,'read',None)):
            贴底=存储.read() is None
        自身.状态={'initialized':False,'followingTail':贴底,'activeTurn':初始回合}
        跟随=用滚动跟随(贴底,跟随阈值+1)
        自身.阅读=聊天读取(自身.视口,存储,自身.状态,自身.当状态,跟随)
        自身.导航=聊天导航(自身.视口,自身.阅读,{'firstSeq':None,'hasMore':False,'loadingOlder':False,'loadOlder':None,'loadThrough':None},自身.当忙)

    def 连接一次(自身):
        '监听只接一次'
        if 自身.已连接 or 自身.阅读 is None:
            return
        自身.已连接=True

        def 滚动(事件):
            '折叠进行中且不是读者挪的，先不采样'
            if not 自身.已开:
                return
            if not 事件['movedByReader'] and 自身.视口.动效['foldActive']():
                return
            自身.阅读.当滚动(事件)

        def 结束(外层):
            '滚动停了再调和导航'
            自身.阅读.当滚动结束(外层)
            自身.导航.读者已停()

        def 交互():
            '分页被读者打断'
            自身.导航.取消()

        def 意图():
            '任何阅读手势都取消待定的贴底'
            自身.视口.动效['cancelInput']()
            自身.阅读.打断跟随()

        def 尺寸():
            '折叠进行中不让尺寸策略抢滚动'
            if not 自身.已开:
                return
            if 自身.导航.内容已提交():
                自身.导航.调和()
                return
            if not 自身.上次输入 or not 自身.上次输入.get('deferCompletedTurns') or not 自身.视口.动效['foldActive']():
                自身.阅读.当尺寸()
            自身.导航.调和()

        自身.视口.连接({'scroll':滚动,'scrollEnd':结束,'interact':交互,'intent':意图,'resize':尺寸})

        def 采样(样本):
            '读者落定后处理内容'
            自身.导航.读者已采样(样本)
            自身.处理内容()

        自身.阅读.连接(采样)
        自身.阅读.绑折叠()

    def 挂元素(自身,列表,列):
        '元素换了才重新挂'
        if 列表 is None or 列 is None:
            return
        if 自身.列表 is 列表 and 自身.列 is 列 and 自身.视口.元素 is not None:
            return
        自身.列表=列表
        自身.列=列
        自身.视口.挂上(列表,列)

    def 处理内容(自身):
        '自己的新输入优先于还没采样的读者'
        当前=自身.上次输入
        if 当前 is None:
            return
        if not 当前.get('ready') and not 自身.已开:
            return
        先前=自身.已应用
        自己的=(当前.get('lastIsUser') and 当前.get('lastKey')!=(None if 先前 is None else 先前.get('lastKey'))) or (当前.get('steeringId') is not None and (先前 is None or (当前.get('steeringId')!=先前.get('steeringId') and 当前.get('steeringId')!=先前.get('submissionId')))) or (当前.get('submissionId') is not None and (先前 is None or (当前.get('submissionId')!=先前.get('submissionId') and 当前.get('submissionId')!=先前.get('steeringId'))))
        if 自身.阅读.待定() and not 自己的:
            return
        自身.已应用=dict(当前)
        if 当前.get('ready') and not 自身.已开:
            自身.已开=True
            自身.导航.重置()
            自身.阅读.恢复()
            return
        if 自己的:
            自身.导航.取消()
            if 当前.get('deferCompletedTurns') and 自身.阅读.跟随输入折叠():
                return
            自身.阅读.跟随尾('smooth' if 当前.get('deferCompletedTurns') else 'instant')
            return
        if 自身.导航.内容已提交():
            自身.导航.调和()
            return
        尖变了=先前 is None or 当前.get('ready')!=先前.get('ready') or 当前.get('firstSeq')!=先前.get('firstSeq') or 当前.get('lastKey')!=先前.get('lastKey') or len(当前.get('order') or [])!=len(先前.get('order') or []) or 当前.get('running')!=先前.get('running') or 当前.get('steeringId')!=先前.get('steeringId') or 当前.get('submissionId')!=先前.get('submissionId')
        if 尖变了 and 自身.阅读.正贴底():
            自身.导航.取消()
            if 当前.get('deferCompletedTurns') and 自身.阅读.跟随输入折叠():
                return
            自身.阅读.跟随尾()
        else:
            自身.导航.调和()

    def 提交(自身,输入):
        '每次渲染后按新内容和布局调和滚动'
        自身.确保(输入.get('chatScroll'),None if len(输入.get('loadedTurns') or [])==0 else 输入['loadedTurns'][-1].get('turn'))
        自身.连接一次()
        自身.挂元素(输入.get('list'),输入.get('column'))
        先前=自身.上次输入
        自身.上次输入=dict(输入)
        自身.导航.设输入({
            'firstSeq':输入.get('firstSeq'),
            'loadingOlder':输入.get('loadingOlder'),
            'hasMore':输入.get('hasMore'),
            'loadOlder':输入.get('loadOlder'),
            'loadThrough':输入.get('loadThrough'),
        })
        if not 输入.get('deferCompletedTurns'):
            自身.视口.动效['cancelInput']()
            自身.阅读.打断跟随()
        自身.视口.更新回合(输入.get('loadedTurns') or [])
        布局变了=先前 is None or 先前.get('order') is not 输入.get('order') or 先前.get('ready')!=输入.get('ready')
        if 布局变了:
            自身.视口.作废()
        自身.视口.收回下方()
        自身.处理内容()
        if 布局变了 and 自身.已开:
            自身.阅读.刷新活动回合()
        视图=输入.get('transcriptView')
        if 自身.上次视图 is not None and 自身.上次视图!=视图:
            自身.视口.动效['cancelInput']()
            自身.阅读.打断跟随()
            def 闲():
                '折叠停了再清垫'
                自身.视口.重置下方()
                if 自身.已开:
                    自身.阅读.当尺寸()
            自身.视口.动效['onFoldIdle'](闲)
        自身.上次视图=视图

    def 回到底(自身):
        '按钮：取消折叠贴底，直接跟尾'
        自身.视口.动效['cancelInput']()
        if 自身.导航 is not None:
            自身.导航.取消()
        if 自身.阅读 is not None:
            自身.阅读.跟随尾()

    def 加载更早(自身):
        '更早按钮'
        if 自身.导航 is not None:
            自身.导航.加载更早()

    def 导航到回合(自身,项):
        '轨上的一回合'
        if 自身.导航 is not None:
            自身.导航.导航到回合(项)
