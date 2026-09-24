import builtins

__all__=['聊天导航','用聊天导航']

class 聊天导航:
    """一次可替换的回合跳转，以及历史加载期间保留的锚。"""
    def __init__(自身,视口,读取,输入,忙回合时):
        """输入为已提交聊天窗的历史可用性。"""
        自身.视口=视口
        自身.读取=读取
        自身.输入=输入
        自身.忙回合时=忙回合时
        自身.跳跃=None
        自身.结算帧=None

    def 设输入(自身,输入):
        """采纳已提交历史可用性，不发起请求。"""
        自身.输入=输入

    def 重置(自身):
        """打开聊天视图时取消导航。"""
        自身.取消()

    def 拆除(自身):
        """取消本地回调；迟到的历史完成不能复活任务。"""
        自身.清任务()

    def 取消(自身):
        """释放跳跃、分页锚与忙指示，不取消共享历史 IO。"""
        自身.清任务()
        自身.忙回合时(None)

    def 清任务(自身):
        """丢掉当前跳跃。"""
        自身.取消帧()
        自身.跳跃=None
        自身.视口.停止保留()

    def 导航到回合(自身,项):
        """用显式回合选择替换当前跳跃。项为 dict。"""
        锚=项['anchor']
        if 锚['kind']=='loaded':
            自身.取消()
            落地=自身.视口.滚到回合(项['turn'])
            if 落地 is None:
                return
            自身.读取.接受导航(落地)
            if 自身.输入['loadingOlder']:
                自身.视口.开始保留(落地['position'])
            return
        自身.取消()
        自身.视口.开始保留()
        自身.读取.暂停跟随()
        跳跃={'turn':项['turn'],'seq':锚['seq'],'phase':'loading','landing':'pending','repageHead':None}
        自身.跳跃=跳跃
        自身.忙回合时(跳跃['turn'])
        自身.请求(跳跃)

    def 加载更早(自身):
        """请求更早一页并保留当前语义位置。"""
        自身.取消()
        自身.视口.开始分页()
        自身.读取.暂停跟随()
        自身.输入['loadOlder']()

    def 读者已采样(自身,采样):
        """待处理历史工作期间保留读者所有权。采样为 dict。"""
        if 采样['movedByReader'] and 自身.跳跃 is not None and 自身.跳跃['landing']=='landed':
            自身.跳跃['landing']='interrupted'
        if 采样['followingTail'] or 采样['movedByReader']:
            自身.视口.停止保留()

    def 内容已提交(自身):
        """提交或稍后尺寸变化后保留一个分页锚。"""
        if not 自身.视口.preserving or 自身.读取.pending:
            return False
        if 自身.落地跳跃(False):
            return True
        落地=自身.视口.保留()
        if 落地 is None:
            return False
        自身.读取.保留位置(落地)
        return True

    def 读者已结算(自身):
        """内外读者滚动结束后才重定向仍在加载的页。"""
        if 自身.输入['loadingOlder'] and 自身.跳跃 is None and not 自身.视口.preserving and not 自身.读取.followingTail:
            自身.视口.开始保留()

    def 对齐(自身):
        """对照已提交窗口落地、重试或完成当前跳跃。"""
        跳跃=自身.跳跃
        if 跳跃 is None or 自身.读取.pending:
            return
        if 跳跃['phase']=='loading':
            if 跳跃['landing']=='pending':
                自身.落地跳跃(False)
            return
        if 自身.输入['loadingOlder']:
            return
        if 自身.落地跳跃(True):
            return
        首=自身.输入['firstSeq']
        未覆盖=首 is None or 首>跳跃['seq']
        if 未覆盖 and 自身.输入['hasMore'] and 跳跃['repageHead'] is not 首:
            跳跃['repageHead']=首
            自身.视口.开始保留()
            自身.请求(跳跃)
            return
        回退=自身.视口.滚到回合或之后(跳跃['turn'])
        自身.取消()
        if 回退 is not None:
            自身.读取.接受导航(回退)

    def 落地跳跃(自身,结算):
        """尝试滚到目标回合。"""
        跳跃=自身.跳跃
        if 跳跃 is None:
            return False
        if 跳跃['landing']=='interrupted':
            if 结算:
                自身.取消()
                return True
            return False
        落地=自身.视口.滚到回合(跳跃['turn'])
        if 落地 is None:
            return False
        自身.读取.接受导航(落地)
        if 结算:
            自身.取消()
        else:
            自身.视口.开始保留(落地['position'])
            跳跃['landing']='landed'
        return True

    def 请求(自身,跳跃):
        """同步加载到目标序号后对齐。"""
        跳跃['phase']='loading'
        def 已结算():
            """加载完成后一拍对齐。"""
            if 自身.跳跃 is not 跳跃:
                return
            跳跃['phase']='settled'
            自身.取消帧()
            调度=getattr(builtins,'requestAnimationFrame',None)
            if not callable(调度):
                自身.对齐()
            else:
                def 帧(*位置参数):
                    """下一拍。"""
                    自身.结算帧=None
                    if 自身.跳跃 is 跳跃:
                        自身.对齐()
                自身.结算帧=调度(帧)
        自身.输入['loadThrough'](跳跃['seq'])
        已结算()

    def 取消帧(自身):
        """取消对齐帧。"""
        取消=getattr(builtins,'cancelAnimationFrame',None)
        if 自身.结算帧 is not None and callable(取消):
            取消(自身.结算帧)
        自身.结算帧=None

def 用聊天导航(视口,读取,输入):
    """铸造导航所有者。"""
    忙回合={'值':None}
    def 设忙(回合):
        """可见忙回合。"""
        忙回合['值']=回合
    导航=聊天导航(视口,读取,输入,设忙)
    return {'navigation':导航,'busyTurn':忙回合}
