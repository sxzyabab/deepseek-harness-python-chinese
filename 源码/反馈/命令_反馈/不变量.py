"""`@deepseek-ai/dsh-command-feedback` 的本包拥有不变量配套。"""
包名='@deepseek-ai/dsh-command-feedback'#本包的不变量所有权名
名称='command-feedback-invariant'#配套不变量插件名
注入=['invariants']#依赖 invariants

def 安装(_上下文对象,_失败):
    """每条 feedback/record 是独立追加事实，无跨事件关系。"""
    return#空安装

def 应用(上下文对象):
    """注册本包的不变量配套。"""
    return 上下文对象.invariants.register(包名,安装)#登记

__all__=['包名','名称','注入','安装','应用']#仅中文公开名
name=名称#Cordis 插件名
inject=注入#Cordis 依赖声明
apply=应用#Cordis 插件入口
default=应用#Cordis 默认导出
