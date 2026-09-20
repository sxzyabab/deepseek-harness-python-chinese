"""首提示词模型标题提供方。"""
from ..会话标题_llm import 登记会话标题llm提供方,会话标题llm配置模式,会话标题llm错误

包名='@deepseek-ai/dsh-session-title-first-prompt-llm'
名称='session-title-first-prompt-llm'
依赖=['sessionTitle','llm','sessions']
配置=会话标题llm配置模式

__all__=['包名','名称','依赖','应用','默认','配置']

def _选首条(消息列表):
    """只取第一条人类消息。"""
    if len(消息列表)==0:
        raise 会话标题llm错误('first-prompt title provider requires one human message')
    return [消息列表[0]]

def 应用(上下文,配置值):
    """登记 first-prompt 自动模式提供方。"""
    登记会话标题llm提供方(上下文,配置值,名称,'first-prompt',_选首条)

默认=应用
name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
Config=配置#框架槽
default=默认#框架槽
