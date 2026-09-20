"""向 invariants 登记本包；查询结果按次投影，无独立运行时检查。"""
包名='@deepseek-ai/dsh-session-query'
名称='session-query-invariant'
依赖=['invariants']

__all__=['包名','名称','依赖','应用','默认']

def 安装(_上下文,_失败):
    """无运行时不变量：查询结果是按次不可变投影，其谱系与事件关系在构建时校验。"""
    return

def 应用(上下文):
    """向 invariants 登记本包，返回拆除器。"""
    return 上下文.invariants.register(包名,安装)

默认=应用
name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
default=默认#框架槽
