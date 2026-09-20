"""向 invariants 登记本包；无独立运行时检查。"""
包名='@deepseek-ai/dsh-session-log-export'
名称='session-export-invariant'
依赖=['invariants']

__all__=['包名','名称','依赖','应用','默认']

def 安装(_上下文,_失败):
    """无运行时不变量：命令注册表拥有生命周期配对，ApiProxy 拥有 ZIP 完整性。"""
    return

def 应用(上下文):
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 上下文.invariants.register(包名,安装)

默认=应用
name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
default=默认#框架槽
