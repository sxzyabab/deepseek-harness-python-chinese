__all__=['创建轨迹字符串换行存储']#仅中文公开名

def 创建轨迹字符串换行存储():
    """浏览器范围内展开 JSON 字符串时的默认折行偏好。"""
    当前=[False]#可变单元格，初值 false
    监听集合=set()#订阅者
    def 取():
        """当前是否折行。"""
        return 当前[0]#读出
    def 设(值):
        """写入布尔偏好。"""
        当前[0]=bool(值)#收成布尔
        for 回调 in list(监听集合):#通知
            回调()#触发
    def 订阅(回调):
        """观察变更。"""
        监听集合.add(回调)#加入
        def 退订():
            """取消。"""
            监听集合.discard(回调)#删除
        return 退订#退订器
    return {#句柄
        'get':取,#读
        'set':设,#写
        'getSnapshot':取,#快照
        'subscribe':订阅,#订阅
        'persist':'dsh.trajectory.jsonStringWrapping',#本地持久名
    }#句柄结束
