"""@deepseek-ai/dsh-user-questions 的包内不变量配套。"""
from ...依赖 import cordis#外部依赖胶水
已兑现=cordis.工具.已兑现#立刻兑现的拆除器

包名='@deepseek-ai/dsh-user-questions'#本包名，用于登记所有权
名称='user-questions-invariant'#Cordis 配套插件名
注入=['invariants']#配套在预留包所有权之前必须已注入的服务
name=名称#Cordis插件名
inject=注入#Cordis依赖声明

def 安装(子上下文=None,失败=None):#空安装器
    """无运行时不变量：单一提供方槽在登记时校验，提问直接回到调用方；本能力缝不发布独立的请求/答案审计流。"""
    return None#不挂运行时检查

def 应用(上下文对象):#登记本包的不变量配套
    """登记本包的不变量配套，返回安装成功后已登记项的拆除器。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#向不变量服务登记安装器

apply=应用#Cordis插件入口
