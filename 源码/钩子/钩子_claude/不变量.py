"""`@deepseek-ai/dsh-hooks-claude-code` 的本包不变量配套。"""
from ...依赖 import cordis#外部依赖胶水
包名='@deepseek-ai/dsh-hooks-claude-code'#本包名，用于登记所有权
名称='hooks-claude-code-invariant'#配套插件名
注入=['invariants']#依赖不变量服务
name=名称#Cordis插件名
inject=注入#Cordis依赖声明

def 安装(子上下文=None,失败=None):#空安装器
    """没有运行时不变量：本桥发布的是钩子协议会话事件，由那份配套拥有每条结果引用的调用事件。"""
    return None#不挂运行时检查

def 应用(上下文对象):#登记本包不变量配套
    """登记本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#向不变量服务登记空安装器

apply=应用#Cordis插件入口
