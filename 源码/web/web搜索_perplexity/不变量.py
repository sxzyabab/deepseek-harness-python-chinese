"""`@deepseek-ai/dsh-web-search-perplexity` 的本包拥有不变量配套。"""
from ...依赖 import cordis#外部依赖胶水
包名='@deepseek-ai/dsh-web-search-perplexity'#本包的不变量所有权名
名称='web-search-perplexity-invariant'#配套不变量插件名
注入=['invariants']#依赖invariants服务
name=名称#Cordis插件名
inject=注入#Cordis依赖声明

__all__=['包名','名称','注入','安装','应用','name','inject']#公开面

def 安装(*位置参数):#空安装器，不挂运行时检查
    """无运行时不变量：本包不暴露独立事件序列或可变数据关系，超出其拥有 seam 已强制的约定。"""
    return#不挂运行时检查

def 应用(上下文对象):#应用不变量配套插件
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#登记空贡献并返回拆除器

apply=应用#Cordis插件入口
