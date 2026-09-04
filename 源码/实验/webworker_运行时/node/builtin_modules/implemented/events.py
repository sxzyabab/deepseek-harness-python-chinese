"""`node:events`：带 harness 代码所用成员的最小 EventEmitter。
发射顺序与监听器身份遵循 Node；基本 on/once/off/emit 集合之外的一律抛错。

对齐上游 `webworker-runtime/src/node/builtin_modules/implemented/events.ts`。
公开面中文名；Node 面经别名与 default 暴露英文名。
"""
__all__=['事件发射器','EventEmitter','__esModule','default']#中文与Node面

class 事件发射器:#事件发射器
    """Harness 注册的 `node:events` 子集：添加、移除与发射。"""

    def __init__(自身):#构造
        """空注册表。"""
        自身._注册表={}#事件到监听器列表

    def 监听(自身,事件,监听器):#注册监听器
        """注册监听器。"""
        列表=自身._注册表.get(事件) or []#取或新建列表
        列表.append(监听器)#追加
        自身._注册表[事件]=列表#写回
        return 自身#链式

    def 一次(自身,事件,监听器):#注册一次性监听器
        """注册首次调用后移除的监听器。"""
        def 包装(*参数):#包装器
            """先移除自身再调用原监听器。"""
            自身.取消监听(事件,包装)#先移除自身
            监听器(*参数)#再调用原监听器
        包装.listener=监听器#挂上原函数供匹配
        return 自身.监听(事件,包装)#经监听注册

    def 前置监听(自身,事件,监听器):#前置注册
        """在已有监听器之前注册。"""
        列表=自身._注册表.get(事件) or []#取或新建列表
        列表.insert(0,监听器)#插到前面
        自身._注册表[事件]=列表#写回
        return 自身#链式

    def 取消监听(自身,事件,监听器):#移除监听器
        """移除监听器，按注册时的函数或 once 包装器所代表的函数。"""
        列表=自身._注册表.get(事件)#取列表
        if 列表 is not None:#有列表
            for 下标 in range(len(列表)-1,-1,-1):#自后向前
                已注册=列表[下标]#当前项
                原监听=getattr(已注册,'listener',None)#once包装的原函数
                if 已注册 is 监听器 or 原监听 is 监听器:#匹配
                    列表.pop(下标)#删掉
                    break#只删一个
        return 自身#链式

    def 移除监听器(自身,事件,监听器):#off别名实现
        """off 的别名。"""
        return 自身.取消监听(事件,监听器)#委托取消监听

    def 移除全部监听器(自身,事件=None):#清除监听器
        """丢弃某一事件的监听器，或全部。"""
        if 事件 is None: 自身._注册表.clear()#清全部
        else: 自身._注册表.pop(事件,None)#清单事件
        return 自身#链式

    def 发射(自身,事件,*参数):#发射
        """发射事件；返回是否有监听器运行。"""
        列表=自身._注册表.get(事件)#取列表
        if 列表 is None or len(列表)==0: return False#无监听器
        for 监听器 in list(列表): 监听器(*参数)#拷贝后逐个调用
        return True#有运行

    def 监听器们(自身,事件):#取监听器副本
        """某一事件的监听器列表副本。"""
        return list(自身._注册表.get(事件) or [])#拷贝

    def 监听器数量(自身,事件):#监听器数量
        """某一事件的监听器数量。"""
        return len(自身._注册表.get(事件) or [])#长度或0

    def 设最大监听器(自身,*位置参数,**关键字参数):#最大监听器旋钮
        """Node 的最大监听器旋钮在此无效果。"""
        return 自身#无效果链式

    on=监听#Node面
    once=一次#Node面
    prependListener=前置监听#Node面
    off=取消监听#Node面
    removeListener=移除监听器#Node面
    removeAllListeners=移除全部监听器#Node面
    emit=发射#Node面
    listeners=监听器们#Node面
    listenerCount=监听器数量#Node面
    setMaxListeners=设最大监听器#Node面

EventEmitter=事件发射器#Node面别名
__esModule=True#CJS互操作
default={'EventEmitter':事件发射器}#默认导出
