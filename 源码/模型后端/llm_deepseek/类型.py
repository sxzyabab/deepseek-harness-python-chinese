"""DeepSeek 对话补全线路格式（OpenAI 兼容）。仅类型。

对齐上游 `llm-deepseek/src/types.ts`。公开面仅中文名；无英文别名。
字段键字面量对齐上游线路载荷（`model`、`messages`、`reasoning_content` 等）。
"""
from typing import Literal,NotRequired,TypedDict#字面量、可选字段与结构类型

__all__=(#仅中文公开名
    '线路请求','线路系统消息','线路用户消息','线路工具消息',
    '线路助手消息','线路消息','线路工具调用','线路工具',
    '线路块','线路选择','线路增量','线路工具调用增量',
    '线路用量','线路错误',
)#公开面结束

class 线路请求(TypedDict):#POST chat/completions 请求体
    model:str#模型id
    messages:list#消息列表
    stream:Literal[True]#必须流式
    stream_options:dict#必须带用量
    thinking:NotRequired[dict]#可选思考开关
    reasoning_effort:NotRequired[str]#可选推理力度
    tools:NotRequired[list]#可选工具
    temperature:NotRequired[float]#可选温度
    max_tokens:NotRequired[int]#可选最大token
    stop:NotRequired[list]#可选停止序列

class 线路系统消息(TypedDict):#系统角色消息
    role:Literal['system']#系统角色
    content:str#指令文本

class 线路用户消息(TypedDict):#用户角色消息
    role:Literal['user']#用户角色
    content:str#用户文本

class 线路工具消息(TypedDict):#工具角色消息
    role:Literal['tool']#工具角色
    tool_call_id:str#调用id
    content:str#结果文本

class 线路助手消息(TypedDict):#助手角色历史消息
    role:Literal['assistant']#助手角色
    content:str|None#可见文本或null
    reasoning_content:NotRequired[str]#可选推理文本
    tool_calls:NotRequired[list]#可选工具调用

线路消息=dict#线路消息联合（按 role 判别）

class 线路工具调用(TypedDict):#回放在助手历史上的已完成工具调用
    id:str#调用id
    type:Literal['function']#函数类型
    function:dict#名字与原始参数

class 线路工具(TypedDict):#请求 tools 数组的一条
    type:Literal['function']#函数类型
    function:dict#函数描述（name/description/parameters）

class 线路块(TypedDict):#已解析的 SSE data 载荷
    choices:NotRequired[list]#可选选择
    usage:NotRequired[dict|None]#可选用量

class 线路选择(TypedDict):#一条流式选择
    delta:NotRequired[dict]#可选增量
    finish_reason:NotRequired[str|None]#可选结束原因

class 线路增量(TypedDict):#一条流式选择的增量内容
    role:NotRequired[str]#可选角色
    content:NotRequired[str|None]#可选可见文本
    reasoning_content:NotRequired[str|None]#可选推理文本
    tool_calls:NotRequired[list]#可选工具调用增量

class 线路工具调用增量(TypedDict):#一次工具调用的流式片段
    index:int#并行下标
    id:NotRequired[str]#可选调用id
    type:NotRequired[Literal['function']]#可选函数类型
    function:NotRequired[dict]#可选函数片段

class 线路用量(TypedDict):#线路 token 记账
    prompt_tokens:int#提示词token（含缓存命中）
    completion_tokens:int#补全token
    prompt_cache_hit_tokens:NotRequired[int]#可选缓存命中
    prompt_cache_miss_tokens:NotRequired[int]#可选缓存未命中
    prompt_tokens_details:NotRequired[dict]#OpenAI兼容命中
    completion_tokens_details:NotRequired[dict]#可选推理token

class 线路错误(TypedDict):#非 2xx 错误体
    error:NotRequired[dict]#可选错误对象
