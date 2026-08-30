"""`@deepseek-ai/dsh-credentials-local` 的包内不变量配套。"""
from ...依赖 import cordis#外部依赖胶水
包名='@deepseek-ai/dsh-credentials-local'#本包名，用于登记所有权
名称='credentials-local-invariant'#配套插件名
注入=['invariants']#依赖不变量服务
name=名称#Cordis 插件名
inject=注入#Cordis 依赖声明

def 安装(子上下文=None,失败=None):#空安装器
    """无运行时不变量：服务定义配套（`dsh-credentials/invariant`）拥有 `credentials/updated` 生命周期约定；本提供方的文件/环境分层是异步 I/O，由其单元测试钉住。"""
    return None#空安装：运行时不变量由服务定义配套持有

def 应用(上下文对象):#对外导出配套入口
    """登记本包的不变量配套。`上下文对象` 须已注入不变量服务；返回安装成功后已登记项的 disposer。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#向不变量服务登记安装器

apply=应用#Cordis 插件入口
