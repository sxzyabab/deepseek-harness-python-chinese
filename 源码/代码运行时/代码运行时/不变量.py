from ...依赖 import cordis#外部依赖胶水
包名='@deepseek-ai/dsh-code-runtime'#本包的不变量所有权名
名称='code-runtime-invariant'#配套不变量插件名
注入=['invariants']#依赖 invariants 服务

def 安装(子上下文=None,失败=None):#空安装器
    """无运行时不变量：本包不暴露独立事件序列或可变数据关系，超出其拥有 seam 已强制的约定。"""
    return None#不挂运行时检查

def 应用(上下文对象):#注册本包不变量配套
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 上下文对象.invariants.register(包名,安装)#同步登记

name=名称#Cordis插件名槽
inject=注入#Cordis依赖槽
apply=应用#Cordis入口槽
