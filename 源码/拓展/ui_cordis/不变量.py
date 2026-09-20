包名='@deepseek-ai/dsh-client-ui-cordis'
名称='client-ui-cordis-invariant'
依赖=['invariants']

__all__=['包名','名称','依赖','安装','应用']

def 安装(上下文,失败):
    """关系只在浏览器侧。"""
    return

def 应用(上下文):
    """注册本包的不变量配套，返回拆除器。"""
    return 上下文.invariants.register(包名,安装)

name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
