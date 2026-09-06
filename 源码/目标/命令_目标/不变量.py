"""@deepseek-ai/dsh-command-goal 的本包拥有不变量配套。"""
包名='@deepseek-ai/dsh-command-goal'#本包的不变量所有权名
名称='command-goal-invariant'#配套不变量插件名
注入=['invariants']#依赖invariants服务

def 安装(子上下文=None,失败=None):
    """无运行时不变量：本命令适配器不拥有事件流或状态投影；已接受的变更由目标域检查，命令分发行为由包测试覆盖。"""
    return None#不挂运行时检查

def 应用(上下文对象):
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 上下文对象.invariants.register(包名,安装)#登记

__all__=['包名','名称','注入','安装','应用']#仅中文公开名
name=名称#Cordis 插件名
inject=注入#Cordis 依赖声明
apply=应用#Cordis 插件入口
default=应用#Cordis 默认导出
