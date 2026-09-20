"""向 invariants 登记用户提问 UI 包检查（注册表与线协议各自观察）。"""
包名='@deepseek-ai/dsh-client-ui-user-questions'
名称='client-ui-user-questions-invariant'
依赖=['invariants']

__all__=['包名','名称','依赖','安装','应用']

def 安装(上下文=None,失败=None):
    """无运行时检查：注册表 effect 与线协议各自拥有观察。"""
    return

def 应用(上下文):
    """向 invariants 登记本包检查，返回拆除器。"""
    return 上下文.invariants.register(包名,安装)

name=名称
inject=依赖
apply=应用
