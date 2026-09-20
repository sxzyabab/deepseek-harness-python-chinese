包名='@deepseek-ai/dsh-typert-generator'
名称='typert-generator-invariant'
依赖=['invariants']

def 安装(上下文,失败):
    """无运行时检查：分析器与代码输出在 cordis 运行时之外执行。"""
    return

def 应用(上下文):
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 上下文.invariants.register(包名,安装)

__all__=['包名','名称','依赖','安装','应用']
name=名称
inject=依赖
apply=应用#框架槽
default=应用#框架槽
