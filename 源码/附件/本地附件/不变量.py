"""`@deepseek-ai/dsh-attachment-local` 的本包拥有不变量配套。"""
from ...依赖 import cordis#外部依赖胶水
包名='@deepseek-ai/dsh-attachment-local'#本包的不变量所有权名
名称='attachment-local-invariant'#配套不变量插件名
注入=['invariants','attachments']#依赖服务
name=名称#Cordis 插件名
inject=注入#Cordis 依赖声明

def 安装(子上下文=None,失败=None):#空安装器
    """无运行时不变量：不可变写入与已验证读取在后端边界直接强制。"""
    return None#不挂运行时检查

def 应用(上下文对象):#注册本包不变量配套
    """登记本包的不变量配套。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#向不变量服务登记安装器

apply=应用#Cordis 插件入口
