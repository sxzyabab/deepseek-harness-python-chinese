"""设置传输的测试替身。"""

def 桩配置表单():
    """内存中的设置作用域：从宿主加载态起步，记录写入，并由测试发布宿主接受。"""
    快照={
        'status':'loading','value':None,'base':None,'user':None,
        'revision':None,'writable':False,'mode':'host',
    }
    监听者=set()
    设置记录=[]
    改写记录=[]
    取消记录=[]

    def 取快照():
        """当前快照。"""
        return 快照

    def 订阅(回调):
        """订阅快照变更。"""
        监听者.add(回调)
        def 拆除():
            """去掉本监听者。"""
            监听者.discard(回调)
        return 拆除

    def 设置(*位置参数,**关键字参数):
        """立刻成功的 set 间谍。"""
        设置记录.append((位置参数,关键字参数))
        return True

    def 改写(*位置参数,**关键字参数):
        """立刻成功的 mutate 间谍。"""
        改写记录.append((位置参数,关键字参数))
        return True

    def 取消(*位置参数,**关键字参数):
        """立刻成功的 unset 间谍。"""
        取消记录.append((位置参数,关键字参数))
        return True

    def 监听者数():
        """当前订阅数。"""
        return len(监听者)

    def 发布(下一):
        """替换快照一部分并通知订阅者。"""
        快照.update(下一)
        for 回调 in list(监听者):
            回调()

    return {
        'scope':{
            'getSnapshot':取快照,
            'subscribe':订阅,
            'mutate':改写,
            'set':设置,
            'unset':取消,
        },
        'set':设置,
        'mutate':改写,
        'unset':取消,
        'listenerCount':监听者数,
        'publish':发布,
        '设置记录':设置记录,
        '改写记录':改写记录,
        '取消记录':取消记录,
    }

__all__=['桩配置表单']
