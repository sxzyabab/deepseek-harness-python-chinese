"""`@deepseek-ai/dsh-credentials-local` 的包内不变量配套。"""
包名='@deepseek-ai/dsh-credentials-local'#本包名
名称='credentials-local-invariant'#配套插件名
依赖=['invariants']

def 安装(上下文,失败):#空安装器
    """无运行时不变量：生命周期约定由 credentials 包拥有。"""
    return#空安装

def 应用(上下文):#对外导出配套入口
    """登记本包的不变量配套。"""
    return 上下文.invariants.register(包名,安装)

__all__=['包名','名称','依赖','安装','应用']
name=名称
inject=依赖
apply=应用
default=应用
