"""Runtime 后端返回的、与界域无关的属性描述符。

对齐上游 `shared/cdp/property.ts`。公开面仅中文名。
"""
__all__=['运行时属性描述符','运行时内部属性描述符','运行时私有属性描述符']#仅中文公开名

class 运行时属性描述符:#属性描述符
    """不调用访问器即返回的一个 JavaScript 属性描述符。"""
    def __init__(自身,name,configurable,enumerable,value=None,writable=None,get=None,set=None,wasThrown=None,isOwn=None,symbol=None):#构造
        """保存属性描述符字段。"""
        自身.name=name#属性名
        自身.value=value#数据值
        自身.writable=writable#是否可写
        自身.get=get#getter
        自身.set=set#setter
        自身.configurable=configurable#是否可配置
        自身.enumerable=enumerable#是否可枚举
        自身.wasThrown=wasThrown#读取是否抛错
        自身.isOwn=isOwn#是否自有
        自身.symbol=symbol#符号键对象

class 运行时内部属性描述符:#内部属性描述符
    """如 `[[Prototype]]` 一类的引擎拥有属性。"""
    def __init__(自身,name,value=None):#构造
        """保存内部属性字段。"""
        自身.name=name#属性名
        自身.value=value#值

class 运行时私有属性描述符:#私有属性描述符
    """后端支持时暴露的一个引擎私有属性。"""
    def __init__(自身,name,value=None,get=None,set=None):#构造
        """保存私有属性字段。"""
        自身.name=name#属性名
        自身.value=value#值
        自身.get=get#getter
        自身.set=set#setter
