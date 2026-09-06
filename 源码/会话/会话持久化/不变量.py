"""@deepseek-ai/dsh-session-persistence 的本包拥有不变量配套。"""
包名='@deepseek-ai/dsh-session-persistence'#本包的不变量所有权名
名称='session-persistence-invariant'#配套不变量插件名
注入=['invariants']#依赖

__all__=['包名','名称','注入','安装','应用']#公开面

def 安装(*位置参数):
    """空安装器。"""
    return#无不变量

def 应用(上下文对象):
    """登记不变量配套。"""
    return 上下文对象.invariants.register(包名,安装)#登记

应用.name=名称#Cordis name 槽
应用.inject=注入#Cordis inject 槽
default=应用#Cordis 默认导出槽
