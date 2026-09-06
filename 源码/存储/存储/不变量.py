"""`@deepseek-ai/dsh-storage` 的本包拥有不变量配套。"""
包名='@deepseek-ai/dsh-storage'#本包的不变量所有权名
名称='storage-invariant'#配套不变量插件名
注入=['invariants']#依赖 invariants 服务

def 安装(子上下文=None,失败=None):#空安装器
    """无运行时不变量：枢纽是纯注册表，一致性在调用点完全强制；不拥有可交叉核对的事件流或可变介质。"""
    return None#不挂运行时检查

def 应用(上下文对象):#注册本包不变量配套
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 上下文对象.invariants.register(包名,安装)#登记贡献

__all__=['包名','名称','注入','安装','应用']#仅中文公开名
name=名称#Cordis插件名
inject=注入#Cordis依赖声明
apply=应用#Cordis插件入口
default=应用#Cordis默认导出
