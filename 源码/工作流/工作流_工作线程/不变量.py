"""`@deepseek-ai/dsh-workflow-worker-thread` 的本包不变量配套。"""
包名='@deepseek-ai/dsh-workflow-worker-thread'#本包在不变量注册表中的名字
名称='workflow-worker-thread-invariant'#配套插件名
注入=['invariants']#依赖不变量服务

__all__=['包名','名称','注入','安装','应用']#仅中文公开名

def 安装(上下文=None):#空安装器，不登记运行时检查
    """无运行时不变量：这个进程边界实现不暴露同进程事件关系；由 worker 协议与已构建 worker 测试覆盖。"""
    _=上下文#空安装不读上下文
    return#空安装

def 应用(上下文):#把本包不变量登记到上下文
    """注册本包的不变量配套。上下文携带不变量服务；返回安装成功后该登记的拆除器。"""
    return 上下文.invariants.register(包名,安装)#同步登记

name=名称#Cordis 插件名槽
inject=注入#Cordis 依赖槽
apply=应用#Cordis 入口槽
