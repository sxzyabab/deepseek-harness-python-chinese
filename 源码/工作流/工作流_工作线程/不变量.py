"""`@deepseek-ai/dsh-workflow-worker-thread` 的本包不变量配套。"""
from ...依赖 import cordis#外部依赖胶水
已兑现=cordis.工具.已兑现#立刻兑现的拆除器

包名='@deepseek-ai/dsh-workflow-worker-thread'#本包在不变量注册表中的名字
名称='workflow-worker-thread-invariant'#配套插件名
注入=['invariants']#依赖不变量服务
name=名称#Cordis 插件名
inject=注入#Cordis 依赖声明
def 安装(_上下文=None):#空安装器，不登记运行时检查
    """无运行时不变量：这个进程边界实现不暴露同进程事件关系；由 worker 协议与已构建 worker 测试覆盖。"""
    return#空安装

def 应用(上下文):#把本包不变量登记到上下文
    """注册本包的不变量配套。上下文携带不变量服务；返回安装成功后该登记的 disposer。"""
    return 已兑现(上下文.invariants.register(包名,安装))#同步登记并包成 Promise

apply=应用#Cordis 插件入口
