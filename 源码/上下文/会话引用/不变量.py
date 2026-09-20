"""`@deepseek-ai/dsh-session-reference` 的本包拥有不变量配套。"""
包名='@deepseek-ai/dsh-session-reference'
名称='session-reference-invariant'
依赖=['invariants']

__all__=['包名','名称','依赖','应用','默认']

def 安装(子上下文=None,失败=None):
    """无运行时不变量：准备阶段返回构建时已校验的不可变每次调用快照；持久上下文的准入、冻结与回放由 agent/session 层拥有。"""
    return None

def 应用(上下文):
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 上下文.invariants.register(包名,安装)

默认=应用
name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
default=默认#框架槽
