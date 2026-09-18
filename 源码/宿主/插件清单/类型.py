"""插件清单类型。"""
from typing import Literal,NotRequired,TypedDict#字面量与结构类型

__all__=['插件条目标识','插件光纤阶段','插件清单条目','预设插件启用','智能体预设插件行','智能体预设插件组','插件清单快照']#仅中文公开名

插件光纤阶段=Literal['pending','loading','active','failed','unloading']|None#对外阶段

预设插件启用=bool|Literal['conditional']#布尔或条件式

class 插件清单条目(TypedDict):#清单行
    entryId:str#Loader 树条目 id
    moduleName:str#插件模块名
    enabled:bool#有效启用
    fiberPhase:插件光纤阶段#根 Fiber 阶段

class 智能体预设插件行(TypedDict):#预设组合行
    entryId:str|None#行 id 或 null
    moduleName:str#模块名
    enabled:预设插件启用#有效启用
    condition:NotRequired[str]#条件表达式
    fiberPhase:插件光纤阶段#fiber 阶段

class 智能体预设插件组(TypedDict):#预设分组
    id:str#预设 id
    trust:Literal['system','user']#信任级别
    name:NotRequired[str]#显示名
    isDefault:bool#是否默认
    broken:NotRequired[str]#损坏原因
    rows:list[智能体预设插件行]#组合行

class 插件清单快照(TypedDict):#一次 list 投影
    managementAvailable:NotRequired[bool]#可选管理能力
    entries:list[插件清单条目]#非 group 条目
    agentPresets:NotRequired[list[智能体预设插件组]]#可选预设组合

def 插件条目标识(值):
    """品牌化条目 id。"""
    return 值#原样品牌
