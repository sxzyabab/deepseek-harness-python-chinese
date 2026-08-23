"""@deepseek-ai/dsh-jobs-local 的本包拥有不变量配套。"""
from ...依赖 import cordis#外部依赖胶水
已兑现=cordis.工具.已兑现#立刻兑现的拆除器

包名='@deepseek-ai/dsh-jobs-local'#本包的不变量所有权名
名称='jobs-local-invariant'#配套不变量插件名
注入=['invariants']#依赖invariants服务
name=名称#Cordis插件名
inject=注入#Cordis依赖声明

def 安装(子上下文=None,失败=None):#空安装器
    """无运行时不变量：`@deepseek-ai/dsh-jobs/invariant` 拥有每快照身份、状态、时间戳与所有者检查。本提供方的准入决定使用私有配置，必须在后端启动器跑之前失败；`LocalJobRegistry.start()` 对当前生产者同步强制它。发布后再重复一份合计只会把私有配置暴露给本配套，并不能验证失败关闭的启动前保证。"""
    return None#不挂运行时检查

def 应用(上下文对象):#注册本包不变量配套
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#登记并包成立即兑现的承诺

apply=应用#Cordis插件入口
