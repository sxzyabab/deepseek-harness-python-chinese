"""`@deepseek-ai/dsh-lsp` 的本包拥有不变量配套。"""
包名='@deepseek-ai/dsh-lsp'
名称='lsp-invariant'
依赖=['invariants']

__all__=['包名','名称','依赖','应用','默认']

def 安装(_上下文,_失败):
    """路由表为私有原子状态，无可独立枚举的快照。"""
    return

def 应用(上下文):
    """注册本包的不变量配套。"""
    return 上下文.invariants.register(包名,安装)

默认=应用
name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
default=默认#框架槽
