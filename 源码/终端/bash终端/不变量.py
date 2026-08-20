"""@deepseek-ai/dsh-terminal-bash 的本包拥有不变量配套。"""
from cordis.工具 import 已兑现#立刻兑现的拆除器

包名='@deepseek-ai/dsh-terminal-bash'#本包的不变量所有权名
名称='terminal-bash-invariant'#配套不变量插件名
注入=['invariants']#依赖invariants服务
name=名称#Cordis插件名
inject=注入#Cordis依赖声明

def 安装(*位置参数):#空安装器，不挂运行时检查
    """无运行时不变量：就绪、终端缓冲与进程树状态是按会话私有的实现状态，此后端不发布独立生命周期流或快照。"""
    return#不挂运行时检查

def 应用(上下文对象):#应用不变量配套插件
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#登记空贡献并返回拆除器

apply=应用#Cordis插件入口
