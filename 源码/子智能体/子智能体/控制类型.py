"""客户端安全的完整后代行与浏览器续跑请求、回执、失败形状。"""
from typing import Literal,NotRequired,TypedDict

__all__=[
    '子智能体目录行','子智能体列举条目','子智能体地址',
    '子智能体提示请求','子智能体提示回执','子智能体打断回执',
]

class 子智能体目录行(TypedDict):
    """完整后代列举共用的子体字段。"""
    id:str
    activity:Literal['running','inactive']
    mode:Literal['one-shot','continuable']
    label:NotRequired[str]

class 子智能体子体列举行(TypedDict):
    """一条完整后代的子体行。"""
    kind:Literal['child']
    id:str
    activity:Literal['running','inactive']
    mode:Literal['one-shot','continuable']
    label:NotRequired[str]
    hasChildren:bool

class 子智能体诊断列举行(TypedDict):
    """一条完整后代的诊断行。"""
    kind:Literal['diagnostic']
    id:str
    reason:Literal['corrupt','unsupported','unavailable']

子智能体列举条目=子智能体子体列举行|子智能体诊断列举行

class 子智能体地址(TypedDict):
    """耐久父/子浏览地址。"""
    parentSessionId:str
    childSessionId:str
    mode:Literal['one-shot','continuable','unknown']

class 子智能体提示请求(TypedDict):
    """发给可续跑直接子体的一条人类消息。"""
    requestId:str
    parentSessionId:str
    childSessionId:str
    mode:Literal['continuable']
    delivery:Literal['queue','steer']
    content:list
    clientTimeZone:NotRequired[str]

class 子智能体提示回执(TypedDict):
    """收件箱接受后的消息身份。"""
    messageId:str

class 子智能体打断回执(TypedDict):
    """打断请求已准入的统一回执。"""
    accepted:Literal[True]
