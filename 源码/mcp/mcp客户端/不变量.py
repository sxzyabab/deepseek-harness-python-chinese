"""MCP 客户端桥接无运行时不变量配套：世代经工具注册表贡献，桥接不暴露独立的服务器到工具快照。"""
包名='@deepseek-ai/dsh-mcp-client'
名称='mcp-client-invariant'
依赖=['invariants']

__all__=['包名','名称','依赖','安装','应用']

def 安装(上下文,失败):
    """无运行时检查：桥接不暴露独立的服务器到工具快照。"""
    return

def 应用(上下文):
    """注册本包的不变量配套，返回拆除器。"""
    return 上下文.invariants.register(包名,安装)

name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
