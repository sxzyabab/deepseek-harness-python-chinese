'每种操作共用的卡片提案、已记录决定和用户操作结果'
from typing import NotRequired,TypedDict

__all__=['操作卡片提案','操作卡片决定','操作卡片视图']

# 声明合并没有运行时：消息来源 kind=action-cards；插件记录 plugin:action-cards/decision；投影键 actionCards。键不译。

class 操作卡片提案(TypedDict):
    '一次成功的 propose_action 收进的卡片'
    callId:str
    turn:int
    action:str
    title:str
    brief:str
    details:dict

class 操作卡片决定(TypedDict):
    '一张卡片的最新状态。replaced 由日志推导，不单独记录'
    callId:str
    action:str
    phase:str
    data:NotRequired[dict]

class 操作卡片视图(TypedDict):
    '当前打开会话的提案和决定，按调用标识索引，不进会话摘要'
    proposals:dict
    decisions:dict
