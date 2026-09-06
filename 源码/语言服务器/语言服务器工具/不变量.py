"""`@deepseek-ai/dsh-tool-lsp` 的本包拥有不变量配套。"""
包名='@deepseek-ai/dsh-tool-lsp'#本包的不变量所有权名
名称='tool-lsp-invariant'#配套不变量插件名
注入=['invariants']#依赖 invariants

__all__=['包名','名称','注入','安装','应用']#仅中文公开名

def 安装(_上下文对象,_失败):
    """无状态适配器，仅贡献工具与提示段。"""
    return#空安装

def 应用(上下文对象):
    """注册本包的不变量配套。"""
    return 上下文对象.invariants.register(包名,安装)#登记

name=名称#Cordis 插件名槽
inject=注入#Cordis 依赖槽
apply=应用#Cordis 入口槽
default=应用#Cordis 默认导出槽
