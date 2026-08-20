"""目标域的纯类型：goal 投影键声明的唯一归属处，以及它携带的持久载荷词汇，不含本包宿主侧导入。"""
from typing import Literal,TypedDict,NotRequired#字面量、结构类型与可选字段

目标标识=str#跨持久修订标识一个目标的品牌字符串
目标标识品牌='GoalId'#目标身份品牌名

class 目标引用(TypedDict):#一个精确目标修订的比较交换身份
    id:目标标识#稳定的目标身份
    revision:int#正数修订；每次持久变更递增

class 创建目标请求(TypedDict):#省略轮次上限时由服务配置补齐的创建输入
    objective:str#目标陈述
    maxGoalRounds:NotRequired[int]#可选轮次上限

class 创建目标结果(TypedDict):#一次创建的线上安全回执
    ref:目标引用#新建目标的引用

class 编辑目标请求(TypedDict):#编辑会改的字段；至少要有一个
    objective:NotRequired[str]#替换陈述
    maxGoalRounds:NotRequired[int]#替换上限

目标阶段=Literal['active','paused','blocked','complete']#持久续跑阶段

class 目标阻塞原因(TypedDict):#阻塞目标的可按机器路由、人类可读说明
    code:str#阻塞策略选定的稳定小写短横线分类
    message:str#展示给人类和模型的非空说明

class 目标快照(TypedDict):#每次非清除目标变更写入的完整持久状态
    id:目标标识#稳定的目标身份
    revision:int#正数修订
    objective:str#人类请求的完成目标
    phase:目标阶段#持久生命周期阶段
    maxGoalRounds:int#已接纳目标轮次的总上限
    blockedReason:NotRequired[目标阻塞原因]#仅当 phase 为 blocked 时出现

目标武装=Literal['armed','disarmed']#本实时进程是否可以自动续跑一个活跃目标

class 目标视图(TypedDict):#当前目标投影，含从会话日志导出的值与进程内武装
    id:目标标识#稳定的目标身份
    revision:int#正数修订
    objective:str#目标陈述
    phase:目标阶段#阶段
    maxGoalRounds:int#轮次上限
    roundsStarted:int#本目标已接纳的最高轮次号
    createdAt:int#创建变更的纪元毫秒
    updatedAt:int#最近一次变更的纪元毫秒
    activation:目标武装#进程内续跑资格；永不持久化
    blockedReason:NotRequired[目标阻塞原因]#仅阻塞时出现

class 目标投影(TypedDict):#goal 投影值：当前持久目标及其回放计数
    goal:目标快照#当前持久目标快照
    roundsStarted:int#本目标已接纳的最高轮次号
    createdAt:int#创建变更的纪元毫秒
    updatedAt:int#最近一次变更的纪元毫秒
