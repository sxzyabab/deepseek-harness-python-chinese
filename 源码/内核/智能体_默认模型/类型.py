"""默认模型设置与插件配置的结构类型。

对齐上游 `agent-default-model/src/index.ts` 中的 `AgentDefaultModelSettings` 与 `Config`。
公开面仅中文名；字段键 `provider` / `model` / `reasoningEffort` 保持上游字面量（Settings 文档与组合配置键）。
"""
from typing import NotRequired,TypedDict#结构类型与可选字段

__all__=('智能体默认模型设置','插件配置')#仅中文公开名

class 智能体默认模型设置(TypedDict):#已存储并参与组合的默认模型选择
    """已存储并参与组合的默认模型选择。Settings 分节与组合入口叠层后的解析值落在此结构。"""
    provider:str#已注册的提供方路由
    model:str#提供方拥有的模型 id
    reasoningEffort:NotRequired[str]#适配器拥有的推理力度；缺省则用提供方/默认行为

class 插件配置(TypedDict):#默认模型选择的组合入口（插件 Config）
    """默认模型选择的组合入口。故意不含 `reasoningEffort`：完整保存的选择须能在下一模型无推理力度时清除旧值，而组合入口会再次被继承。"""
    provider:str#已注册的提供方路由
    model:str#提供方拥有的模型 id
