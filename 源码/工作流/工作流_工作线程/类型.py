"""worker-thread 引擎的非协议线路词汇：`workerData` 初始化载荷，以及 worker 侧运行时消费的子端口接口。宿主/worker 消息定义在 `./协议`；传输的子请求与结果是供跨线程传递的普通 JSON。"""
from typing import NotRequired,Protocol,TypedDict#可选字段、协议与结构类型

class 工人上限(TypedDict):#worker 侧上限
    """worker 侧运行时强制执行的每次运行上限。宿主只保留自己能动手的旋钮（provider、disposeGraceMs）。"""
    maxConcurrentAgents:int#并发智能体上限（已自动解析；≥ 1）
    maxTotalAgents:int#智能体总数上限（失控循环挡板）
    maxItemsPerCall:int#单次组合子条目上限
    syncTimeoutMs:int#同步切片超时毫秒

class 工人初始化(TypedDict):#worker 初始化载荷
    """一次运行初始化用的 workerData 载荷（宿主 → worker，生成时一次）。"""
    meta:object#已校验的 meta 块（启动请求上的普通数据，宿主侧已校验）
    body:str#普通脚本正文，与启动请求携带的完全一致
    args:NotRequired[object]#该次运行的 args 值；跨线程传递就是隔离调用方的那份拷贝
    limits:工人上限#worker 强制执行的上限

class 子启动请求(TypedDict):#启动子智能体的请求
    """worker 请宿主为一次 agent() 调用启动的内容（选项已在 worker 侧校验）。"""
    prompt:str#子智能体的提示词文本
    schema:NotRequired[object]#结构化输出模式（若调用传入；已做过子集检查）
    provider:NotRequired[str]#每个子的提供方覆盖（若调用传入）
    model:NotRequired[str]#每个子的模型覆盖（若调用传入）

class 子结果(TypedDict):#子运行结果投影
    """子智能体 SubagentResult 跨端口的 JSON 投影。缝上的 stopReason 联合可合并扩展，因此线路上降级为 string——运行时只对 completed 分支。"""
    output:list#子智能体最终助手输出块
    structured:NotRequired[object]#结构化值，当且仅当请求带了模式且提供方兑现了它时存在
    stopReason:str#子运行为何结束（运行时只对 completed 分支）

class 子句柄(Protocol):#worker 侧子句柄
    """已启动子智能体在 worker 侧的句柄——子智能体缝运行句柄的 RPC 镜像，缩减到运行时实际消费的部分。"""
    @property#只读属性
    def id(自身):#子智能体 id（由宿主侧子智能体缝铸造）
        """子智能体 id。"""
        ...#协议桩
    @property#只读属性
    def result(自身):#兑现为子的终态子结果；仅在宿主报告基础设施故障时拒绝
        """子结果承诺。"""
        ...#协议桩
    def dispose(自身):#请宿主销毁该子；在宿主确认时兑现
        """销毁子运行。"""
        ...#协议桩
    def 销毁(自身):#中文销毁入口
        """销毁子运行。"""
        ...#协议桩

class 子端口(Protocol):#worker 侧子端口
    """运行时用来启动子智能体的 worker 侧端口——这条缝让执行核心不必知道线程边界。"""
    def startAgent(自身,请求):#在宿主上启动一个子智能体（agent() 钩子的启动半边）
        """提示词与已校验选项；返回已发布的子句柄；同步启动或提供方异步启动失败时拒绝。"""
        ...#协议桩
    def 启动子(自身,请求):#中文启动入口
        """启动子智能体。"""
        ...#协议桩
