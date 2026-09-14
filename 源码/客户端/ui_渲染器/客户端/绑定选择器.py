__all__=['绑定快照选择器']#仅中文公开名

def 绑定快照选择器(源):
    """subscribe/getSnapshot 按源捕获进稳定闭包一次。"""
    def 订阅(回调):
        """稳定订阅闭包。"""
        return 源.subscribe(回调)#订
    def 取快照():
        """稳定读快照闭包。"""
        return 源.getSnapshot()#读

    def 用选择器(选择器,相等=None):
        """无服务器快照；相等性默认 is。"""
        快照=取快照()#读快照
        return 选择器(快照)#选中切片
    用选择器._subscribe=订阅#挂订阅供外部
    用选择器._getSnapshot=取快照#挂快照供外部
    return 用选择器#返回钩子
