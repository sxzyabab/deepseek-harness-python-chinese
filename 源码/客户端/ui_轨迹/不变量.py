"""向 invariants 登记轨迹 UI 包检查（无独立生命周期流）。"""
包名='@deepseek-ai/dsh-client-ui-trajectory'
名称='client-ui-trajectory-invariant'
依赖=['invariants']

__all__=['包名','名称','依赖','安装','应用']

def 安装(_上下文,_失败):
    """无独立生命周期流。"""
    return

def 应用(上下文):
    """向 invariants 登记本包检查，返回拆除器。"""
    return 上下文.invariants.register(包名,安装)

name=名称
inject=依赖
apply=应用
