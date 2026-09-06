"""`@deepseek-ai/dsh-anonymous-user-id` 的本包拥有不变量配套。"""
包名='@deepseek-ai/dsh-anonymous-user-id'#本包的不变量所有权名
名称='anonymous-user-id-invariant'#配套插件名
注入=['invariants']#依赖 invariants 服务

def 安装(子上下文=None,失败=None):
    """无运行时不变量：API 拥有私有记忆与一个尽力文件，无独立事件流。"""
    return None#不挂运行时检查

def 应用(上下文对象):
    """登记本包的不变量配套。"""
    return 上下文对象.invariants.register(包名,安装)#登记

__all__=['包名','名称','注入','安装','应用']#仅中文公开名
name=名称#Cordis 插件名
inject=注入#Cordis 依赖声明
apply=应用#Cordis 插件入口
default=应用#Cordis 默认导出
