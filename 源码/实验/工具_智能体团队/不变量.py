from ...依赖 import cordis#外部依赖胶水

包名='@deepseek-ai/dsh-experimental-tool-agent-team'#本包的不变量所有权名
名称='tool-agent-team-invariant'#配套不变量插件名
注入=['invariants']#依赖invariants服务

def 安装(子上下文=None,失败=None):#空安装器
    """无运行时不变量：本面向模型的适配器不拥有独立状态或事件协议；成员作用域与任务 CAS 由团队域检查。"""
    return None#不挂运行时检查

def 应用(上下文对象):#注册本包不变量配套
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 上下文对象.invariants.register(包名,安装)#登记

name=名称#Cordis插件名
inject=注入#Cordis依赖声明
apply=应用#Cordis插件入口
