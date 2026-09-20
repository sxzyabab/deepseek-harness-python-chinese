包名='@deepseek-ai/dsh-brand'
名称='brand-invariant'
依赖=['invariants']

__all__=['包名','名称','依赖','安装','应用']

def 安装(子上下文=None,失败=None):
    """无运行时不变量：本包是纯工具，不拥有事件流或可变运行时数据；其值代数由单元测试强制。"""
    return None

def 应用(上下文):
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 上下文.invariants.register(包名,安装)

name=名称
inject=依赖
apply=应用
