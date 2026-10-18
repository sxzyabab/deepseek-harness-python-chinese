from .用滚动跟随 import 用滚动跟随

__all__=['聊天读取','跟随阈值','采样间隔毫秒']

跟随阈值=24
采样间隔毫秒=500


class 聊天读取:
    '贴底、恢复保存位置，以及采样读者移动'
    def __init__(自身,视口,存储,状态,变更,跟随):
        '记下视口和初始阅读状态'
        自身.视口=视口
        自身.存储=存储
        自身.状态=dict(状态)
        自身.变更=变更
        自身.跟随=跟随
        自身.采样定时=None
        自身.探测帧=None
        自身.已采样=None

    def 待定(自身):
        '读者输入还没采样完'
        return 自身.采样定时 is not None

    def 正贴底(自身):
        '内容长高时还跟不跟'
        return 自身.状态.get('followingTail') is True

    def 设存储(自身,存储):
        '换成当前会话的滚动记忆'
        自身.存储=存储

    def 连接(自身,已采样):
        '历史策略接收落定的阅读位置'
        自身.已采样=已采样

        def 断开():
            '只摘这一份'
            if 自身.已采样 is 已采样:
                自身.已采样=None

        return 断开

    def 拆除(自身):
        '取消定时和帧'
        自身.取消待定()
        自身.已采样=None

    def 暂停跟随(自身):
        '显式导航时放开贴底'
        自身.取消待定()
        下一=dict(自身.状态)
        下一['followingTail']=False
        自身.发布(下一)

    def 跟随尾(自身,行为='instant'):
        '落到当前地板并清掉保存的位置'
        落地=自身.视口.滚到底(自身.跟随,行为)
        if 落地 is None:
            return
        自身.取消待定()
        自身.提交(落地,True,自身.视口.最新回合())

    def 跟随输入折叠(自身):
        '贴底交给正在跑的折叠时钟'
        自身.取消待定()
        return 自身.视口.跟随输入折叠(自身.跟随)

    def 绑折叠(自身):
        '让折叠批次读跟随意图'
        def 落地(落):
            '贴底落地后提交'
            自身.取消待定()
            自身.提交(落,True,自身.视口.最新回合())

        def 待定():
            '还有没采样的读者移动'
            return 自身.待定()

        return 自身.视口.绑读者({'follow':自身.跟随,'landedAtTail':落地,'pending':待定})

    def 打断跟随(自身):
        '停在当前原生滚动位置'
        自身.视口.打断跟随(自身.跟随)

    def 恢复(自身):
        '有保存位置就恢复，没有就贴底'
        保存=None
        if 自身.存储 is not None and callable(getattr(自身.存储,'read',None)):
            保存=自身.存储.read()
        if 保存 is None:
            自身.跟随尾()
            return
        落地=自身.视口.恢复(保存)
        if 落地 is None:
            return
        自身.取消待定()
        跟随=自身.跟随.靠近底(落地['metrics'])
        回合=自身.视口.最新回合() if 跟随 else 自身.状态.get('activeTurn')
        自身.提交(落地,跟随,回合,跟随)
        if not 自身.状态.get('followingTail') and 落地.get('position') is None:
            位置=自身.视口.捕获位置()
            if 位置 is not None and callable(getattr(自身.存储,'save',None)):
                自身.存储.save(位置)
        自身.刷新活动回合()

    def 接受导航(自身,落地):
        '导航落地直接采用'
        自身.取消待定()
        跟随=自身.跟随.靠近底(落地['metrics'])
        回合=落地.get('turn')
        if 回合 is None and 跟随:
            回合=自身.视口.最新回合()
        elif 回合 is None:
            回合=自身.状态.get('activeTurn')
        自身.提交(落地,跟随,回合)

    def 保留位置(自身,落地):
        '历史改几何时保持当前策略'
        自身.取消待定()
        自身.提交(落地,自身.状态.get('followingTail') is True,自身.状态.get('activeTurn'))

    def 当滚动(自身,滚动):
        '贴底和刚到地板立刻处理。其余等采样'
        if 自身.跟随.动画中():
            return
        度量=滚动['metrics']
        if (not 滚动['movedByReader'] and 自身.状态.get('followingTail')) or (滚动['movedByReader'] and abs(度量['top']-度量['floor'])<1):
            自身.跟随尾()
            if callable(自身.已采样):
                自身.已采样({'position':None,'movedByReader':滚动['movedByReader'],'followingTail':True})
            return
        if 自身.采样定时 is None:
            窗=自身.取窗()
            if 窗 is not None and hasattr(窗,'setTimeout'):
                自身.采样定时=窗.setTimeout(自身.冲刷采样,采样间隔毫秒)

    def 当滚动结束(自身,外层=True):
        '只有外层滚动口能结束贴底动画'
        if 自身.跟随.动画中():
            if not 外层:
                return
            滚动=自身.视口.读滚动()
            if 滚动 is None:
                return
            if 自身.跟随.结算(滚动['metrics']):
                自身.跟随尾()
                return
            自身.视口.承认(滚动['metrics'])
            下一=dict(自身.状态)
            下一['followingTail']=False
            自身.发布(下一)
            自身.刷新活动回合()
            return
        自身.冲刷采样()

    def 当尺寸(自身):
        '没采样完的读者输入不被尺寸盖掉'
        if 自身.待定():
            return
        if 自身.状态.get('followingTail'):
            自身.跟随尾()
        else:
            自身.刷新活动回合()

    def 刷新活动回合(自身):
        '贴底用最新回合。否则下一帧探阅读线'
        if 自身.待定():
            return
        if 自身.状态.get('followingTail'):
            下一=dict(自身.状态)
            下一['initialized']=True
            下一['activeTurn']=自身.视口.最新回合()
            自身.发布(下一)
            return
        if 自身.探测帧 is not None:
            return
        窗=自身.取窗()
        if 窗 is None or not hasattr(窗,'requestAnimationFrame'):
            自身.探测()
        else:
            自身.探测帧=窗.requestAnimationFrame(自身.探测)

    def 提交(自身,落地,贴底,活动回合,已初始化=True):
        '贴底清记忆。否则保存锚'
        if 贴底:
            if callable(getattr(自身.存储,'save',None)):
                自身.存储.save(None)
        elif 落地.get('position') is not None and callable(getattr(自身.存储,'save',None)):
            自身.存储.save(落地['position'])
        自身.发布({'initialized':已初始化,'followingTail':贴底,'activeTurn':活动回合})

    def 发布(自身,状态):
        '没变化就不通知'
        自身.跟随.设跟随(状态.get('followingTail') is True)
        if 状态.get('initialized')==自身.状态.get('initialized') and 状态.get('followingTail')==自身.状态.get('followingTail') and 状态.get('activeTurn')==自身.状态.get('activeTurn'):
            自身.状态=dict(状态)
            return
        自身.状态=dict(状态)
        if callable(自身.变更):
            自身.变更(dict(自身.状态))

    def 取消待定(自身):
        '清定时和探测帧'
        窗=自身.取窗()
        if 自身.采样定时 is not None and 窗 is not None and hasattr(窗,'clearTimeout'):
            窗.clearTimeout(自身.采样定时)
        if 自身.探测帧 is not None and 窗 is not None and hasattr(窗,'cancelAnimationFrame'):
            窗.cancelAnimationFrame(自身.探测帧)
        自身.采样定时=None
        自身.探测帧=None

    def 探测(自身,时刻=None):
        '从阅读线读活动回合'
        自身.探测帧=None
        if 自身.待定():
            return
        滚动=自身.视口.读滚动()
        if 滚动 is None:
            return
        if 自身.跟随.靠近底(滚动['metrics']):
            回合=自身.视口.最新回合()
        else:
            回合=自身.视口.读可见回合(滚动['metrics'])
        下一=dict(自身.状态)
        下一['initialized']=True
        下一['activeTurn']=回合
        自身.发布(下一)

    def 冲刷采样(自身):
        '采样间隔到了，决定是否还贴底'
        if not 自身.待定():
            return
        自身.取消待定()
        滚动=自身.视口.读滚动()
        if 滚动 is None:
            return
        贴底=自身.跟随.采样(滚动['metrics'],滚动['movedByReader'])
        位置=None
        if not 滚动['movedByReader'] and 贴底:
            自身.跟随尾()
        else:
            位置=None if 贴底 else 自身.视口.捕获位置()
            自身.视口.承认(滚动['metrics'])
            if (贴底 or 位置 is not None) and callable(getattr(自身.存储,'save',None)):
                自身.存储.save(位置)
            if 自身.跟随.靠近底(滚动['metrics']):
                回合=自身.视口.最新回合()
            else:
                回合=自身.视口.读可见回合(滚动['metrics'])
            自身.发布({'initialized':True,'followingTail':贴底,'activeTurn':回合})
        if callable(自身.已采样):
            自身.已采样({'position':位置,'movedByReader':滚动['movedByReader'],'followingTail':贴底})

    def 取窗(自身):
        '滚动口所在窗口'
        if 自身.视口.元素 is None:
            return None
        滚动口=自身.视口.元素['scroller']
        文档=getattr(滚动口,'ownerDocument',None)
        if 文档 is None:
            return None
        return getattr(文档,'defaultView',None)
