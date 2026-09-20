"""本包拥有的不变量配套。"""
包名='@deepseek-ai/dsh-fs-sandbox'#本包的不变量所有权名
名称='fs-sandbox-invariant'#配套不变量插件名
依赖=['invariants']#依赖invariants服务

__all__=['包名','名称','依赖','安装','应用']#仅中文公开名

def 安装(子上下文=None,失败=None):#空安装器
    """空安装：无状态适配器；策略与文件系统关系委托给各自拥有方。"""
    return None#登记约定传入子上下文与失败，此处忽略

def 应用(上下文):#注册本包不变量配套
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 上下文.invariants.register(包名,安装)#登记贡献

name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
default=应用#框架槽
