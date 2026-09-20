包名='@deepseek-ai/dsh-agent-tool-presentation'#本包名（登记到 invariants 的所有权键）
名称='tool-presentation-invariant'#配套插件名
依赖=['invariants']#配套预占包所有权前必须具备的服务

__all__=('包名','名称','依赖','安装','应用')

def 安装(*位置参数):
    """空安装器。呈现关系由工具注册表持有，本包不另挂检查。位置参数由登记约定传入，此处忽略。"""
    return#不挂运行时检查

def 应用(上下文):
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 上下文.invariants.register(包名,安装)#登记空贡献并返回拆除器

应用.name=名称#Cordis name 槽
应用.inject=依赖
default=应用#Cordis 默认导出槽
