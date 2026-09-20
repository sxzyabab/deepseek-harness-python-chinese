"""本包拥有的不变量配套。

无运行时不变量：环境注册表在每次变更/读取时校验所有权与收集值；它不发布配套可以交叉核对的独立快照。
"""
from ...依赖 import cordis#外部依赖胶水
包名='@deepseek-ai/dsh-tool-bash'#本包的不变量所有权名
名称='tool-bash-invariant'#配套不变量插件名
依赖=['invariants']
name=名称
inject=依赖

__all__=['包名','名称','依赖','安装','应用']

def 安装(子上下文=None,失败=None):#空安装器
    """空安装器，不挂运行时检查；子上下文与失败由登记约定传入。"""
    return None#不挂运行时检查

def 应用(上下文):#注册本包不变量配套
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 上下文.invariants.register(包名,安装)#登记贡献

apply=应用#Cordis插件入口（协议槽）
