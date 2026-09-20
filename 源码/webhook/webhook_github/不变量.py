"""GitHub webhook 适配器无运行时不变量配套。"""
包名='@deepseek-ai/dsh-webhook-github'
名称='webhook-github-invariant'
依赖=['invariants']

__all__=['包名','名称','依赖','应用','默认']

def 安装(上下文,失败):
    """无运行时不变量：认证与输入校验在精确 HTTP 操作边界完成。"""
    return

def 应用(上下文):
    """注册本包的不变量配套，返回拆除器。"""
    return 上下文.invariants.register(包名,安装)

默认=应用
name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
default=默认#框架槽
