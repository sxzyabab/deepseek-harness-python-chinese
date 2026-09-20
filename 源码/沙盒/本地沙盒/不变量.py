"""本地沙箱无运行时不变量配套。"""
包名='@deepseek-ai/dsh-sandbox-local'
名称='sandbox-local-invariant'
依赖=['invariants']

def 安装(*位置参数):
    """无运行时不变量：除所属服务已强制的约定外，本包不暴露独立事件序列或可变数据关系。"""
    return

def 应用(上下文):
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 上下文.invariants.register(包名,安装)

__all__=['包名','名称','依赖','安装','应用']
name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
default=应用#框架槽
