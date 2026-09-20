"""本包拥有的不变量配套。"""
包名='@deepseek-ai/dsh-tool-pwsh-persistent'#包名
名称='tool-pwsh-persistent-invariant'#插件名
依赖=['invariants']
__all__=['包名','名称','依赖','安装','应用']

def 安装(*位置参数):#空安装器
    """无运行时不变量。"""
    return None#空

def 应用(上下文):#注册本包不变量配套
    """注册本包的不变量配套。"""
    return 上下文.invariants.register(包名,安装)#登记贡献

name=名称#Cordis插件名
inject=依赖
apply=应用#Cordis插件入口
