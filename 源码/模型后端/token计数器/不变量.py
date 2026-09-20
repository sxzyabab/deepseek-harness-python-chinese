"""向 invariants 登记本包；无运行时检查（估算按次输出，缓存按事件失效；用量折叠可非单调）。"""
包名='@deepseek-ai/dsh-token-meter'
名称='token-meter-invariant'
依赖=['invariants']

__all__=['包名','名称','依赖','安装','应用']

def 安装(上下文,失败):
    """空安装器，不挂运行时检查。"""
    return

def 应用(上下文):
    """注册本包的不变量配套，返回拆除器。"""
    return 上下文.invariants.register(包名,安装)

name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
