"""全提示词模型标题提供方。"""
from ..会话标题_llm import 登记会话标题llm提供方,会话标题llm配置模式

包名='@deepseek-ai/dsh-session-title-all-prompts-llm'
名称='session-title-all-prompts-llm'
依赖=['sessionTitle','llm','sessions']
配置=会话标题llm配置模式

__all__=['包名','名称','依赖','应用','默认','配置']

def 全量消息(消息列表):
    """取全部人类消息。"""
    return 消息列表

def 应用(上下文,配置值):
    """登记 all-prompts 自动模式提供方。"""
    登记会话标题llm提供方(上下文,配置值,名称,'all-prompts',全量消息)

默认=应用
name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
Config=配置#框架槽
default=默认#框架槽
