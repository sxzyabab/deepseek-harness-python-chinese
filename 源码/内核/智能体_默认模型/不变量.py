包名='@deepseek-ai/dsh-agent-default-model'#本包的不变量所有权名
名称='agent-default-model-invariant'#配套插件名（字面量不译）
注入=['invariants']#依赖 invariants 服务

__all__=('包名','名称','注入','安装','应用')#仅中文公开名

def 安装(*位置参数):
    """无运行时不变量：设置校验拥有唯一的可变值关系。位置参数由登记约定传入，此处忽略。"""
    return#不挂运行时检查

def 应用(上下文对象):
    """注册故意为空的不变量贡献，返回安装成功后已登记贡献的拆除器。"""
    return 上下文对象.invariants.register(包名,安装)#登记空贡献并返回拆除器

应用.name=名称#Cordis name 槽
应用.inject=注入#Cordis inject 槽
default=应用#Cordis 默认导出槽
