"""@deepseek-ai/dsh-tool-call-timeout-policy 的本包拥有不变量配套。"""
from ...依赖 import cordis#外部依赖胶水
包名='@deepseek-ai/dsh-tool-call-timeout-policy'#本包的不变量所有权名
名称='timeout-policy-invariant'#配套不变量插件名
注入=['invariants']#依赖invariants服务
name=名称#Cordis插件名
inject=注入#Cordis依赖声明

__all__=['包名','名称','注入','安装','应用']#仅中文公开名

def 安装(子上下文=None,失败=None):#空安装器；对齐上游 install
    """无运行时不变量：此无状态策略插件除所拦截的 seam 外，不拥有包内事件历史或可变数据关系。"""
    return None#不挂运行时检查

def 应用(上下文对象):#注册本包不变量配套；对齐上游 apply
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#登记并包成立即兑现的承诺

apply=应用#Cordis插件入口
