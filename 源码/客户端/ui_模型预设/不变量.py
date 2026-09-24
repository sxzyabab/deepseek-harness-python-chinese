"""向 invariants 登记权限预设 UI 包检查（无宿主事件所有权）。"""
包名='@deepseek-ai/dsh-client-ui-permission-presets'
名称='client-ui-permission-presets-invariant'
依赖=['invariants']

__all__=['包名','名称','依赖','安装','应用']

def 安装(上下文,失败):
    """无运行时检查：仅浏览器侧 Settings 控制器不拥有宿主事件。"""
    return

def 应用(上下文):
    """向 invariants 登记本包检查，返回拆除器。"""
    return 上下文.invariants.register(包名,安装)

name=名称
inject=依赖
apply=应用
