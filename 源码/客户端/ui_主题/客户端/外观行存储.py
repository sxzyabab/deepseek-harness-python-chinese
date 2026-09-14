
__all__=['创建外观行存储','外观行状态']#仅中文公开名

def 创建外观行存储():
    """默认 system、修订 -1；sync 按修订守卫丢弃过期。"""
    状态={'preference':'system','revision':-1}#初始
    监听集合=set()#订阅者

    def 通知():
        """通知全部监听。"""
        for 监听器 in list(监听集合):#快照
            监听器()#触发

    def 同步(偏好,修订):
        """修订不大于当前则丢弃。"""
        if 修订<=状态['revision']:#旧
            return#丢
        状态['preference']=偏好#偏好
        状态['revision']=修订#修订
        通知()#通知

    def 取快照():
        """快照拷贝。"""
        return dict(状态)#拷贝

    def 订阅(监听器):
        """登记监听，返回退订。"""
        监听集合.add(监听器)#加入
        def 退订():
            """取消订阅。"""
            监听集合.discard(监听器)#删除
        return 退订#退订器

    return {#存储句柄；getSnapshot/subscribe/sync 是槽位存储协议键
        'getSnapshot':取快照,#快照拷贝
        'subscribe':订阅,#订阅
        'sync':同步,#同步
        'init':状态,#初始态引用
    }#结束

外观行状态=dict#状态形别名（preference/revision）
