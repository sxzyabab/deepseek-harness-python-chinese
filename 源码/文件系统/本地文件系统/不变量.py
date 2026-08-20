"""@deepseek-ai/dsh-fs-local 的本包拥有不变量配套。"""
from cordis.工具 import 承诺#可等待结果

包名='@deepseek-ai/dsh-fs-local'#本包的不变量所有权名
名称='fs-local-invariant'#配套不变量插件名
注入=['invariants']#依赖invariants服务
name=名称#Cordis插件名
inject=注入#Cordis依赖声明

def 安装(子上下文=None,失败=None):#空安装器，不挂运行时检查
    """无运行时不变量：本包不暴露独立事件序列或可变数据关系，超出其拥有 seam 已强制的约定。"""
    return None#空配套

def 应用(上下文对象):#注册本包不变量配套
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    拆除器=上下文对象.invariants.register(包名,安装)#登记本包空安装器
    任务=承诺()#对齐上游 Promise.resolve
    任务.兑现(拆除器)#已决议拆除器
    return 任务#返回可等待结果

apply=应用#Cordis插件入口
