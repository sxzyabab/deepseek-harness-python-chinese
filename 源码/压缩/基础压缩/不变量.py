"""@deepseek-ai/dsh-compaction-basic 的本包拥有不变量配套。"""
包名='@deepseek-ai/dsh-compaction-basic'#本包的不变量所有权名
名称='compaction-basic-invariant'#配套不变量插件名
注入=['invariants']#依赖 invariants 服务

def 安装(子上下文=None,失败=None):
    """无运行时不变量：本包不暴露独立事件序列或可变数据关系，超出其拥有 seam 已强制的约定。"""
    return None#不挂运行时检查

def 应用(上下文对象):
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 上下文对象.invariants.register(包名,安装)#登记贡献并返回拆除器

应用.name=名称#Cordis name 槽
应用.inject=注入#Cordis inject 槽
default=应用#Cordis 默认导出槽
