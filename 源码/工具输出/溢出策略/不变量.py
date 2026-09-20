"""`@deepseek-ai/dsh-spill-policy` 的本包拥有不变量配套。"""
包名='@deepseek-ai/dsh-spill-policy'
名称='spill-policy-invariant'
依赖=['invariants']

__all__=['包名','名称','依赖','安装','应用']

def 安装(子上下文=None,失败=None):
    """无运行时不变量：本包除在其拥有 seam 上强制的约定外，不暴露独立事件序列或可变数据关系。"""
    return None

def 应用(上下文):
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 上下文.invariants.register(包名,安装)

name=名称
inject=依赖
apply=应用
