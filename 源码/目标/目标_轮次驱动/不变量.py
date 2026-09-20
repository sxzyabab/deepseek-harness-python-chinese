"""向 invariants 登记本包；无独立运行时检查。"""
包名='@deepseek-ai/dsh-goal-round-driver'
名称='goal-round-driver-invariant'
依赖=['invariants']

def 安装(子上下文=None,失败=None):
    """无运行时不变量：轮次驱动不拥有独立事件协议。"""
    return None

def 应用(上下文):
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 上下文.invariants.register(包名,安装)

__all__=['包名','名称','依赖','安装','应用']
name=名称
inject=依赖
apply=应用
default=应用
