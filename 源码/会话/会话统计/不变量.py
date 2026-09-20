"""向 invariants 登记本包；无独立运行时检查。"""
包名='@deepseek-ai/dsh-session-stats'
名称='session-stats-invariant'
依赖=['invariants']

__all__=['包名','名称','依赖','应用','默认']

def 安装(*位置参数):
    """空安装器。"""
    return

def 应用(上下文):
    """登记不变量配套。"""
    return 上下文.invariants.register(包名,安装)

默认=应用
name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
default=默认#框架槽
