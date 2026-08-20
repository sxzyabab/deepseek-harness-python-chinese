"""仅宿主使用的工作流请求与存活运行句柄。浏览器安全的持久词汇留在 `.类型`，这样 Client 程序永远不会导入 Agent 或宿主 Cordis 上下文声明。"""
from typing import NotRequired,TypedDict#可选字段与结构类型
from .类型 import 工作流元数据#元数据词汇

class 工作流启动请求(TypedDict):#调用方启动一次工作流运行时要给出的内容；按缝约定，meta 和 args 是普通 JSON 数据；parent 必填，因为脚本生成的每次 agent() 都归到该存活 Agent
    script:str#普通 JS 脚本正文（允许顶层 await；以 return <json-value> 结束）
    meta:工作流元数据#工作流身份块，普通 JSON 数据（由引擎做形态校验）
    args:NotRequired[object]#可选输入，原文作为 args 全局暴露给脚本
    subagentProvider:NotRequired[str]#可选的本次运行全局子提供方覆盖
    maxTotalAgents:NotRequired[int]#可选的本次运行子智能体总数上限
    parent:object#运行所代表的智能体（每个子运行的父；上游类型为 Agent）
    signal:NotRequired[object]#中止时取消该运行（上游类型为 AbortSignal）

class 工作流运行:#持有者所有的存活工作流句柄协议；result 永不拒绝；消费方可取消，且必须调用幂等的 dispose() 以等待脚本与子运行静止
    """持有者所有的存活工作流。提供方对象实现本协议（字段由实例赋值；方法由提供方覆写）。"""
    id=None#运行标识（工作流运行标识品牌）
    meta=None#脚本正文运行前即可取得的已校验 meta 块
    result=None#结算结果承诺（上游为 Promise<WorkflowResult>；兑现值为工作流结果）

    def 取消(自身,原因=None):#取消该运行及其子运行
        """取消该运行及其子运行。可选 reason 原文保留给诊断。"""
        raise NotImplementedError('WorkflowRun.cancel')#由提供方实现

    def 销毁(自身):#如有需要则取消，并等待有界结算与清理
        """如有需要则取消，并等待有界结算与清理。"""
        raise NotImplementedError('WorkflowRun.dispose')#由提供方实现
