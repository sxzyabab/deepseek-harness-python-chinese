"""加载器配置表达式求值与插值。"""
import cosmokit

def 求值(上下文,表达式):
    """对照加载器上下文作用域求值一段表达式。"""
    class 作用域(dict):
        """把上下文属性暴露成求值局部名。"""
        def __getitem__(自身,键):
            if 键=='ctx':
                return 上下文#函数形参 ctx
            try:
                return getattr(上下文,键)#with (ctx) 属性查找
            except AttributeError:
                raise KeyError(键)#对应未定义名
    return eval(表达式,{'ctx':上下文},作用域())#new Function + with + eval

def 插值(上下文,值):
    """递归把 YAML `!js` 表达式节点替换成求值结果。"""
    if 是否js表达式(值):
        表达式=值['__jsExpr'] if isinstance(值,dict) else 值.__jsExpr#取出表达式
        return 求值(上下文,表达式)#求值替换
    if 值 is None or isinstance(值,(str,bytes,int,float,bool)):
        return 值#原始值原样返回
    if isinstance(值,list):
        return [插值(上下文,项) for 项 in 值]#数组逐项插值
    if isinstance(值,dict):
        def 变换(项,键):
            """对象值插值。"""
            return 插值(上下文,项)#递归
        return cosmokit.映射值(值,变换)#对象逐值插值
    return 值#其它对象原样返回

def 是否js表达式(值):
    """值为序列化后的加载器 JavaScript 表达式时为真。"""
    if 值 is None or isinstance(值,(str,bytes,int,float,bool)):
        return False#原始值不是对象
    if isinstance(值,dict):
        return '__jsExpr' in 值#映射带表达式键
    return hasattr(值,'__jsExpr')#对象带表达式字段

evaluate=求值#英文别名
interpolate=插值#英文别名
isJsExpr=是否js表达式#英文别名
