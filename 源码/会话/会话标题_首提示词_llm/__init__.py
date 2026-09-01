"""首提示词模型标题提供方（对齐 upstream session-title-first-prompt-llm）。"""
from ..会话标题_llm import 登记会话标题llm提供方,会话标题llm配置模式#共享策略
名称='session-title-first-prompt-llm'#Cordis 插件名
注入=['sessionTitle','llm','sessions']#依赖
配置=会话标题llm配置模式#配置模式
__all__=['名称','注入','配置','应用','默认']#公开面

def _选首条(消息们):#只取首条
    """只取第一条人类消息。"""
    if len(消息们)==0:#空
        raise Exception('first-prompt title provider requires one human message')#拒绝
    return [消息们[0]]#首条

def 应用(上下文,配置值):#登记提供方
    """登记 first-prompt 自动模式提供方。"""
    登记会话标题llm提供方(上下文,配置值,名称,'first-prompt',_选首条)#首条消息

apply=应用#Cordis 插件入口
default=应用#Cordis 默认导出
默认=应用#中文默认导出
