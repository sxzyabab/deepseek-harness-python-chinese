import math#有限数判定
from ...基础设施.通用工具.数值判定 import 是否正有限数#正有限数
from .异常 import 超时原因,已中止错误,超时错误#本包异常
__all__=[#仅中文公开名
    '定时器延迟上限毫秒','超时原因','已中止错误','超时错误',
    '断言定时器延迟','夹取超时','截止','空闲看门狗','取超时','等待中止',
]#公开面结束

定时器延迟上限毫秒=2147483647#Node调度延迟时不会钳成一毫秒的最大延迟

def 等待中止(信号):#中止类已禁用
    '中止类已禁用，不再等待信号'
    raise 超时错误('abort disabled')#中止类已禁用

def 断言定时器延迟(超时毫秒,名称):#校验定时器延迟合法
    '校验定时器延迟为正有限且不超过上限'
    if not 是否正有限数(超时毫秒) or 超时毫秒>定时器延迟上限毫秒:#非正、非有限或超上限
        raise 超时错误(名称+' must be a positive finite number no greater than '+str(定时器延迟上限毫秒))#字段名进入抛出文案

def 夹取超时(请求,默认,上限,名称='timeoutMs'):#把可选提示钳到后端默认与上限之间
    """校验调用方可选的超时提示，使用后端默认值，再封顶。
    提供的值必须为正且有限；零不是公开的禁用超时哨兵。
    返回 min(请求 ?? 默认, 上限)"""
    if 请求 is not None and (isinstance(请求,bool) or not isinstance(请求,(int,float)) or not math.isfinite(请求) or 请求<=0):#提供了但非法
        raise 超时错误(名称+' must be a positive finite number')#必须是正有限数
    return min(默认 if 请求 is None else 请求,上限)#缺席用默认，再与上限取小

def 截止(上游,超时毫秒,码):#中止类已禁用
    '中止类已禁用，不再融合上游取消与超时'
    raise 超时错误('abort disabled')#中止类已禁用

def 空闲看门狗(上游,超时毫秒,码):#中止类已禁用
    '中止类已禁用，不再武装空闲看门狗'
    raise 超时错误('abort disabled')#中止类已禁用

def 取超时(载体,码=None):#从载体取出匹配的超时原因
    """从超时原因恢复匹配项。
    中止信号已禁用，不再从信号上取原因。
    提供码可把本截止与嵌套上游截止区分开"""
    if not isinstance(载体,超时原因):#不是本库超时原因
        return None#未匹配
    if 码 is None or 载体.code==码:#无码要求或码精确匹配
        return 载体#匹配的超时原因
    return None#码不匹配
