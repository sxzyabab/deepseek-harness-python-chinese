包名='@deepseek-ai/dsh-experimental-tool-agent-team'
名称='tool-agent-team-invariant'
依赖=['invariants']

def 安装(子上下文=None,失败=None):
    """无运行时不变量：本面向模型的适配器不拥有独立状态或事件协议；成员作用域与任务 CAS 由团队域检查。"""
    return None

def 应用(上下文):
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 上下文.invariants.register(包名,安装)

name=名称
inject=依赖
apply=应用
