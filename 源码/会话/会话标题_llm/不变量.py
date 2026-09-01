"""@deepseek-ai/dsh-session-title-llm 的本包拥有不变量配套。"""
包名='@deepseek-ai/dsh-session-title-llm'#包名
名称='session-title-llm-invariant'#插件名
注入=['invariants']#依赖
name=名称#Cordis 插件名
inject=注入#Cordis 依赖
__all__=['包名','名称','注入','安装','应用']#公开面

def 安装(*位置参数):#空安装器
    """无运行时不变量：请求在派发前同步校验。"""
    return#不挂检查

def 应用(上下文对象):#登记不变量
    """注册不变量配套。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#登记

apply=应用#Cordis 插件入口
