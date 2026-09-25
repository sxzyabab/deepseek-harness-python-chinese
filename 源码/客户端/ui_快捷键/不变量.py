"""向 invariants 登记本包：Host 入口无运行时关系。"""
包名='@deepseek-ai/dsh-client-ui-shortcuts'
名称='client-ui-shortcuts-invariant'
依赖=['invariants']

__all__=['包名','名称','依赖','安装','应用']

def 安装(上下文=None,失败=None):
    """无运行时检查：界面与命令目录由浏览器半边派生。"""
    return

def 应用(上下文):
    """向 invariants 登记本包检查，返回拆除器。"""
    return 上下文.invariants.register(包名,安装)

name=名称
inject=依赖
apply=应用
