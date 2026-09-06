"""`@deepseek-ai/dsh-deepseek-llm-api-extensions` 的本包拥有不变量配套。"""
包名='@deepseek-ai/dsh-deepseek-llm-api-extensions'#本包的不变量所有权名
名称='deepseek-llm-api-extensions-invariant'#配套不变量插件名
注入=['invariants']#依赖 invariants 服务

__all__=['包名','名称','注入','安装','应用']#仅中文公开名

def 安装(上下文对象,失败):#空安装器
    """重复所有权与联合 accept 由注册表操作内强制。"""
    return#空安装

def 应用(上下文对象):#注册本包不变量配套
    """注册本包的不变量配套，返回拆除器。"""
    return 上下文对象.invariants.register(包名,安装)#同步登记

name=名称#框架槽
inject=注入#框架槽
apply=应用#框架槽
