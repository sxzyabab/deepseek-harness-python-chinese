"""@deepseek-ai/dsh-user-questions 的包内不变量配套。"""
包名='@deepseek-ai/dsh-user-questions'#本包名，用于登记所有权
名称='user-questions-invariant'#Cordis 配套插件名
依赖=['invariants']

def 安装(子上下文=None,失败=None):#空安装器
    """无运行时不变量：单一提供方槽在登记时校验，提问直接回到调用方；本能力缝不发布独立的请求/答案审计流。"""
    return None#不挂运行时检查

def 应用(上下文):#登记本包的不变量配套
    """登记本包的不变量配套，返回安装成功后已登记项的拆除器。"""
    return 上下文.invariants.register(包名,安装)#向不变量服务登记安装器

__all__=['包名','名称','依赖','安装','应用']
name=名称
inject=依赖
apply=应用#Cordis插件入口
default=应用#Cordis默认导出
