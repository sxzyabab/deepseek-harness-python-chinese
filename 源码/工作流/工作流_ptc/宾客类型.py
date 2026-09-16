"""一次工作流宾客与其拥有宿主运行之间的 JSON 回调。"""
from typing import TypedDict#结构类型

__all__=[#仅中文公开名
    '已启动子字段','工作流子请求字段','工作流进度','工作流宾客宿主',
]#公开面结束

已启动子字段=('callId','childId')#宿主分配的已发布子引用

class 已启动子(TypedDict):#宿主分配的已发布子引用
    callId:int#本运行回调标识，由宿主分配
    childId:str#子智能体提供方发布的子身份

工作流子请求字段=('callId',)#寻址本运行拥有的一个子

class 工作流子请求(TypedDict):#寻址本运行拥有的一个子
    callId:int#宿主分配的回调标识

工作流进度=dict#进度事件：type 为 phase/log/agent-start/agent-end

class 工作流宾客宿主:#经 PTC 运行时 JSON 绑定命名空间暴露的宿主函数
    """经 PTC 运行时 JSON 绑定命名空间暴露的宿主函数。方法同步。"""
    def 开始(自身,输入):#读已校验脚本与输入
        """执行前读取已校验脚本及其输入。输入是空请求对象。返回本次运行输入。"""
        raise NotImplementedError('WorkflowGuestHost.begin')#由宿主实现
    def 启动子(自身,请求):#发布一个子
        """经配置的子智能体提供方发布一个子。请求是提示词与已校验脚本选项。返回宿主分配的子引用。"""
        raise NotImplementedError('WorkflowGuestHost.startChild')#由宿主实现
    def 子结果(自身,请求):#观察已发布子的终态
        """观察已发布子的终态结果。请求是宿主分配的子引用。返回子 JSON 结果；基础设施故障则抛。"""
        raise NotImplementedError('WorkflowGuestHost.childResult')#由宿主实现
    def 拆除子(自身,请求):#加入一个已发布子的拆除
        """加入一个已发布子的拆除。请求是宿主分配的子引用。宿主拆除完成后返回 None。"""
        raise NotImplementedError('WorkflowGuestHost.disposeChild')#由宿主实现
    def 进度(自身,事件表):#发布一批有序进度
        """为本工作流运行发布一批有序进度。事件表是脚本叙述与子生命周期数据，按发出顺序。宿主接纳每条后返回 None。"""
        raise NotImplementedError('WorkflowGuestHost.progress')#由宿主实现
