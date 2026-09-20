"""插件清单线载荷形态。"""
from typing import Literal as 字面量,NotRequired as 非必需,TypedDict as 类型字典

__all__=['插件条目标识','插件纤程阶段','插件清单条目','预设插件启用','智能体预设插件行','智能体预设插件组','插件清单快照']

插件纤程阶段=字面量['pending','loading','active','failed','unloading']|None#对外阶段；None 表示已处置

预设插件启用=bool|字面量['conditional']#布尔启用，或条件式

class 插件清单条目(类型字典):#清单行
    entryId:str#Loader 树条目 id
    moduleName:str#插件模块名
    enabled:bool#有效启用
    fiberPhase:插件纤程阶段#根纤程阶段

class 智能体预设插件行(类型字典):#预设组合行
    entryId:str|None#行 id，可空
    moduleName:str#模块名
    enabled:预设插件启用#有效启用
    condition:非必需[str]#条件表达式
    fiberPhase:插件纤程阶段#纤程阶段

class 智能体预设插件组(类型字典):#预设分组
    id:str#预设 id
    trust:字面量['system','user']#信任级别
    name:非必需[str]#显示名
    isDefault:bool#是否默认
    broken:非必需[str]#损坏原因
    rows:list#组合行

class 插件清单快照(类型字典):#一次 list 投影
    managementAvailable:非必需[bool]#是否暴露持久管理
    entries:list#非 group 条目
    agentPresets:非必需[list]#可选预设组合

def 插件条目标识(值):
    """把条目 id 标成清单条目 id。"""
    return 值
