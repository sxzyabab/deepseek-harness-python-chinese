"""`@deepseek-ai/dsh-attachment` 的本包拥有不变量配套。"""
from ...依赖 import cordis#外部依赖胶水
包名='@deepseek-ai/dsh-attachment'#本包的不变量所有权名
名称='attachment-invariant'#配套插件名
注入=['invariants']#依赖不变量服务
name=名称#Cordis 插件名
inject=注入#Cordis 依赖声明

def 已兑现(值=None):#立刻兑现的操作任务
    """把同步结果包成可 wait 的任务。"""
    class _任务:#内联已决议任务
        def wait(自身): return 值#英文 wait
        def 等待(自身): return 值#中文等待
    return _任务()#返回任务

def 安装(子上下文=None,失败=None):#空安装器
    """无运行时不变量：此无状态 seam 拥有类型，由实现强制不可变存储检查。"""
    return None#不挂运行时检查

def 应用(上下文对象):#注册本包不变量配套
    """登记本包的不变量配套。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#向不变量服务登记安装器

apply=应用#Cordis 插件入口
