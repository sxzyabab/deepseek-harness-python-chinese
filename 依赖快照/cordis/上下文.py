"""Cordis 插件的根容器与子依赖容器。"""
from .工具 import 符号,取可追踪,原型映射#导入共享符号与可追踪包装

class 上下文:
    """Cordis 插件的根容器与子依赖容器。"""
    副作用=符号.副作用#副作用元数据符号
    过滤=符号.过滤#事件过滤符号
    隔离=符号.隔离#隔离映射符号
    拦截=符号.拦截#拦截映射符号

    @staticmethod
    def 是(值):
        """判断值是否为 Cordis 上下文。"""
        if 值 is None or not hasattr(值,'__dict__'):
            return False#空值或无字典
        字典=object.__getattribute__(值,'__dict__')#实例字典
        if 字典.get('_是上下文') or 字典.get(符号.是):
            return True#本层品牌
        原型=字典.get('_原型上下文')#原型
        if 原型 is not None:
            return 上下文.是(原型)#沿链
        return False#不是

    def __init__(自身):
        """创建根上下文并安装内建服务。"""
        from .光纤 import 光纤#延迟导入光纤
        from .反射 import 反射服务#延迟导入反射
        from .注册表 import 注册表服务#延迟导入注册表
        from .事件 import 事件服务#延迟导入事件
        from .日志 import 日志服务#延迟导入日志
        自身.__dict__[符号.隔离]=原型映射()#空隔离表
        自身.__dict__[符号.拦截]=原型映射()#空拦截表
        自身.__dict__[符号.是]=True#上下文品牌
        自身.__dict__['_是上下文']=True#探测字段
        自身.__dict__['root']=自身#根引用指向自身
        自身.__dict__['baseUrl']=None#根上下文默认没有基准 URL
        def 空栈():
            """根光纤没有外层调用栈。"""
            return []#空列表
        自身.__dict__['fiber']=光纤(自身,{},原型映射(),None,空栈)#创建根光纤
        自身.__dict__['reflect']=反射服务(自身)#安装反射服务
        自身.__dict__['registry']=注册表服务(自身)#安装插件注册表
        自身.__dict__['events']=事件服务(自身)#安装事件服务
        自身.__dict__['logger']=日志服务(自身)#安装日志服务
        自身.__dict__['fiber']._释放器.清空()#清掉构造期副作用

    def __repr__(自身):
        """检查器显示为带光纤名的上下文。"""
        光纤=查链(自身,'fiber')#光纤
        名称=光纤.名称 if 光纤 is not None else '?'#光纤名
        return f'Context <{名称}>'#展示

    def __getattribute__(自身,名):
        """普通属性读取走服务解析器。"""
        if 名 in ('__dict__','__class__','__repr__','__init__','__getitem__','__setitem__','__contains__','extend','isolate','intercept','是'):
            return object.__getattribute__(自身,名)#内部方法
        from .反射 import 反射服务#延迟导入反射
        return 反射服务.取属性(自身,名)#代理解析

    def __setattr__(自身,名,值):
        """普通属性写入走服务解析器。"""
        from .反射 import 反射服务#延迟导入反射
        反射服务.写属性(自身,名,值)#代理写入

    def __contains__(自身,名):
        """询问属性是否存在。"""
        from .反射 import 反射服务#延迟导入反射
        return 反射服务.有属性(自身,名)#代理 has

    def __getitem__(自身,键):
        """按键读取，符号键走原型链。"""
        if isinstance(键,str):
            return getattr(自身,键)#字符串走代理
        值,有=查链项(自身,键)#符号键
        if 有:
            return 值#命中
        raise KeyError(键)#没有

    def __setitem__(自身,键,值):
        """按键写入，符号键写到本层字典。"""
        if isinstance(键,str):
            setattr(自身,键,值)#字符串走代理
            return
        自身.__dict__[键]=值#符号键

    def extend(自身,元数据=None):
        """在当前作用域之上创建带额外元数据的子上下文。"""
        if 元数据 is None:
            元数据={}#空元数据
        阴影=自身.__dict__.get(符号.阴影)#读取当前阴影
        子=object.__new__(上下文)#子对象
        子.__dict__['_原型上下文']=取可追踪(自身,自身)#以可追踪父级为原型
        子.__dict__['_是上下文']=True#品牌
        子.__dict__[符号.是]=True#符号品牌
        for 键 in 元数据:
            子.__dict__[键]=元数据[键]#挂上自有属性
        if not 阴影:
            return 子#没有阴影则直接返回
        包=object.__new__(上下文)#再包一层
        包.__dict__['_原型上下文']=子#原型为子上下文
        包.__dict__[符号.阴影]=阴影#保留阴影
        包.__dict__['_是上下文']=True#品牌
        包.__dict__[符号.是]=True#符号品牌
        return 包#带阴影的子上下文

    def isolate(自身,服务名,标签=None):
        """为服务创建独立作用域的子上下文。"""
        子表=原型映射(自身[符号.隔离])#以父隔离表为原型
        子表[服务名]=标签 if 标签 is not None else object()#新标签或传入标签
        return 自身.extend({符号.隔离:子表})#用新隔离表扩展

    def intercept(自身,服务名,配置):
        """为在此上下文之下启动的插件追加某服务的拦截配置。"""
        子表=原型映射(自身[符号.拦截])#以父拦截表为原型
        子表[服务名]=配置#写入拦截配置
        return 自身.extend({符号.拦截:子表})#用新拦截表扩展

def 查链项(对象,属性):
    """沿上下文原型链查找自有键，返回值和是否命中。"""
    当前=对象#从接收者开始
    while 当前 is not None:
        字典=object.__getattribute__(当前,'__dict__')#本层字典
        if 属性 in 字典:
            return 字典[属性],True#命中
        当前=字典.get('_原型上下文')#上溯
    return None,False#未找到

def 查链(对象,属性):
    """沿上下文原型链取值，没有则为 None。"""
    值,有=查链项(对象,属性)#查找
    if 有:
        return 值#命中
    return None#没有

Context=上下文#英文别名
上下文.is_=上下文.是#英文别名
