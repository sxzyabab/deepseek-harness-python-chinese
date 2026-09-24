from typing import NotRequired,TypedDict

__all__=('智能体默认模型设置','插件配置')

class 智能体默认模型设置(TypedDict):
    """默认模型选择。"""
    provider:str
    model:str
    reasoningEffort:NotRequired[str]

class 插件配置(TypedDict):
    """默认模型选择的组合入口。"""
    provider:str
    model:str
    reasoningEffort:NotRequired[str]
