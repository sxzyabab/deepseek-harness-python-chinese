"""`@deepseek-ai/dsh-session-query-sqlite` 的包内不变量配套。"""
包名='@deepseek-ai/dsh-session-query-sqlite'#本包名
名称='session-query-sqlite-invariant'#配套插件名
注入=['invariants']#依赖不变量服务

def 安装(子上下文=None,失败=None):
    """无运行时不变量：索引一致性由重建与对账测试钉住。"""
    return None#不挂运行时检查

def 应用(上下文对象):
    """登记不变量配套。"""
    return 上下文对象.invariants.register(包名,安装)#登记安装器

应用.name=名称#Cordis name 槽
应用.inject=注入#Cordis inject 槽
default=应用#Cordis 默认导出槽
