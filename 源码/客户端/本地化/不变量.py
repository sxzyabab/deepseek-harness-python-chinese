"""向 invariants 登记本地化包检查（回退链由行为规格断言）。"""
包名='@deepseek-ai/dsh-client-locale'
名称='client-locale-invariant'
依赖=['invariants']

__all__=['包名','名称','依赖','安装','应用']

def 安装(上下文,失败):
    """无运行时检查：回退链解析与语言仓库行为由本包行为规格直接断言。"""
    return

def 应用(上下文):
    """向 invariants 登记本包检查，返回拆除器。"""
    return 上下文.invariants.register(包名,安装)

name=名称
inject=依赖
apply=应用
