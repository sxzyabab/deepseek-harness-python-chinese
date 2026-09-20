"""本包拥有的不变量配套。"""
from ...依赖 import cordis#外部依赖胶水
包名='@deepseek-ai/dsh-tool-terminal'#本包的不变量所有权名
名称='tool-terminal-invariant'#配套不变量插件名
依赖=['invariants']#依赖invariants服务
name=名称#框架槽
inject=依赖#框架槽

def 安装(*位置参数):#空安装器，不挂运行时检查
    """空安装：无状态适配器只贡献工具与提示词指引；PTY 生命周期与后台任务由所组合服务持有。"""
    return#登记约定传入位置参数，此处忽略

def 应用(上下文):#应用不变量配套插件
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 上下文.invariants.register(包名,安装)#登记贡献

apply=应用#框架槽
