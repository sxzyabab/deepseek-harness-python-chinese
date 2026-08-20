"""线路安全的问答类型，不含 cordis/服务导入，好让浏览器类型链（apiproxy api → client）消费它们而不加载本包的 Context 扩增。"""
from typing import Literal,TypedDict,NotRequired#字面量、结构类型与可选字段

class 询问用户问题选项(TypedDict):#提供给用户的一条可选答案
    label:str#面向用户的标签
    description:NotRequired[str]#有能力的 UI 可渲染的可选额外上下文

class 询问用户问题意图(TypedDict):#调用方声明的展示意图：该问题就是这种决定，认得该标签的 UI 可按此展示；意图只改展示，从不改协议
    kind:Literal['plan-review']#提交评审的计划：detail 是 ask() 要求的计划 markdown
    approve:str#批准该计划的选项标签；点名的不是本问题自己的选项时，在 ask() 被拒绝

class 询问用户问题项(TypedDict):#用户提问请求里的一条问题
    id:str#调用方提供的稳定问题 id，会在答案里回显
    question:str#要展示的问题
    detail:NotRequired[str]#可选补充细节，与问题一起渲染，但不进选项标签
    header:NotRequired[str]#可选短标题/分组标签
    options:NotRequired[list[询问用户问题选项]]#UI 可渲染成菜单的可选选项
    multiSelect:NotRequired[bool]#是否可多选；默认单选
    intent:NotRequired[询问用户问题意图]#给有能力 UI 的可选展示意图；缺省则要通用选项列表

class 询问用户问题答案项(TypedDict):#一条问题的答案
    id:str#已回答的问题 id
    selected:list[str]#选中的选项标签；多选问题可以伴随自定义文本
    custom:NotRequired[str]#可选的自由文本「其他」答案

class 询问用户问题答案(TypedDict):#人类的回答
    answers:list[询问用户问题答案项]#按问题 id 键入的结构化答案
