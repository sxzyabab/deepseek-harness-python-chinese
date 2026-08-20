"""`@deepseek-ai/dsh-fs-sandbox` 的本包拥有不变量配套。"""
from cordis.工具 import 已兑现#立刻兑现的拆除器

包名='@deepseek-ai/dsh-fs-sandbox'#本包的不变量所有权名
名称='fs-sandbox-invariant'#配套不变量插件名
注入=['invariants']#依赖invariants服务
name=名称#Cordis插件名
inject=注入#Cordis依赖声明

def 安装(子上下文=None,失败=None):#空安装器
    """无运行时不变量：此无状态适配器把策略与文件系统关系委托给各自拥有的 seam。"""
    return None#不挂运行时检查

def 应用(上下文对象):#注册本包不变量配套
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#登记并包成立即兑现的承诺

apply=应用#Cordis插件入口
