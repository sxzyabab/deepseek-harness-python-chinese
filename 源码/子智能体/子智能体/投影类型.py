from typing import Literal,NotRequired,TypedDict#字面量、可选字段与结构类型

class 子智能体目录一次性条目(TypedDict):#一次性直接子发现行
    id:str#子会话 id
    createdAt:int#创建时刻
    mode:Literal['one-shot']#一次性
    label:NotRequired[str]#可选标签

class 子智能体目录可续跑条目(TypedDict):#可续跑直接子发现行
    id:str#子会话 id
    createdAt:int#创建时刻
    mode:Literal['continuable']#可续跑
    label:str#标签

子智能体目录条目=子智能体目录一次性条目|子智能体目录可续跑条目#目录条目联合

class 子智能体计时活动(TypedDict):#当前未到达 turn/end 的开放回合的同一切片边界
    since:int#开放回合的起点
    through:int#折进本投影切片的最新事件时间

class 子智能体计时投影(TypedDict):#一份有描述符的子会话的耐久活动回合计时
    settledMs:int#子体自身描述符之后、已完成回合累计的毫秒
    active:NotRequired[子智能体计时活动]#当前未结束回合的同一切片边界

class 子智能体一次性身份投影(TypedDict):#终态一次性子体的耐久身份
    mode:Literal['one-shot']#终态一次性子体
    label:NotRequired[str]#来自子描述符的可选耐久创建标签
    seq:int#折叠出本身份的 subagent/descriptor 事件的 seq

class 子智能体可续跑身份投影(TypedDict):#可恢复对话的耐久身份
    mode:Literal['continuable']#可恢复对话
    label:str#来自子描述符的耐久创建标签
    seq:int#折叠出的描述符事件 seq；自身后缀证明见一次性臂

子智能体身份投影=子智能体一次性身份投影|子智能体可续跑身份投影#身份投影联合（mode 判别）

# 会话投影图扩充（仅文档；对齐上游 SessionProjectionMap）：
# subagentCatalog: 子智能体目录条目[] — 按父目录事件顺序的直接子体。
# subagentTiming: 子智能体计时投影 — 有描述符的子智能体会话的活动回合时长。
# subagent: 子智能体身份投影 | None — null 哨兵 ⟺ 没有合法描述符（缺失、畸形或无法识别版本）；故意可序列化。
