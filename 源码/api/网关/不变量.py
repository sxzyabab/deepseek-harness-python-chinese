"""`@deepseek-ai/dsh-api-gateway` 的本包拥有不变量配套。

对齐上游 `gateway/src/invariant.ts`。公开面仅中文名。

无运行时不变量：Host 调用会重新读取权威的 Cordis 与 Typert 状态，而 Client 方法、描述符与 `$on` 订阅在一个所拥有的 effect 内变更。
"""
包名='@deepseek-ai/dsh-api-gateway'#本包的不变量所有权名
名称='api-gateway-invariant'#配套不变量插件名
注入=['invariants']#依赖 invariants 服务

__all__=['包名','名称','注入','安装','应用']#仅中文公开名

def 安装(上下文对象,失败):#空安装器
    """无运行时检查：权威状态在调用时重读，客户端贡献在 effect 内变更。"""
    return#空安装

def 应用(上下文对象):#注册本包不变量配套
    """注册本包的不变量配套，返回拆除器。"""
    return 上下文对象.invariants.register(包名,安装)#同步登记

name=名称#框架槽
inject=注入#框架槽
apply=应用#框架槽
