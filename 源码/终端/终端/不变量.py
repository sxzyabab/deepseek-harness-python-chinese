"""`@deepseek-ai/dsh-terminal` 的本包拥有不变量配套。"""
from ...依赖 import cordis#外部依赖胶水
包名='@deepseek-ai/dsh-terminal'#本包的不变量所有权名
名称='terminal-invariant'#配套不变量插件名
注入=['invariants']#依赖invariants服务
name=名称#Cordis插件名
inject=注入#Cordis依赖声明

def 安装(子上下文=None,失败=None):#空安装器，不挂运行时检查
    """无运行时不变量：后端与按所有者作用域的会话注册表是私有可变状态，服务既不暴露独立生命周期流，也不暴露无作用域快照。"""
    return None#不挂运行时检查

def 应用(上下文对象):#应用不变量配套插件
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#登记空贡献并返回拆除器

apply=应用#Cordis插件入口
