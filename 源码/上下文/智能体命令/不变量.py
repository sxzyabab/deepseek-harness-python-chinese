"""@deepseek-ai/dsh-agent-instructions 的本包拥有不变量配套。"""
包名='@deepseek-ai/dsh-agent-instructions'
名称='workspace-context-invariant'
依赖=['invariants']

__all__=['包名','名称','依赖','应用','默认']

def 安装(子上下文=None,失败=None):
    """无运行时不变量：回放有意容忍未知或畸形的工作区来源；其私有待处理/缓存状态转换由针对性流水线测试拥有。"""
    return None

def 应用(上下文):
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 上下文.invariants.register(包名,安装)

默认=应用
name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
default=默认#框架槽
