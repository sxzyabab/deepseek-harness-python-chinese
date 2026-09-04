"""uSES 桥：把任意裸可观察快照源变成带类型的选择器钩子。

对齐上游 `ui-renderer/src/client/bind.ts`。公开面仅中文名。
仅客户端渲染，不接线服务器快照。
"""
__all__=['绑定快照选择器']#仅中文公开名

def 绑定快照选择器(源):#绑定选择器
    """subscribe/getSnapshot 按源捕获进稳定闭包一次。"""
    订阅=lambda 回调:源.subscribe(回调)#稳定订阅闭包
    取快照=lambda:源.getSnapshot()#稳定读快照闭包

    def 用选择器(选择器,相等=None):#选择器钩子
        """无服务器快照；相等性默认 is。"""
        快照=取快照()#读快照
        选中=选择器(快照)#选择
        return 选中#选中切片
    用选择器._subscribe=订阅#挂订阅供外部
    用选择器._getSnapshot=取快照#挂快照供外部
    return 用选择器#返回钩子

bindSnapshotSelector=绑定快照选择器#上游名
