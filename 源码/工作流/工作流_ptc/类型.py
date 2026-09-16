"""工作流宾客输入，以及其 VM 钩子消费的子回调。PTC 把初始化数据、请求与结果当无损 JSON 传输。"""
from typing import NotRequired,TypedDict#可选字段与结构类型
from ...工作流.工作流.类型 import 工作流元数据#已校验元数据

__all__=[#仅中文公开名
    '工作者上限字段','工作者初始化字段','子启动请求字段','子结果字段',
    '子句柄','子端口',
]#公开面结束

工作者上限字段=('maxConcurrentAgents','maxTotalAgents','maxItemsPerCall','syncTimeoutMs')#宾客钩子执行的脚本上限

class 工作者上限(TypedDict):#宾客钩子执行的普通脚本上限
    maxConcurrentAgents:int#并发 agent() 上限（已自动解析；≥ 1）
    maxTotalAgents:int#一次运行的 agent() 总数（跑飞循环挡板）
    maxItemsPerCall:int#一次 parallel()/pipeline() 接受的条目数
    syncTimeoutMs:int#脚本最初同步片段的 VM 超时

工作者初始化字段=('meta','body','args','limits')#宿主在脚本运行前返回的初始化数据

class 工作者初始化(TypedDict):#宿主在脚本运行前返回的初始化数据
    meta:工作流元数据#已校验元数据块（start 请求上的普通数据，宿主侧校验）
    body:str#普通 JS 脚本正文，与 start 请求携带的完全一致
    args:NotRequired[object]#本次运行的 args，经 PTC JSON 通道拷贝
    limits:工作者上限#宾客钩子上限

子启动请求字段=('prompt','schema','provider','model')#宾客校验脚本选项之后的一次 agent() 子请求

class 子启动请求(TypedDict):#宾客校验脚本选项之后的一次 agent() 子请求
    prompt:str#子提示词文本
    schema:NotRequired[object]#结构化输出模式（若调用传入；已做子集检查）
    provider:NotRequired[str]#每子提供方覆盖（若调用传入）
    model:NotRequired[str]#每子模型覆盖（若调用传入）

子结果字段=('output','structured','stopReason')#子 SubagentResult 的 JSON 投影

class 子结果(TypedDict):#子结果的 JSON 投影；缝的 stopReason 联合可合并扩展，线上退化为 string——运行时只对 completed 分支
    output:list#子最终助手输出块
    structured:NotRequired[object]#结构化值，当且仅当请求带 schema 且提供方兑现
    stopReason:str#子运行为何结束（运行时只对 completed 分支）

class 子句柄:#已发布子的宾客句柄，缩到 VM 钩子要用的部分
    """已发布子的宾客句柄。id 与 result 为载荷字段；拆除入口仅 销毁。"""
    id=None#子智能体 id（宿主侧由子智能体缝铸造）
    result=None#子终态结果任务；仅宿主报告基础设施故障时拒绝

    def 销毁(自身):#请宿主拆除该子
        """请宿主拆除该子；宿主确认后返回。"""
        raise NotImplementedError('ChildHandle.dispose')#由提供方实现

class 子端口:#与 PTC 传输无关的子回调
    """与 PTC 传输无关的子回调。"""
    def 启动智能体(自身,请求):#启动一个子智能体
        """在宿主上启动一个子智能体（agent() 钩子的启动半边）。请求是提示词与已校验选项。返回已发布子句柄；同步启动或提供方异步启动失败则抛。"""
        raise NotImplementedError('ChildPort.startAgent')#由提供方实现
