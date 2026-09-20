"""向 invariants 登记本包；无独立运行时检查。"""
包名='@deepseek-ai/dsh-storage'
名称='storage-invariant'
依赖=['invariants']

def 安装(子上下文=None,失败=None):
    """无运行时不变量：枢纽是纯注册表，一致性在调用点完全强制；不拥有可交叉核对的事件流或可变介质。"""
    return None

def 应用(上下文):
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 上下文.invariants.register(包名,安装)

__all__=['包名','名称','依赖','安装','应用']
name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
default=应用#框架槽
