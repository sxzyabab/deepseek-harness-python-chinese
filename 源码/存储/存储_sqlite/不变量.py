"""向 invariants 登记本包；无独立运行时检查。"""
包名='@deepseek-ai/dsh-storage-sqlite'
名称='storage-sqlite-invariant'
依赖=['invariants']

def 安装(子上下文=None,失败=None):
    """无运行时不变量：耐久与布局正确性由介质往返测试钉住。"""
    return None

def 应用(上下文):
    """注册本包的不变量配套。"""
    return 上下文.invariants.register(包名,安装)

__all__=['包名','名称','依赖','安装','应用']
name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
default=应用#框架槽
