"""@deepseek-ai/dsh-subagent-acp 的本包拥有不变量配套。"""
包名='@deepseek-ai/dsh-subagent-acp'#包名
名称='subagent-acp-invariant'#插件名
注入=['invariants']#依赖

__all__=['包名','名称','注入','安装','应用']#仅中文公开名

def 安装(上下文对象,失败):#空安装器
    """空安装器。"""
    return#无不变量

def 应用(上下文对象):#登记
    """注册本包的不变量配套，返回拆除器。"""
    return 上下文对象.invariants.register(包名,安装)#同步登记

name=名称#框架槽
inject=注入#框架槽
apply=应用#框架槽
