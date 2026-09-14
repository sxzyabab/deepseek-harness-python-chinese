包名='@deepseek-ai/dsh-util-crypto'#本包的不变量所有权名
名称='util-crypto-invariant'#配套不变量插件名
注入=['invariants']#依赖invariants服务
name=名称#Cordis插件名
inject=注入#Cordis依赖声明

def 安装(子上下文=None,失败=None):#空安装器
    """无运行时不变量：本纯工具包不拥有事件流或可变运行时数据；其值代数由单元测试强制。"""
    return None#不挂运行时检查

def 应用(上下文对象):#注册本包不变量配套
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 上下文对象.invariants.register(包名,安装)#登记贡献

apply=应用#Cordis插件入口
