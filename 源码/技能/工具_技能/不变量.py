包名='@deepseek-ai/dsh-tool-skill'#本包的不变量所有权名
名称='tool-skill-invariant'#配套不变量插件名
依赖=['invariants']#依赖invariants服务

__all__=['包名','名称','依赖','安装','应用']#仅中文公开名

def 安装(子上下文=None,失败=None):#空安装器
    """无运行时不变量：此面向模型的适配器没有独立生命周期流；执行关系由其调用的能力缝拥有。"""
    return None#不挂运行时检查；子上下文与失败由登记约定传入

def 应用(上下文):#注册本包不变量配套
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 上下文.invariants.register(包名,安装)#登记贡献

name=名称#Cordis 插件名槽
inject=依赖#Cordis 依赖槽
apply=应用#Cordis 入口槽
default=应用#Cordis 默认导出槽
