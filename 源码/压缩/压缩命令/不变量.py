"""@deepseek-ai/dsh-command-compact 的本包拥有不变量配套。"""
from cordis.工具 import 已兑现#立刻兑现的拆除器

包名='@deepseek-ai/dsh-command-compact'#本包的不变量所有权名
名称='command-compact-invariant'#配套不变量插件名
注入=['invariants']#依赖invariants服务
name=名称#Cordis 插件名
inject=注入#Cordis 依赖声明

def 安装(子上下文=None,失败=None):#空安装器，不挂运行时检查
    """无运行时不变量：本命令适配器不拥有状态或事件流；压缩 seam 拥有成对的耐久事务，命令注册表拥有注册与派发生命周期。"""
    return None#不挂运行时检查

def 应用(上下文对象):#注册本包的不变量配套
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#登记并包成立即兑现的承诺

apply=应用#Cordis 插件入口
