"""`@deepseek-ai/dsh-credentials-local` 的包内不变量配套。"""
包名='@deepseek-ai/dsh-credentials-local'#本包名
名称='credentials-local-invariant'#配套插件名
注入=['invariants']#依赖不变量服务

def 安装(上下文对象,失败):#空安装器
    """无运行时不变量：生命周期约定由 credentials 包拥有。"""
    return#空安装

def 应用(上下文对象):#对外导出配套入口
    """登记本包的不变量配套。"""
    return 上下文对象.invariants.register(包名,安装)#同步登记

name=名称#框架槽
inject=注入#框架槽
apply=应用#框架槽
