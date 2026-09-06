"""全提示词模型标题提供方（对齐 upstream session-title-all-prompts-llm）。"""
from ..会话标题_llm import 登记会话标题llm提供方,会话标题llm配置模式#共享策略
名称='session-title-all-prompts-llm'#Cordis 插件名
注入=['sessionTitle','llm','sessions']#依赖
配置=会话标题llm配置模式#配置模式
__all__=['名称','注入','配置','应用']#公开面

def 全量消息(消息列表):
    """取全部人类消息。"""
    return 消息列表#全量

def 应用(上下文,配置值):
    """登记 all-prompts 自动模式提供方。"""
    登记会话标题llm提供方(上下文,配置值,名称,'all-prompts',全量消息)#全量消息

应用.name=名称#Cordis name 槽
应用.inject=注入#Cordis inject 槽
应用.Config=配置#Cordis Config 槽
apply=应用#Cordis 插件入口
default=应用#Cordis 默认导出槽
