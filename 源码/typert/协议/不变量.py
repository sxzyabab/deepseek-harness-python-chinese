包名='@deepseek-ai/dsh-typert-protocol'
名称='typert-protocol-invariant'
依赖=['invariants']

def 安装(上下文,失败):
    """无运行时检查：装饰器标记与绑定是冻结私有声明。"""
    return

def 应用(上下文):
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 上下文.invariants.register(包名,安装)

__all__=['包名','名称','依赖','安装','应用']
name=名称
inject=依赖
apply=应用#框架槽
default=应用#框架槽
