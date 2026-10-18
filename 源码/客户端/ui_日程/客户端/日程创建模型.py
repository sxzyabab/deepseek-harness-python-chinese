'从 schedule_create 的结果 JSON 取出任务。坏数据返回空，不抛'
import json
from .日程格式 import 任务名

__all__=['日程创建卡模型']

def 解析json(文本):
    '不是 JSON 就返回 None'
    try:
        return json.loads(文本)
    except Exception:
        return None

def 是记录(值):
    '普通对象，不是列表'
    return isinstance(值,dict)

def 首行(文本):
    '指令的第一行，去掉两端空白'
    下标=0
    长度=len(文本)
    while 下标<长度:
        if 文本[下标]=='\n':
            break
        if 文本[下标]=='\r':
            break
        下标=下标+1
    if 下标==长度:
        return 文本.strip()
    return 文本[:下标].strip()

def 收窄日程记录(值):
    '缺身份或不完整的规则返回 None。旧结果没有标题时用指令首行'
    if not 是记录(值):
        return None
    标识=值.get('id')
    指令=值.get('prompt')
    计划于=值.get('scheduledAt')
    种类=值.get('kind')
    if not isinstance(标识,str) or 标识=='':
        return None
    if not isinstance(指令,str) or 指令=='':
        return None
    if not isinstance(计划于,str):
        return None
    标题=值.get('title')
    if not (isinstance(标题,str) and 标题.strip()!=''):
        标题=首行(指令)
    if 标题=='':
        return None
    if 种类=='after':
        if not isinstance(值.get('afterSeconds'),(int,float)) or isinstance(值.get('afterSeconds'),bool):
            return None
        return {'id':标识,'kind':'after','title':标题,'prompt':指令,'afterSeconds':值['afterSeconds'],'scheduledAt':计划于}
    if 种类=='at':
        return {'id':标识,'kind':'at','title':标题,'prompt':指令,'scheduledAt':计划于}
    if 种类=='every':
        if not isinstance(值.get('everySeconds'),(int,float)) or isinstance(值.get('everySeconds'),bool):
            return None
        return {'id':标识,'kind':'every','title':标题,'prompt':指令,'everySeconds':值['everySeconds'],'scheduledAt':计划于}
    if 种类=='daily':
        if not isinstance(值.get('time'),str) or not isinstance(值.get('timeZone'),str):
            return None
        return {'id':标识,'kind':'daily','title':标题,'prompt':指令,'time':值['time'],'timeZone':值['timeZone'],'scheduledAt':计划于}
    if 种类=='weekly':
        星期=值.get('weekdays')
        if not isinstance(值.get('time'),str) or not isinstance(值.get('timeZone'),str):
            return None
        if not isinstance(星期,list) or not all(isinstance(项,(int,float)) and not isinstance(项,bool) for 项 in 星期):
            return None
        return {'id':标识,'kind':'weekly','title':标题,'prompt':指令,'time':值['time'],'timeZone':值['timeZone'],'weekdays':星期,'scheduledAt':计划于}
    if 种类=='cron':
        if not isinstance(值.get('expression'),str) or not isinstance(值.get('timeZone'),str):
            return None
        return {'id':标识,'kind':'cron','title':标题,'prompt':指令,'expression':值['expression'],'timeZone':值['timeZone'],'scheduledAt':计划于}
    return None

def 日程创建卡模型(块,工具名):
    '已结束的结果取出任务。还在跑就用参数里的标题，没有就用工具名'
    已结束='kind' in 块
    if 已结束:
        调用=块.get('call') if isinstance(块.get('call'),dict) else {}
        参数原文=调用.get('argsRaw') if isinstance(调用.get('argsRaw'),str) else ''
    else:
        参数原文=块.get('argsRaw') if 块.get('phase')=='start' and isinstance(块.get('argsRaw'),str) else ''
    输出=None
    if 已结束:
        内容=块.get('content')
        if isinstance(内容,list) and len(内容)==1:
            首=内容[0]
            if isinstance(首,dict) and 首.get('type')=='text' and isinstance(首.get('text'),str) and 首['text']!='':
                输出=首['text']
    任务=收窄日程记录(解析json('' if 输出 is None else 输出)) if 已结束 else None
    if 任务 is not None:
        标题=任务名(任务)
    else:
        解析=解析json(参数原文)
        待定=None
        if 是记录(解析):
            if isinstance(解析.get('title'),str) and 解析['title'].strip()!='':
                待定=解析['title'].strip()
            elif isinstance(解析.get('prompt'),str):
                行=首行(解析['prompt'])
                if 行!='':
                    待定=行
        标题=工具名 if 待定 is None else 待定
    return {'task':任务,'title':标题,'output':输出}
