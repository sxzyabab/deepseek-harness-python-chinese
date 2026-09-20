包名='@deepseek-ai/dsh-tool-call-timeout-policy'#本包的不变量所有权名
名称='timeout-policy-invariant'#配套不变量插件名
依赖=['invariants']#依赖invariants服务

__all__=['包名','名称','依赖','安装','应用']#仅中文公开名

def 安装(子上下文=None,失败=None):
    """无运行时不变量：此无状态策略插件除所拦截的 seam 外，不拥有包内事件历史或可变数据关系。"""
    return None#不挂运行时检查

def 应用(上下文):
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 上下文.invariants.register(包名,安装)#登记贡献并返回拆除器

应用.name=名称#Cordis name 槽
inject=依赖#Cordis inject 槽
default=应用#Cordis 默认导出槽
