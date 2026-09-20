"""@deepseek-ai/dsh-lsp-stdio 的本包拥有不变量配套。"""
包名='@deepseek-ai/dsh-lsp-stdio'
名称='lsp-stdio-invariant'
依赖=['invariants']

__all__=['包名','名称','依赖','应用','默认']

def 安装(*位置参数):
    """无运行时不变量：进程池与按工作区队列是私有实现状态，本提供方不发布独立生命周期事件流或可枚举快照。"""
    return

def 应用(上下文):
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 上下文.invariants.register(包名,安装)

默认=应用
name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
default=默认#框架槽
