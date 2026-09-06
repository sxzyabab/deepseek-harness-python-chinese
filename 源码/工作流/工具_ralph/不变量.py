"""`@deepseek-ai/dsh-tool-ralph` 的本包不变量配套。"""
包名='@deepseek-ai/dsh-tool-ralph'#本包在不变量注册表中的名字
名称='tool-ralph-invariant'#配套插件名
注入=['invariants']#依赖不变量服务

__all__=['包名','名称','注入','安装','应用']#仅中文公开名

def 安装(子上下文=None,失败=None):#空安装器，不登记运行时检查
    """无运行时不变量：这个面向模型的编排适配器不拥有独立事件流；由工作流与子智能体所有者校验它启动的运行和子生命周期。"""
    _=子上下文#空安装不读上下文
    _=失败#空安装不登记失败回调
    return None#不挂运行时检查

def 应用(上下文对象):#把本包不变量登记到上下文
    """注册本包的不变量配套，返回安装成功后该登记的拆除器。"""
    return 上下文对象.invariants.register(包名,安装)#同步登记

name=名称#Cordis 插件名槽
inject=注入#Cordis 依赖槽
apply=应用#Cordis 入口槽
