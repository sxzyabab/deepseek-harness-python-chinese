import builtins
from .用滚动跟随 import 用滚动跟随

__all__=['聊天读取','用聊天读取']

跟随阈值=24
滚动采样间隔毫秒=500

class 聊天读取:
    """跟随尾部所有权、已存位置恢复与采样读者移动，不访问 DOM。"""
    def __init__(自身,视口,存储,状态,变更时,跟随):
        """记下视口、滚动记忆与跟随器。"""
        自身.视口=视口
        自身.存储=存储
        自身.状态=状态
        自身.变更时=变更时
        自身.跟随=跟随
        自身.采样定时=None
        自身.探测帧=None
        自身.已采样=None

    @property
    def pending(自身):
        """是否仍等间隔或 scrollend 采样。"""
        return 自身.采样定时 is not None

    @property
    def followingTail(自身):
        """内容增长是否保留底部跟随。"""
        return 自身.状态['followingTail']

    def 设存储(自身,存储):
        """采纳当前会话的滚动记忆。"""
        自身.存储=存储

    def 连接(自身,已采样):
        """把历史策略接到已结算阅读观察。"""
        自身.已采样=已采样
        def 断开():
            """只断开这名监听。"""
            if 自身.已采样 is 已采样:
                自身.已采样=None
        return 断开

    def 拆除(自身):
        """取消定时与帧并摘掉采样监听。"""
        自身.取消待处理()
        自身.已采样=None

    def 暂停跟随(自身):
        """显式导航时释放底部跟随与待采样。"""
        自身.取消待处理()
        自身.发布({'initialized':自身.状态['initialized'],'followingTail':False,'activeTurn':自身.状态['activeTurn']})

    def 跟随尾(自身):
        """落到当前底部并清除已存读者位置。"""
        落地=自身.视口.滚到底(自身.跟随)
        if 落地 is None:
            return
        自身.取消待处理()
        自身.提交(落地,True,自身.视口.latestTurn)

    def 恢复(自身):
        """恢复会话语义位置；无已存则跟随尾。"""
        已存=自身.存储.read()
        if 已存 is None:
            自身.跟随尾()
            return
        落地=自身.视口.恢复(已存)
        if 落地 is None:
            return
        自身.取消待处理()
        跟随=自身.跟随.近底(落地['metrics'])
        自身.提交(落地,跟随,自身.视口.latestTurn if 跟随 else 自身.状态['activeTurn'],跟随)
        if not 自身.状态['followingTail'] and 落地['position'] is None:
            位置=自身.视口.捕获位置()
            if 位置 is not None:
                自身.存储.save(位置)
        自身.刷新活动回合()

    def 接受导航(自身,落地):
        """采纳已知落地，不重发现锚。"""
        自身.取消待处理()
        跟随=自身.跟随.近底(落地['metrics'])
        回合=落地['turn']
        if 回合 is None:
            回合=自身.视口.latestTurn if 跟随 else 自身.状态['activeTurn']
        自身.提交(落地,跟随,回合)

    def 保留位置(自身,落地):
        """历史改变锚几何时保留阅读策略。"""
        自身.取消待处理()
        自身.提交(落地,自身.状态['followingTail'],自身.状态['activeTurn'])

    def 滚动(自身,滚动):
        """钉住布局移动与读者抵达底部立即处理。滚动为 dict。"""
        if ((not 滚动['movedByReader'] and 自身.状态['followingTail'])
            or (滚动['movedByReader'] and 滚动['metrics']['top']>=滚动['metrics']['floor'])):
            自身.跟随尾()
            if 自身.已采样 is not None:
                自身.已采样({'position':None,'movedByReader':滚动['movedByReader'],'followingTail':True})
            return
        if 自身.采样定时 is None:
            窗=getattr(builtins,'window',None)
            定时=窗.setTimeout if 窗 is not None else getattr(builtins,'setTimeout',None)
            自身.采样定时=定时(自身.冲刷采样,滚动采样间隔毫秒)

    def 滚动结束(自身):
        """浏览器 scrollend 时结算待处理读者移动。"""
        自身.冲刷采样()

    def 尺寸变化(自身):
        """布局变化；不覆盖未采样读者输入。"""
        if 自身.pending:
            return
        if 自身.状态['followingTail']:
            自身.跟随尾()
        else:
            自身.刷新活动回合()

    def 刷新活动回合(自身):
        """由尾部所有权或合并后的阅读线探测解析活动回合。"""
        if 自身.pending:
            return
        if 自身.状态['followingTail']:
            自身.发布({'initialized':True,'followingTail':True,'activeTurn':自身.视口.latestTurn})
            return
        if 自身.探测帧 is not None:
            return
        调度=getattr(builtins,'requestAnimationFrame',None)
        if not callable(调度):
            自身.探测()
        else:
            自身.探测帧=调度(自身.探测)

    def 提交(自身,落地,跟随尾,活动回合,已初始化=True):
        """写入滚动记忆并发布。"""
        if 跟随尾:
            自身.存储.save(None)
        elif 落地['position'] is not None:
            自身.存储.save(落地['position'])
        自身.发布({'initialized':已初始化,'followingTail':跟随尾,'activeTurn':活动回合})

    def 发布(自身,状态):
        """跟随器对齐；无变化则不通知。就地更新同一状态表。"""
        自身.跟随.设跟随(状态['followingTail'])
        if (状态['initialized']==自身.状态['initialized']
            and 状态['followingTail']==自身.状态['followingTail']
            and 状态['activeTurn']==自身.状态['activeTurn']):
            return
        自身.状态['initialized']=状态['initialized']
        自身.状态['followingTail']=状态['followingTail']
        自身.状态['activeTurn']=状态['activeTurn']
        自身.变更时(自身.状态)

    def 取消待处理(自身):
        """清定时与帧。"""
        if 自身.采样定时 is not None:
            窗=getattr(builtins,'window',None)
            清=窗.clearTimeout if 窗 is not None else getattr(builtins,'clearTimeout',None)
            if callable(清):
                清(自身.采样定时)
        取消=getattr(builtins,'cancelAnimationFrame',None)
        if 自身.探测帧 is not None and callable(取消):
            取消(自身.探测帧)
        自身.采样定时=None
        自身.探测帧=None

    def 探测(自身,*位置参数):
        """一拍后读可见回合。"""
        自身.探测帧=None
        if 自身.pending:
            return
        滚动=自身.视口.读滚动()
        if 滚动 is None:
            return
        度量=滚动['metrics']
        活动=自身.视口.latestTurn if 自身.跟随.近底(度量) else 自身.视口.读可见回合(度量)
        自身.发布({'initialized':True,'followingTail':自身.状态['followingTail'],'activeTurn':活动})

    def 冲刷采样(自身,*位置参数):
        """结算待采样读者移动。"""
        if not 自身.pending:
            return
        自身.取消待处理()
        滚动=自身.视口.读滚动()
        if 滚动 is None:
            return
        跟随尾=自身.跟随.采样(滚动['metrics'],滚动['movedByReader'])
        位置=None
        if not 滚动['movedByReader'] and 跟随尾:
            自身.跟随尾()
        else:
            位置=None if 跟随尾 else 自身.视口.捕获位置()
            自身.视口.确认(滚动['metrics'])
            if 跟随尾 or 位置 is not None:
                自身.存储.save(位置)
            度量=滚动['metrics']
            活动=自身.视口.latestTurn if 自身.跟随.近底(度量) else 自身.视口.读可见回合(度量)
            自身.发布({'initialized':True,'followingTail':跟随尾,'activeTurn':活动})
        if 自身.已采样 is not None:
            自身.已采样({'position':位置,'movedByReader':滚动['movedByReader'],'followingTail':跟随尾})

def 用聊天读取(视口,存储,初始回合):
    """铸造读取策略。存储为带 read/save 的滚动记忆。"""
    状态={'initialized':False,'followingTail':存储.read() is None,'activeTurn':初始回合}
    跟随=用滚动跟随(状态['followingTail'],跟随阈值+1)
    def 变更(下一):
        """席位可见状态。"""
        读取.状态=下一
    读取=聊天读取(视口,存储,状态,变更,跟随)
    读取.变更时=变更
    return {'reading':读取,'state':读取.状态}
