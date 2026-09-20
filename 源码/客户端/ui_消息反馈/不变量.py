"""向 invariants 登记消息反馈 UI 包检查（拆除由生命周期规格证明）。"""
包名='@deepseek-ai/dsh-client-ui-message-feedback'
名称='client-ui-feedback-invariant'
依赖=['invariants']

__all__=['包名','名称','依赖','安装','应用']

def 安装(上下文,失败):
    """无运行时检查：生命周期规格证明拆除。"""
    return

def 应用(上下文):
    """向 invariants 登记本包检查，返回拆除器。"""
    return 上下文.invariants.register(包名,安装)

name=名称
inject=依赖
apply=应用
