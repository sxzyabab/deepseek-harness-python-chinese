"""向 invariants 登记本包；无独立运行时检查。"""
包名='@deepseek-ai/dsh-session-query-sqlite'
名称='session-query-sqlite-invariant'
依赖=['invariants']

__all__=['包名','名称','依赖','应用','默认']

def 安装(子上下文=None,失败=None):
    """无运行时不变量：索引一致性由重建与对账测试钉住。"""
    return None

def 应用(上下文):
    """登记不变量配套。"""
    return 上下文.invariants.register(包名,安装)

默认=应用
name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
default=默认#框架槽
