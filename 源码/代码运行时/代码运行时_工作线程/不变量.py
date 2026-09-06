"""@deepseek-ai/dsh-code-runtime-worker-thread 的本包拥有不变量配套。"""
from ...依赖 import cordis#外部依赖胶水
包名='@deepseek-ai/dsh-code-runtime-worker-thread'#本包的不变量所有权名
名称='code-runtime-worker-thread-invariant'#配套不变量插件名
注入=['invariants']#依赖invariants服务

def 安装(子上下文=None,失败=None):#空安装器
    """无运行时不变量：此进程边界实现不暴露同进程事件关系；由工作线程协议与工作线程测试覆盖。"""
    return None#不挂运行时检查

def 应用(上下文对象):#注册本包不变量配套
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 上下文对象.invariants.register(包名,安装)#同步登记

name=名称#Cordis插件名槽
inject=注入#Cordis依赖槽
apply=应用#Cordis入口槽
