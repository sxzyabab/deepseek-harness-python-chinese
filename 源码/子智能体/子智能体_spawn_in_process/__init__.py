"""进程内 spawn 子智能体后端（对齐 upstream subagent-spawn-in-process）。"""
from ...依赖.schemastery import 字典字段,字符串字段#配置
from ..子智能体_in_process_driver import 启动进程内跑#共享驱动

名称='subagent-spawn-in-process'#Cordis 插件名
注入=['subagents']#依赖
配置=字典字段({'providerName':字符串字段(默认值='spawn')})#配置

__all__=['名称','注入','配置','应用']#公开面

class 进程内孵化提供方:
    """新鲜子体；不继承父对话。"""
    def __init__(自身,名):
        """记下提供方名与能力。"""
        自身.名称=名#中文名
        自身.能力={'agentOptions':True,'outputSchema':True,'depthLimit':True,'toolFilter':True,'persona':True}#能力
        自身.继承父上下文=False#契约

    def 启动(自身,请求):
        """启动一次性孵化子体。请求为 dict。"""
        return 启动进程内跑(请求,{})#新鲜子体

    def 准备可续跑(自身,请求=None):
        """准备可续跑规格。请求为 dict。"""
        return {}#无可续跑种子

def 应用(上下文,配置值):
    """加载 spawn 提供方。配置为 dict。"""
    名=配置值['providerName'] if 'providerName' in 配置值 else 'spawn'#提供方名
    上下文.subagents.登记提供方(进程内孵化提供方(名))#登记

name=名称#框架槽
inject=注入#框架槽
apply=应用#框架槽
Config=配置#框架槽
default=应用#框架槽
