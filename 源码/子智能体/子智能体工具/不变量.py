包名='@deepseek-ai/dsh-tool-subagent'#本包的不变量所有权名
名称='tool-subagent-invariant'#配套不变量插件名
依赖=['invariants']#依赖 invariants 服务

__all__=['包名','名称','依赖','安装','应用']#仅中文公开名

def 安装(上下文,失败):#空安装器
    """无运行时不变量：本面向模型的适配器没有独立生命周期流。"""
    return#不挂运行时检查

def 应用(上下文):#注册本包不变量配套
    """注册本包的不变量配套，返回拆除器。"""
    return 上下文.invariants.register(包名,安装)#同步登记

name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
