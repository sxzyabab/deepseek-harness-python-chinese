"""向 invariants 登记目录选择器包检查。"""
包名='@deepseek-ai/dsh-host-directory-picker'
名称='directory-picker-invariant'
依赖=['invariants']

def 安装(上下文,失败):
    """本包暂无启动检查。"""
    return

def 应用(上下文):
    """登记本包不变量安装器，返回拆除器。"""
    return 上下文.invariants.register(包名,安装)

__all__=['包名','名称','依赖','安装','应用']
name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
default=应用#框架槽
