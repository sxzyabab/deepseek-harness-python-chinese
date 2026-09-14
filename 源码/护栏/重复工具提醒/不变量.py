包名='@deepseek-ai/dsh-repeat-tool-reminder'#本包的不变量所有权名
名称='repeat-tool-reminder-invariant'#配套不变量插件名
注入=['invariants']#依赖invariants服务

__all__=['包名','名称','注入','安装','应用']#仅中文公开名

def 安装(子上下文=None,失败=None):
    """无运行时不变量：重复链私有于一条后执行监听器，不暴露独立配套可观察的包拥有事件或快照。"""
    return None#不挂运行时检查

def 应用(上下文对象):
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 上下文对象.invariants.register(包名,安装)#登记贡献并返回拆除器

应用.name=名称#Cordis name 槽
应用.inject=注入#Cordis inject 槽
default=应用#Cordis 默认导出槽
