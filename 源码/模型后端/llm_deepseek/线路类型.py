"""DeepSeek 支持的 Anthropic Messages 请求协议子集。线路键保持英文。"""
from typing import Literal,NotRequired,TypedDict

__all__=['线路文本输入','线路内联图输入','线路文件图输入','线路思考块','线路工具使用块','线路工具结果块','线路消息','线路请求']

class 线路文本输入(TypedDict):
    type:Literal['text']
    text:str

class 线路内联图输入(TypedDict):
    type:Literal['image']
    source:dict

class 线路文件图输入(TypedDict):
    type:Literal['image']
    source:dict

class 线路思考块(TypedDict):
    type:Literal['thinking']
    thinking:str
    signature:NotRequired[str]

class 线路工具使用块(TypedDict):
    type:Literal['tool_use']
    id:str
    name:str
    input:dict

class 线路工具结果块(TypedDict):
    type:Literal['tool_result']
    tool_use_id:str
    content:list
    is_error:NotRequired[bool]

class 线路消息(TypedDict):
    role:Literal['user','assistant','system']
    content:list

class 线路请求(TypedDict):
    model:str
    stream:Literal[True]
    max_tokens:int
    messages:list
    thinking:dict
    system:NotRequired[str]
    output_config:NotRequired[dict]
    temperature:NotRequired[float]
    stop_sequences:NotRequired[list]
    tools:NotRequired[list]
