"""本包拥有的不变量配套。

无运行时不变量：本无状态服务定义拥有请求/结果类型，执行器与策略拥有观察。
"""
from ...依赖 import cordis#外部依赖胶水
包名='@deepseek-ai/dsh-shell'#本包的不变量所有权名
名称='shell-invariant'#配套不变量插件名
依赖=['invariants']
name=名称
inject=依赖

__all__=['包名','名称','依赖','安装','应用']

def 安装(*位置参数):#空安装器，不挂运行时检查
    """空安装器，不挂运行时检查。"""
    return#不挂运行时检查

def 应用(上下文):#应用不变量配套插件
    """注册 bash 不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 上下文.invariants.register(包名,安装)#登记贡献

apply=应用#Cordis插件入口（协议槽）
