"""面向模型的工作流工具写入其调用方父 Session 的、浏览器安全的持久工作流记录事件。"""
from typing import NotRequired,TypedDict#可选字段与结构类型
from workflow.类型 import (#导入工作流持久词汇
    工作流智能体结局,#智能体结局
    工作流停止原因,#停止原因
)#来自工作流类型包

class 工具工作流运行开始数据(TypedDict):#运行开始记录
    """打开一条持久的顶层工作流运行记录。"""
    runId:str#运行标识（工作流运行标识品牌）
    name:str#展示名称

class 工具工作流智能体开始数据(TypedDict):#成员开始记录
    """在子 Session 发布后记录一名工作流成员。"""
    runId:str#运行标识
    seq:int#成员序号
    label:str#展示标签
    phase:NotRequired[str]#所属阶段
    childId:str#子会话标识（会话标识品牌）

class 工具工作流智能体结束数据(TypedDict):#成员结束记录
    """结算一名先前已开始的工作流成员。"""
    runId:str#运行标识
    seq:int#成员序号
    outcome:工作流智能体结局#成员结局

class 工具工作流运行结束数据(TypedDict):#运行结束记录
    """在存活资源静止后结算一次工作流运行。"""
    runId:str#运行标识
    stopReason:工作流停止原因#停止原因

# 会话事件映射扩充（仅文档；由记录器经 session.append 写入；对齐上游 SessionEventMap）：
# tool-workflow/run-start(data) — 打开一条顶层工作流记录；data 为稳定的运行身份与展示名称。
# tool-workflow/agent-start(data) — 记录一名已发布的工作流成员；data 含运行身份、成员序号、展示身份与子 Session。
# tool-workflow/agent-end(data) — 记录一名成员的结算；data 含运行身份、成对的成员序号与结局。
# tool-workflow/run-end(data) — 清理完成后关闭一条工作流记录；data 为稳定的运行身份与终态原因。

__all__=(#本模块公开符号
    '工具工作流运行开始数据',#运行开始
    '工具工作流智能体开始数据',#成员开始
    '工具工作流智能体结束数据',#成员结束
    '工具工作流运行结束数据',#运行结束
    '工作流智能体结局',#结局联合
    '工作流停止原因',#停止原因联合
)#公开符号结束
