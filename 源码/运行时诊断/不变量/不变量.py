"""不变量注册表服务的自检配套。"""
包名='@deepseek-ai/dsh-invariants'
名称='invariants-invariant'
依赖=['invariants']

def 安装(子上下文=None,失败=None):
    """无运行时不变量：注册所有权与子生命周期就是服务自身的变更边界；从同一注册表观察它们只会重复实现。"""
    return None

def 应用(上下文):
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 上下文.invariants.register(包名,安装)

__all__=['包名','名称','依赖','安装','应用']
name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
default=应用#框架槽
