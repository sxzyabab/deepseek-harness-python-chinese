"""向 invariants 登记本包；无独立运行时检查。"""
包名='@deepseek-ai/dsh-tool-jobs'
名称='tool-jobs-invariant'
依赖=['invariants']

def 安装(子上下文=None,失败=None):
    """无运行时不变量：此面向模型的适配器没有独立生命周期流；执行关系由它所调用的能力服务拥有。"""
    return None

def 应用(上下文):
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 上下文.invariants.register(包名,安装)

__all__=['包名','名称','依赖','安装','应用']
name=名称
inject=依赖
apply=应用#框架槽
default=应用#框架槽
