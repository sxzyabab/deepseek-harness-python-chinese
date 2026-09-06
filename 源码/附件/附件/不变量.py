"""`@deepseek-ai/dsh-attachment` 的本包拥有不变量配套。"""
包名='@deepseek-ai/dsh-attachment'#本包的不变量所有权名
名称='attachment-invariant'#配套插件名
注入=['invariants']#依赖不变量服务

def 安装(子上下文=None,失败=None):
    """无运行时不变量：此无状态 seam 拥有类型，由实现强制不可变存储检查。"""
    return None#不挂运行时检查

def 应用(上下文对象):
    """登记本包的不变量配套。"""
    return 上下文对象.invariants.register(包名,安装)#登记

__all__=['包名','名称','注入','安装','应用']#仅中文公开名
name=名称#Cordis 插件名
inject=注入#Cordis 依赖声明
apply=应用#Cordis 插件入口
default=应用#Cordis 默认导出
