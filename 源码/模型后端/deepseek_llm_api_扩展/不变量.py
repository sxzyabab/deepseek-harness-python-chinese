"""向 invariants 登记本包；无独立运行时检查。"""
包名='@deepseek-ai/dsh-deepseek-llm-api-extensions'
名称='deepseek-llm-api-extensions-invariant'
依赖=['invariants']

__all__=['包名','名称','依赖','安装','应用']

def 安装(上下文,失败):
    """重复所有权与联合 accept 由注册表操作内强制。"""
    return

def 应用(上下文):
    """注册本包的不变量配套，返回拆除器。"""
    return 上下文.invariants.register(包名,安装)

name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
