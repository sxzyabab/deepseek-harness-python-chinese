import math#有限数判定
import re#千分位插入

__all__=[#仅中文公开名
    '轨迹错误',
    '轨迹单元格种类',
    '轨迹记录身份',
    '格式化毫秒时长',
    '格式化已用秒数',
]#公开面结束

千分位插入=re.compile(r'\B(?=([0-9]{3})+(?![0-9]))')#千分位缝

class 轨迹错误(Exception):
    """本包异常基类。"""
    def __init__(自身,消息):
        """记下英文消息。"""
        super().__init__(消息)#消息原样英文

轨迹单元格种类=(#轨迹单元格种类闭集
    'system',#系统记录
    'user',#用户记录
    'context',#上下文注入
    'compacted',#压缩记录
    'message',#助手消息
    'tool',#工具调用
    'subtool',#子工具调用
)#种类结束

def 轨迹记录身份(单元格):#解析轨迹记录稳定身份
    """解析前置更旧投影记录后仍稳定的身份。"""
    if 'recordId' in 单元格 and 单元格['recordId'] is not None:#有投影稳定 id
        return 单元格['recordId']#用之
    调用标识=单元格['callId'] if 'callId' in 单元格 else None#工具调用 id
    种类=单元格['kind'] if 'kind' in 单元格 else None#记录种类
    if 调用标识 is not None:#有调用 id
        return f'{种类}\u0000call\u0000{调用标识}'#种类+调用
    源序号=单元格['sourceSeq'] if 'sourceSeq' in 单元格 else None#源事件序号
    if 源序号 is not None:#有源序号
        return f'{种类}\u0000seq\u0000{源序号}'#种类+序号
    下标=单元格['index'] if 'index' in 单元格 else None#展示序号
    return f'{种类}\u0000index\u0000{下标}'#回退到种类+展示序号

def 格式化毫秒时长(毫秒):#格式化毫秒时长
    """把毫秒时长格式化成千分位分隔的标签；未知时为破折号。"""
    if 毫秒 is None or type(毫秒) is bool or not isinstance(毫秒,(int,float)) or not math.isfinite(毫秒):#无效
        return '—'#破折号
    整数=str(round(毫秒))#四舍五入成整毫秒字符串
    return 千分位插入.sub(',',整数,count=0)+' ms'#插入千分位并加 ms

def 格式化已用秒数(秒):#把秒时长转成毫秒标签
    """把以秒给出的经过时长格式化成毫秒标签。"""
    return 格式化毫秒时长(None if 秒 is None else 秒*1000)#秒转毫秒后格式化
