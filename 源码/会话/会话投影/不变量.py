"""@deepseek-ai/dsh-session-projection 的本包拥有不变量配套。"""
from ...依赖 import cordis#外部依赖胶水
包名='@deepseek-ai/dsh-session-projection'#本包的不变量所有权名
名称='session-projection-invariant'#配套不变量插件名
注入=['invariants']#依赖 invariants 服务
name=名称#Cordis插件名
inject=注入#Cordis依赖声明
__all__=['包名','名称','注入','安装','应用']#仅中文公开名

def 安装(*位置参数):#空安装器
    """无运行时不变量：注册表在同步路径内强制重复键与 stateVersion 拒绝，并由规格证明。"""
    return#不挂运行时检查

def 应用(上下文对象):#注册本包不变量配套
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#登记空贡献

apply=应用#Cordis插件入口
