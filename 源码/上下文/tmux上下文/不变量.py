"""@deepseek-ai/dsh-tmux-context 的本包拥有不变量配套。"""
包名='@deepseek-ai/dsh-tmux-context'
名称='tmux-context-invariant'
依赖=['invariants']

__all__=['包名','名称','依赖','应用','默认']

def 安装(*位置参数):
    """无运行时不变量：一次读数是外部 tmux 状态的每轮快照，会话里没有可跨事件检查的关系；调度与格式由流水线测试拥有。"""
    return

def 应用(上下文):
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 上下文.invariants.register(包名,安装)

默认=应用
name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
default=默认#框架槽
