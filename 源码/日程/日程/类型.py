"""持久且面向模型的日程取值类型。"""
from typing import Literal,TypedDict,NotRequired,Union#字面量、结构类型与可选字段

日程标识=str#会话内唯一且永不复用的稳定提醒身份
日程标识品牌='ScheduleId'#会话内唯一且永不复用的稳定提醒身份品牌名

class 延迟日程记录(TypedDict):#由正延迟创建的持久一次性提醒
    id:日程标识#会话局部稳定身份
    kind:Literal['after']#延迟一次性提醒的规则判别
    prompt:str#创建时提供的已裁切提醒内容
    afterSeconds:int#创建时接受的正安全整数延迟
    scheduledAt:str#四位年份的RFC3339UTC目标

延迟日程记录字段=('id','kind','prompt','afterSeconds','scheduledAt')#字段名元组

class 绝对日程记录(TypedDict):#由绝对瞬间创建的持久一次性提醒
    id:日程标识#会话局部稳定身份
    kind:Literal['at']#绝对一次性提醒的规则判别
    prompt:str#创建时提供的已裁切提醒内容
    scheduledAt:str#四位年份的RFC3339UTC目标

绝对日程记录字段=('id','kind','prompt','scheduledAt')#字段名元组

class 固定频率日程记录(TypedDict):#下次目标仍与创建锚对齐的持久固定频率提醒
    id:日程标识#会话局部稳定身份
    kind:Literal['every']#固定频率重复提醒的规则判别
    prompt:str#创建时提供的已裁切提醒内容
    everySeconds:int#固定安全整数间隔，从不低于五分钟
    scheduledAt:str#尚未派发的最早锚对齐出现

固定频率日程记录字段=('id','kind','prompt','everySeconds','scheduledAt')#字段名元组

class 本地绝对输入(TypedDict):#schedule_create接受的结构化本地日历输入
    date:str#四位ISO日历日期
    time:str#本地墙钟时间，可选一到三位毫秒
    time_zone:str#显式UTC或IANAArea/Location时区

本地绝对输入字段=('date','time','time_zone')#字段名元组
绝对输入=Union[str,本地绝对输入]#schedule_create接受的绝对选择器
一次性日程记录=Union[延迟日程记录,绝对日程记录]#在仅id派发上终止的一次性记录变体
日程记录=Union[一次性日程记录,固定频率日程记录]#v1持久提醒记录联合

class 日程创建变更(TypedDict):#创建一条持久提醒记录
    version:Literal[1]#变更版本
    operation:Literal['create']#创建操作
    schedule:日程记录#新记录

class 日程删除变更(TypedDict):#删除一条当前活动提醒
    version:Literal[1]#变更版本
    operation:Literal['delete']#删除操作
    id:日程标识#目标id

class 一次性派发变更(TypedDict):#记录一条活动一次性提醒进入了持久派发历史
    version:Literal[1]#变更版本
    operation:Literal['dispatch']#派发操作
    id:日程标识#目标id

class 固定频率派发变更(TypedDict):#记录一次固定频率决定，并直接越过错过的出现
    version:Literal[1]#变更版本
    operation:Literal['dispatch']#派发操作
    id:日程标识#目标id
    acceptedAt:str#用来选择最近到期出现的墙钟决定时间

日程派发变更=Union[一次性派发变更,固定频率派发变更]#当前规则集支持的持久派发形态
日程变更=Union[日程创建变更,日程删除变更,日程派发变更]#严格版本1的持久日程变更联合
日程状态=Literal['scheduled','overdue']#由持久记录与墙钟派生的当前投递时机
日程投递模式=Literal['session-local']#固定v1投递边界：原会话必须在线

class 日程视图(TypedDict):#一条活动提醒的完整面向模型视图
    id:日程标识#会话局部稳定身份
    kind:Literal['after','at','every']#规则判别
    prompt:str#已裁切提醒内容
    scheduledAt:str#计划时刻
    state:日程状态#目标是否仍在未来
    deliveryMode:日程投递模式#提醒投递永不离开所属会话
    afterSeconds:NotRequired[int]#延迟秒数，仅after
    everySeconds:NotRequired[int]#间隔秒数，仅every

日程持久操作=Literal['create','list','delete']#持久屏障可能不确定的管理操作

class 非法正文错误(TypedDict):#空提醒正文返回的稳定错误
    code:Literal['invalid_prompt']#错误码
    message:str#错误消息

class 非法选择器错误(TypedDict):#缺失、冲突或不支持的规则选择器返回的稳定错误
    code:Literal['invalid_selector']#错误码
    message:str#错误消息

class 非法规则错误(TypedDict):#非法规则或管理参数返回的稳定错误
    code:Literal['invalid_rule']#错误码
    message:str#错误消息

class 非法时区错误(TypedDict):#非法或不支持的IANA时区返回的稳定错误
    code:Literal['invalid_time_zone']#错误码
    message:str#错误消息

class 非未来错误(TypedDict):#绝对目标不是严格未来时返回的稳定错误
    code:Literal['not_future']#错误码
    message:str#错误消息

class 时间越界错误(TypedDict):#计算出的瞬间无法使用四位UTC年时返回的稳定错误
    code:Literal['time_out_of_range']#错误码
    message:str#错误消息

class 频率过高错误(TypedDict):#固定频率规则比所支持的更频繁时返回的稳定错误
    code:Literal['frequency_too_high']#错误码
    message:str#错误消息

class 日志损坏错误(TypedDict):#持久日程流畸形时返回的稳定错误
    code:Literal['corrupt_schedule_log']#错误码
    message:str#错误消息

class 持久不确定错误(TypedDict):#必需的持久检查点未完成时返回的稳定错误
    code:Literal['persistence_uncertain']#错误码
    message:str#错误消息
    operation:日程持久操作#相关操作
    id:NotRequired[日程标识]#可选相关id

class 内部日程错误(TypedDict):#不披露内部异常的稳定回退
    code:Literal['internal_error']#错误码
    message:str#错误消息

日程工具错误=Union[#封闭的v1日程管理错误联合
    非法正文错误,#非法正文
    非法选择器错误,#非法选择器
    非法规则错误,#非法规则
    非法时区错误,#非法时区
    非未来错误,#非未来
    时间越界错误,#时间越界
    频率过高错误,#频率过高
    日志损坏错误,#日志损坏
    持久不确定错误,#持久不确定
    内部日程错误,#内部错误
]#联合结束
日程创建取值=Union[日程视图,日程工具错误]#规范schedule_create取值
日程列出取值=Union[list,日程工具错误]#规范schedule_list取值

class 删除已删结果(TypedDict):#成功删除
    id:日程标识#目标id
    deleted:Literal[True]#已删除

class 删除未找到结果(TypedDict):#非变更的未找到结果
    id:日程标识#目标id
    deleted:Literal[False]#未删除
    code:Literal['schedule_not_found']#未找到码

日程删除结果=Union[删除已删结果,删除未找到结果]#成功的schedule_delete取值
日程删除取值=Union[日程删除结果,日程工具错误]#规范schedule_delete取值
