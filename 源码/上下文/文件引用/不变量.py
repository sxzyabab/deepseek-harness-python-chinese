"""`@deepseek-ai/dsh-file-reference` 的本包拥有不变量配套。"""
包名='@deepseek-ai/dsh-file-reference'#本包的不变量所有权名
名称='file-reference-invariant'#配套不变量插件名
注入=['invariants']#依赖 invariants

__all__=['包名','名称','注入','安装','应用']#仅中文公开名

def 安装(_上下文对象,_失败):
    """接口层不保留候选或生命周期状态。"""
    return#空安装

def 应用(上下文对象):
    """注册本包的不变量配套。"""
    return 上下文对象.invariants.register(包名,安装)#登记

应用.name=名称#Cordis name 槽
应用.inject=注入#Cordis inject 槽
default=应用#Cordis 默认导出槽
