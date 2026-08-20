"""Composer 阻断：其它插件让某会话输入栏失效的唯一途径。

对齐上游 `ui-conversation/src/client/input/blocks.ts`。公开面仅中文名。
"""

__all__=['快照仓库','阻断登记表']#仅中文公开名

class 快照仓库:#简易阻断快照
    """值 + 订阅；对齐 createSnapshotStore。"""
    def __init__(自身,初值):#播种
        """记下初值。"""
        自身.状态=初值#当前值（可为 None）
        自身.监听者=set()#订阅者

    def getSnapshot(自身):#读快照
        """返回当前值。"""
        return 自身.状态#值

    def subscribe(自身,回调):#订阅
        """登记变更回调。"""
        自身.监听者.add(回调)#加入
        def 退订():#退订
            """取消。"""
            自身.监听者.discard(回调)#删除
        return 退订#退订器

    def set(自身,下一份):#整体替换
        """写入新值并通知。"""
        自身.状态=下一份#覆盖
        for 回调 in list(自身.监听者):#通知
            回调()#触发

class 阻断登记表:#按会话的 composer 阻断注册表
    """每个插件 fiber 一份实例；经 ctx.conversation.blocks 触达。"""
    def __init__(自身):#空表
        """会话 id → 阻断 store。"""
        自身.仓库们={}#表

    def set(自身,会话标识,阻断):#提出或清除阻断
        """幂等：原因相同则不通知。"""
        仓库=自身.storeFor(会话标识)#取或创建
        当前=仓库.getSnapshot()#当前
        当前原因=当前.get('reason') if isinstance(当前,dict) else None#原因
        新原因=阻断.get('reason') if isinstance(阻断,dict) else None#新原因
        if 当前原因==新原因:#相同
            return#跳过
        仓库.set(阻断)#写入或清除

    def storeFor(自身,会话标识):#取本会话阻断 store
        """首次读取时创建；初值为未阻断。"""
        已有=自身.仓库们.get(会话标识)#已有
        if 已有 is not None:#复用
            return 已有#已有
        新建=快照仓库(None)#未阻断
        自身.仓库们[会话标识]=新建#登记
        return 新建#交给调用方

    def forget(自身,会话标识):#丢掉该会话 store
        """由会话作用域 disposer 调用。"""
        自身.仓库们.pop(会话标识,None)#删除
