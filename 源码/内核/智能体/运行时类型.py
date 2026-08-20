"""公开的智能体类型常量、在线运行时事件名，以及句柄/选项/决策词汇。

对齐上游 `agent/src/runtime-types.ts`。公开面仅中文名；状态／来源／决策字面量与 TypedDict 字段键保持上游 wire 名。
可持久化文字记录事实与轮次/步骤边界仍属会话包事件。
模型选择类型属 `模型选择.py`；已消费工作账本属 `已消费工作.py`。
"""
from typing import Literal,NotRequired,TypedDict#字面量、可选字段与结构类型
from session import 智能体取消原因#再导出取消原因，对齐上游 runtime-types 对 session 的再导出

__all__=(#仅中文公开名
    '智能体取消原因',
    '空闲','运行中','智能体状态',
    '启动','恢复','清空','压缩','会话开始来源',
    '拒绝','进入','重试',
    '智能体选项','取消选项','预步骤拒绝','预步骤进入','请求错误重试',
    '智能体句柄协议',
)#公开面结束

空闲='idle'#没有驱动器在活动
运行中='running'#驱动器已唤醒
智能体状态=(空闲,运行中)#生命周期状态：idle⇄running；拆除不是第三种可观察状态

启动='startup'#种子创建
恢复='resume'#持久化加载
清空='clear'#清空会话
压缩='compact'#压缩会话
会话开始来源=(启动,恢复,清空,压缩)#会话生命周期来源；clear/compact 预留

拒绝='reject'#预步骤拒绝
进入='enter'#预步骤进入
重试='retry'#请求错误后重试

class 智能体选项(TypedDict):#可合并扩展的智能体创建选项；人设归系统提示词段落
    provider:NotRequired[str]#提供方路由（调用时必须已有注册适配器）
    model:NotRequired[str]#由所选提供方适配器解释的模型 id
    maxTokens:NotRequired[int]#每次对话模型请求的最大输出 token 数

class 取消选项(TypedDict):#智能体.取消 的选项
    keepInbox:NotRequired[bool]#保留排队与转向收件箱条目，而不是丢掉它们

class 预步骤拒绝(TypedDict):#预步骤拒绝进入
    kind:Literal['reject']#拒绝臂

class 预步骤进入(TypedDict):#预步骤进入提议步骤
    kind:Literal['enter']#进入臂
    messages:list#拟进入步骤的完整、带标识且冻结的用户消息批次

class 请求错误重试(TypedDict):#拥有模型请求恢复的监听器返回的重试动作
    kind:Literal['retry']#重试臂

class 智能体句柄协议:#公开的在线智能体句柄协议；字段由实例赋值，方法由循环实现覆写
    """每个插件面向的句柄：与会话共享身份，拥有收件箱投影与作用域上下文。"""
    id=None#与 session 共享的唯一身份
    options=None#本智能体请求使用的提供方路由与模型
    session=None#本智能体驱动的在线会话；其日志是可持久化真相源
    inbox=None#智能体拥有的可持久化待处理工作投影
    status=None#当前生命周期状态，每次 agent/status 变迁都镜像
    ctx=None#智能体作用域上下文；贡献是智能体本地的，拆除时解开

    def 取消(自身,原因,选项=None):#取消活动
        """清空排队与转向工作——除非 keepInbox——并中止活动轮次。没有活动时是空操作。"""
        raise NotImplementedError('智能体句柄协议.取消')#由循环实现

    def 等到空闲(自身):#等到完全停稳
        """在当前整智能体活动到达静止后兑现；跟随替换工作，但不标识任何特定消息的落定。"""
        raise NotImplementedError('智能体句柄协议.等到空闲')#由循环实现

    def 跑维护(自身,任务):#跑非轮次维护
        """从真正空闲阶段跑一次非轮次维护任务；公开状态保持 idle。"""
        raise NotImplementedError('智能体句柄协议.跑维护')#由循环实现

    def 发送(自身,消息,目标,唤醒):#投递消息
        """把已标识输入路由到收件箱边界，并可选唤醒驱动器。"""
        raise NotImplementedError('智能体句柄协议.发送')#由循环实现

    def 后续(自身,消息):#后续提示
        """排队一次普通后续轮次并唤醒驱动器。"""
        raise NotImplementedError('智能体句柄协议.后续')#由循环实现

    def 转向(自身,消息):#转向
        """为最近步骤提交转向；空闲驱动器会开始一轮。"""
        raise NotImplementedError('智能体句柄协议.转向')#由循环实现

    def 注入(自身,消息):#注入上下文
        """为下一个预步骤排队面向模型的上下文，不唤醒驱动器。"""
        raise NotImplementedError('智能体句柄协议.注入')#由循环实现

# 事件声明（仅文档；由注册表/循环经作用域载体派发；对齐上游 Cordis Events）：
# agent/created(payload) @mode emit：完全配置好的智能体与在线会话已发表；同步监听器失败否决发表。
# agent/disposed(payload) @mode emit：智能体离开注册表。
# agent/status(payload) @mode emit：状态 idle⇄running。
# agent/inbox/inserted|claimed|discarded(payload) @mode emit：收件箱在线通知。
# agent/session-start(payload) @mode emit：会话生命周期开始；不可否决。
# agent/pre-step(payload, next) @mode waterfall：预步骤决策 reject|enter。
# agent/request(payload, next) @mode waterfall：请求路由组合。
# agent/request-error(payload, next) @mode waterfall：恢复动作 retry 或缺省终态。
# agent/turn-stopping(payload) @mode serial：可完成轮次关闭前征求。
# agent/error(payload) @mode emit：步骤级错误通知。
