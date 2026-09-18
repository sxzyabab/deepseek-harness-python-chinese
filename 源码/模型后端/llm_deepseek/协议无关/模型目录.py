"""每个 DeepSeek 协议共享的默认目录。"""
from .默认值 import 默认上下文窗口#默认窗口

__all__=('默认模型列表',)#仅中文公开名

默认模型列表=[
    {'id':'deepseek-flash','name':'DeepSeek-V41-Flash','contextWindow':默认上下文窗口,#V41 Flash
     'inputModalities':['text','image'],#支持图文
     'systemPromptUpdate':'in-history'},#系统提示更新策略
    {'id':'deepseek-v4-pro','name':'DeepSeek-V4-Pro','contextWindow':默认上下文窗口,#Pro
     'description':'Stronger agentic coding, knowledge, and difficult reasoning; suited to complex or quality-critical tasks at higher cost.'},#描述
]#默认建议目录
