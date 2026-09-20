"""本包拥有的不变量配套。"""
from ...依赖 import cordis#外部依赖胶水
__all__=['包名','名称','依赖','安装','应用']

包名='@deepseek-ai/dsh-shell-env'#本包的不变量所有权名
名称='shell-env-invariant'#配套不变量插件名
依赖=['invariants']
name=名称
inject=依赖

def 安装(*位置参数):#空安装器，不挂运行时检查
    """无运行时不变量：环境注册表在每次注册/收集时校验所有权与已收集值；它不发布配套可以交叉核对的独立快照。"""
    return#不挂运行时检查

def 应用(上下文):#应用不变量配套插件
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 上下文.invariants.register(包名,安装)#登记贡献

apply=应用#Cordis插件入口（协议槽）
