"""默认 DeepSeek 模型目录。"""
from .默认值 import 默认上下文窗口

__all__=['默认模型列表']

默认模型列表=[
    {
        'id':'deepseek-flash',
        'name':'DeepSeek-V41-Flash',
        'contextWindow':默认上下文窗口,
        'inputModalities':['text','image'],
        'systemPromptUpdate':'in-history',
    },
    {
        'id':'deepseek-v4-pro',
        'name':'DeepSeek-V4-Pro',
        'description':'更强的智能体编码、知识与困难推理；适合复杂或质量优先任务，成本更高。',
        'contextWindow':默认上下文窗口,
    },
]
