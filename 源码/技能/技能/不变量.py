包名='@deepseek-ai/dsh-skill'#本包的不变量所有权名
名称='skill-invariant'#配套不变量插件名
注入=['invariants']#依赖invariants服务

__all__=['包名','名称','注入','安装','应用']#仅中文公开名

def 安装(子上下文=None,失败=None):#空安装器
    """无运行时不变量：提供方/运行时映射与带修订的缓存在注册表内原子变更，注册表没有可供交叉核对的独立变更事件或快照。"""
    return None#不挂运行时检查

def 应用(上下文对象):#注册本包不变量配套
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 上下文对象.invariants.register(包名,安装)#登记贡献

name=名称#Cordis 插件名槽
inject=注入#Cordis 依赖槽
apply=应用#Cordis 入口槽
default=应用#Cordis 默认导出槽
