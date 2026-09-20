"""向 invariants 登记主题 UI 包检查（一致性由行为规格覆盖）。"""
包名='@deepseek-ai/dsh-client-ui-theme'
名称='client-ui-theme-invariant'
依赖=['invariants']

__all__=['包名','名称','依赖','安装','应用']

def 安装(上下文=None,失败=None):
    """无运行时检查：Host、作用域与服务行为规格直接覆盖一致性。"""
    return

def 应用(上下文):
    """向 invariants 登记本包检查，返回拆除器。"""
    return 上下文.invariants.register(包名,安装)

name=名称
inject=依赖
apply=应用
