"""目标域的宿主侧词汇：实时视图、持久变更载荷、消息归因、回放折叠，以及作用域内的 goal/changed 事件。"""
from typing import Literal,TypedDict,NotRequired,Union#字面量、结构类型与联合
from .类型 import 目标标识,目标引用,目标快照,目标视图#身份、引用、快照与视图

目标操作=Literal['create','edit','pause','resume','complete','block','clear']#记入持久源变更的目标状态动词

class 目标快照变更元(TypedDict):#由持久 goal/change 事件提交的整快照目标变更
    kind:Literal['goal/change']#事件判别标签
    version:Literal[1]#载荷版本钉死为 1
    operation:Literal['create','edit','pause','resume','complete','block']#非清除操作
    goal:目标快照#变更后的完整快照
    roundsStarted:int#已接纳轮次
    createdAt:int#创建时间
    updatedAt:int#本条变更时间

class 目标清除变更元(TypedDict):#当前目标被清除时保留的墓碑
    kind:Literal['goal/change']#同一事件标签
    version:Literal[1]#载荷版本钉死为 1
    operation:Literal['clear']#清除操作
    cleared:目标引用#墓碑引用（修订比被清快照多一）
    clearedAt:int#清除时间

目标变更元=Union[目标快照变更元,目标清除变更元]#目标域自有会话事件携带的持久变更联合

class 目标消息来源(TypedDict):#已接纳续跑轮次的消息归因
    kind:Literal['goal']#来源判别
    goalId:目标标识#所属目标
    revision:int#入队时的修订
    round:int#已接纳的正数续跑轮次

class 折叠目标(TypedDict):#持久目标事实的纯回放折叠，不含进程内武装
    roundsStarted:int#当前目标已接纳的最高轮次
    goal:NotRequired[目标快照]#当前目标；清除后或首次创建前缺席
    createdAt:NotRequired[int]#当前目标创建时间；没有当前目标则缺席
    updatedAt:NotRequired[int]#当前目标变更时间；没有当前目标则缺席
    lastRef:NotRequired[目标引用]#最近一次变更引用，包括清除墓碑

class 目标已变更(TypedDict):#一次持久目标变更提交后的实时通知
    operation:目标操作#本次动词
    ref:目标引用#本次引用
    goal:NotRequired[目标视图]#清除墓碑时缺席

目标错误码=Literal[#被拒绝的目标读取与变更的稳定错误码
    'GOAL_AGENT_NOT_LIVE',#智能体不是注册表里的实时实例
    'GOAL_NOT_FOUND',#没有当前目标
    'GOAL_ALREADY_EXISTS',#未完成目标还在
    'GOAL_STALE_REVISION',#比较交换引用过期
    'GOAL_INVALID_OBJECTIVE',#目标陈述非法
    'GOAL_INVALID_MAX_ROUNDS',#轮次上限非法
    'GOAL_INVALID_BLOCK_REASON',#阻塞原因非法
    'GOAL_INVALID_EDIT',#编辑字段非法
    'GOAL_INVALID_TRANSITION',#阶段迁移非法
]#错误码结束
