"""`@deepseek-ai/dsh-command-feedback` 的本包拥有不变量配套。"""
from ...依赖 import cordis#外部依赖胶水
包名='@deepseek-ai/dsh-command-feedback'#本包的不变量所有权名
名称='command-feedback-invariant'#配套不变量插件名
注入=['invariants']#依赖 invariants

__all__=['包名','名称','注入','安装','应用']#仅中文公开名

def 安装(_上下文对象,_失败):#空安装器
    """每条 feedback/record 是独立追加事实，无跨事件关系。"""
    return#空安装

def 应用(上下文对象):#注册本包不变量配套
    """注册本包的不变量配套。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#登记
