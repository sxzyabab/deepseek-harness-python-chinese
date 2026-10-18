__all__=['聊天导航']


class 聊天导航:
    '回合跳转和往前补历史时保住锚'
    def __init__(自身,视口,阅读,输入,忙回合):
        '记下视口和历史操作'
        自身.视口=视口
        自身.阅读=阅读
        自身.输入=dict(输入)
        自身.忙回合=忙回合
        自身.跳=None
        自身.结算帧=None

    def 设输入(自身,输入):
        '换成最新的历史状态'
        自身.输入=dict(输入)

    def 重置(自身):
        '打开聊天时取消导航'
        自身.取消()

    def 拆除(自身):
        '卸掉本地回调'
        自身.清任务()

    def 取消(自身):
        '放开跳转和分页锚。不取消共享的历史读取'
        自身.清任务()
        if callable(自身.忙回合):
            自身.忙回合(None)

    def 清任务(自身):
        '清帧和跳转'
        自身.清帧()
        自身.跳=None
        自身.视口.停止保留()

    def 导航到回合(自身,项):
        '已加载就直接对齐。未加载就先取到那个序号'
        锚=项.get('anchor') if isinstance(项,dict) else None
        if isinstance(锚,dict) and 锚.get('kind')=='loaded':
            自身.取消()
            落地=自身.视口.滚到回合(项.get('turn'))
            if 落地 is None:
                return
            自身.阅读.接受导航(落地)
            if 自身.输入.get('loadingOlder'):
                自身.视口.开始保留(落地.get('position'))
            return
        自身.取消()
        自身.视口.开始保留()
        自身.阅读.暂停跟随()
        跳={'turn':项.get('turn'),'seq':None if not isinstance(锚,dict) else 锚.get('seq'),'phase':'loading','landing':'pending','repageHead':None}
        自身.跳=跳
        if callable(自身.忙回合):
            自身.忙回合(跳['turn'])
        自身.请求(跳)

    def 加载更早(自身):
        '留住当前位置再要一页更早的历史'
        自身.取消()
        自身.视口.开始翻页()
        自身.阅读.暂停跟随()
        加载=自身.输入.get('loadOlder')
        if callable(加载):
            加载()

    def 读者已采样(自身,样本):
        '读者自己动了，就不再守着跳转锚'
        if 样本.get('movedByReader') and isinstance(自身.跳,dict) and 自身.跳.get('landing')=='landed':
            自身.跳['landing']='interrupted'
        if 样本.get('followingTail') or 样本.get('movedByReader'):
            自身.视口.停止保留()

    def 内容已提交(自身):
        '分页锚还在时，用它消化这次布局'
        if not 自身.视口.正在保留() or 自身.阅读.待定():
            return False
        if 自身.落地跳转(False):
            return True
        落地=自身.视口.保留位置()
        if 落地 is None:
            return False
        自身.阅读.保留位置(落地)
        return True

    def 读者已停(自身):
        '还在加载更早历史、又没有锚时，重新开始保留'
        if 自身.输入.get('loadingOlder') and 自身.跳 is None and not 自身.视口.正在保留() and not 自身.阅读.正贴底():
            自身.视口.开始保留()

    def 调和(自身):
        '对照已提交窗口落地、重试或结束这次跳转'
        跳=自身.跳
        if 跳 is None or 自身.阅读.待定():
            return
        if 跳.get('phase')=='loading':
            if 跳.get('landing')=='pending':
                自身.落地跳转(False)
            return
        if 自身.输入.get('loadingOlder'):
            return
        if 自身.落地跳转(True):
            return
        首=自身.输入.get('firstSeq')
        未覆盖=首 is None or (跳.get('seq') is not None and 首>跳['seq'])
        if 未覆盖 and 自身.输入.get('hasMore') and 跳.get('repageHead')!=首:
            跳['repageHead']=首
            自身.视口.开始保留()
            自身.请求(跳)
            return
        回退=自身.视口.滚到回合或之后(跳.get('turn'))
        自身.取消()
        if 回退 is not None:
            自身.阅读.接受导航(回退)

    def 落地跳转(自身,结算):
        '锚已经在窗口里就对齐'
        跳=自身.跳
        if 跳 is None:
            return False
        if 跳.get('landing')=='interrupted':
            if 结算:
                自身.取消()
                return True
            return False
        落地=自身.视口.滚到回合(跳.get('turn'))
        if 落地 is None:
            return False
        自身.阅读.接受导航(落地)
        if 结算:
            自身.取消()
        else:
            自身.视口.开始保留(落地.get('position'))
            跳['landing']='landed'
        return True

    def 请求(自身,跳):
        '取到序号后下一帧再调和'
        跳['phase']='loading'
        加载=自身.输入.get('loadThrough')

        def 落定(结果=None):
            '晚到的完成不能复活已取消的跳转'
            if 自身.跳 is not 跳:
                return
            跳['phase']='settled'
            自身.清帧()
            窗=自身.取窗()
            if 窗 is None or not hasattr(窗,'requestAnimationFrame'):
                自身.调和()
                return

            def 帧(时刻=None):
                '下一帧再看窗口'
                自身.结算帧=None
                if 自身.跳 is 跳:
                    自身.调和()

            自身.结算帧=窗.requestAnimationFrame(帧)

        if not callable(加载):
            落定()
            return
        try:
            结果=加载(跳.get('seq'))
        except Exception:
            落定()
            return
        if hasattr(结果,'then'):
            结果.then(落定,落定)
        else:
            落定(结果)

    def 清帧(自身):
        '取消还没跑的调和帧'
        窗=自身.取窗()
        if 自身.结算帧 is not None and 窗 is not None and hasattr(窗,'cancelAnimationFrame'):
            窗.cancelAnimationFrame(自身.结算帧)
        自身.结算帧=None

    def 取窗(自身):
        '滚动口所在窗口'
        if 自身.视口.元素 is None:
            return None
        文档=getattr(自身.视口.元素['scroller'],'ownerDocument',None)
        if 文档 is None:
            return None
        return getattr(文档,'defaultView',None)
