"""向 invariants 登记本包；无独立运行时检查（可变关系由适配器注册与配置校验拥有）。"""
包名='@deepseek-ai/dsh-llm-pi-ai'
名称='llm-pi-ai-invariant'
依赖=['invariants']

__all__=['包名','名称','依赖','安装','应用']

def 安装(上下文,失败):
    """无运行时不变量：适配器注册与配置校验拥有可变值关系。"""
    return

def 应用(上下文):
    """注册本包的不变量配套，返回拆除器。"""
    return 上下文.invariants.register(包名,安装)

name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
