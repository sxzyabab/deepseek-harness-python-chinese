包名='@deepseek-ai/dsh-settings-file'
名称='settings-file-invariant'
依赖=['invariants']

__all__=['包名','名称','依赖','安装','应用']

def 安装(上下文,失败):
    """无运行时不变量：文件往返由包测试证明；进程内提交关系由 settings 包拥有。"""
    return

def 应用(上下文):
    """注册本包的不变量配套，返回拆除器。"""
    return 上下文.invariants.register(包名,安装)

name=名称
inject=依赖
apply=应用
