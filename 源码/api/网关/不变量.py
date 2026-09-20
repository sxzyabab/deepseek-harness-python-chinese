"""网关无运行时不变量配套：Host 调用会重新读取权威的 Cordis 与 Typert 状态，而 Client 方法、描述符与订阅在一个所拥有的 effect 内变更。"""
包名='@deepseek-ai/dsh-api-gateway'
名称='api-gateway-invariant'
依赖=['invariants']

__all__=['包名','名称','依赖','应用','默认']

def 安装(上下文,失败):
    """无运行时检查：权威状态在调用时重读，客户端贡献在 effect 内变更。"""
    return

def 应用(上下文):
    """注册本包的不变量配套，返回拆除器。"""
    return 上下文.invariants.register(包名,安装)

默认=应用
name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
default=默认#框架槽
