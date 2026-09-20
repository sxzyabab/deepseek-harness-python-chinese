"""向 invariants 登记本包；准入在启动器前失败，快照关系由所属不变量拥有。"""
包名='@deepseek-ai/dsh-jobs-local'
名称='jobs-local-invariant'
依赖=['invariants']

def 安装(子上下文=None,失败=None):
    """无运行时不变量：每快照身份、状态、时间戳与所有者检查由所属不变量配套拥有。本提供方的准入决定使用私有配置，必须在后端启动器跑之前失败；启动器对当前生产者同步强制它。发布后再重复一份合计只会把私有配置暴露给本配套，并不能验证失败关闭的启动前保证。"""
    return None

def 应用(上下文):
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 上下文.invariants.register(包名,安装)

__all__=['包名','名称','依赖','安装','应用']
name=名称
inject=依赖
apply=应用#框架槽
default=应用#框架槽
