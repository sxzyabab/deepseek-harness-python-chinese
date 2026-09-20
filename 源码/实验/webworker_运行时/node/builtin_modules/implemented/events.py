__all__=['EventEmitter']

class 事件发出器:
    """Harness 注册的 `node:events` 子集：添加、移除与发出。"""

    def __init__(自身):
        """空注册表。"""
        自身._注册表={}

    def 监听(自身,事件,监听器):
        """注册监听器。"""
        if 事件 not in 自身._注册表: 列表=[]#??空列表，判的是缺席不是 length
        else: 列表=自身._注册表[事件]
        列表.append(监听器)
        自身._注册表[事件]=列表
        return 自身

    def 一次(自身,事件,监听器):
        """注册首次调用后移除的监听器。"""
        def 包装(*参数):
            """先移除自身再调用原监听器。"""
            自身.取消监听(事件,包装)
            监听器(*参数)
        包装.listener=监听器
        return 自身.监听(事件,包装)

    def 前置监听(自身,事件,监听器):
        """在已有监听器之前注册。"""
        if 事件 not in 自身._注册表: 列表=[]#??空列表，判的是缺席不是 length
        else: 列表=自身._注册表[事件]
        列表.insert(0,监听器)
        自身._注册表[事件]=列表
        return 自身

    def 取消监听(自身,事件,监听器):
        """移除监听器，按注册时的函数或 once 包装器所代表的函数。"""
        if 事件 not in 自身._注册表:
            return 自身
        列表=自身._注册表[事件]
        for 下标 in range(len(列表)-1,-1,-1):
            已注册=列表[下标]
            原监听=getattr(已注册,'listener',None)
            if 已注册 is 监听器 or 原监听 is 监听器:
                列表.pop(下标)
                break
        return 自身

    def 移除监听器(自身,事件,监听器):
        """off 的别名。"""
        return 自身.取消监听(事件,监听器)

    def 移除全部监听器(自身,事件=None):
        """丢弃某一事件的监听器，或全部。"""
        if 事件 is None: 自身._注册表.clear()
        else: 自身._注册表.pop(事件,None)
        return 自身

    def 发出(自身,事件,*参数):
        """发出事件；返回是否有监听器运行。"""
        if 事件 not in 自身._注册表: return False
        列表=自身._注册表[事件]
        if len(列表)==0: return False
        for 监听器 in list(列表): 监听器(*参数)
        return True

    def 列出监听器(自身,事件):
        """某一事件的监听器列表副本。"""
        if 事件 not in 自身._注册表: return []#??空列表，判的是缺席不是 length
        return list(自身._注册表[事件])

    def 监听器数量(自身,事件):
        """某一事件的监听器数量。"""
        if 事件 not in 自身._注册表: return 0#??空列表，判的是缺席不是 length
        return len(自身._注册表[事件])

    def 设最大监听器(自身,*位置参数,**关键字参数):
        """Node 的最大监听器旋钮在此无效果。"""
        return 自身

    on=监听
    once=一次
    prependListener=前置监听
    off=取消监听
    removeListener=移除监听器
    removeAllListeners=移除全部监听器
    emit=发出
    listeners=列出监听器
    listenerCount=监听器数量
    setMaxListeners=设最大监听器

EventEmitter=事件发出器
__esModule=True
default={'EventEmitter':事件发出器}
