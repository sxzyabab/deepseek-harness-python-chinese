import time
from datetime import datetime as 日期时间类,timezone as 时区类#日期时间与固定偏移时区
__all__=['当前毫秒','毫秒转UTC的ISO文本','当前UTC的ISO文本']#仅中文公开名

UTC时区=时区类.utc#UTC时区的中文别名

def 当前毫秒()->int:
    '当前时刻的Unix纪元毫秒数，取整'
    return int(time.time()*1000)#秒转毫秒并取整

def 毫秒转UTC的ISO文本(毫秒:int|float)->str:
    '纪元毫秒转为带+00:00偏移的UTC的ISO8601文本'
    return 日期时间类.fromtimestamp(毫秒/1000,UTC时区).isoformat()#毫秒转秒后按UTC格式化

def 当前UTC的ISO文本()->str:
    '当前时刻的带+00:00偏移的UTC的ISO8601文本'
    return 日期时间类.now(UTC时区).isoformat()#取UTC当前时刻并格式化
