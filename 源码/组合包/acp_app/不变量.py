"""`@deepseek-ai/dsh-acp-app` 的本包拥有不变量配套。

无运行时不变量：本包是启动生命周期提供方。
"""
包名='@deepseek-ai/dsh-acp-app'
名称='acp-app-invariant'
依赖=['invariants']

__all__=['包名','名称','依赖','安装','应用']

def 安装(上下文,失败):
    """空安装器，不挂运行时检查。"""
    return

def 应用(上下文):
    """注册本包的不变量配套，返回拆除器。"""
    return 上下文.invariants.register(包名,安装)

name=名称
inject=依赖
apply=应用
