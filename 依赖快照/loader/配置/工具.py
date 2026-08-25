"""加载器配置里的表达式求值与插值。"""
from ...cosmokit import 字典值转换#批量变换映射的值

表达式键='__jsExpr'#序列化后的表达式节点上存放源码的键

def 是否表达式节点(值):
    "值是序列化过的加载器表达式节点时为真"
    if isinstance(值,dict):
        return 表达式键 in 值#映射形态
    if 值 is None or isinstance(值,(str,bytes,bool,int,float)):
        return False#原始值不是节点
    return hasattr(值,表达式键)#对象形态

def 取表达式(节点):
    "从表达式节点里取出源码"
    return 节点[表达式键] if isinstance(节点,dict) else getattr(节点,表达式键)#源码

def 求值(上下文,表达式):
    "把上下文的属性当作局部名，求值一段表达式"
    class 上下文作用域(dict):
        "把上下文属性暴露成求值时的局部名"
        def __missing__(自身,键):
            "局部名没命中就去上下文上找同名属性"
            try:
                return getattr(上下文,键)#上下文属性
            except AttributeError:
                raise KeyError(键)#当成未定义名
    return eval(表达式,{'ctx':上下文,'上下文':上下文},上下文作用域())#求值

def 插值(上下文,值):
    "递归把配置里的表达式节点替换成求值结果"
    if 是否表达式节点(值):
        return 求值(上下文,取表达式(值))#换成求值结果
    if 值 is None or isinstance(值,(str,bytes,bool,int,float)):
        return 值#原始值原样返回
    if isinstance(值,list):
        return [插值(上下文,项) for 项 in 值]#逐项插值
    if isinstance(值,dict):
        return 字典值转换(值,lambda 项,键:插值(上下文,项))#逐值插值
    return 值#其它对象原样返回
