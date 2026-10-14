'从 schedule_create 的结果 JSON 里取出任务'
import json
from .日程格式 import 任务名

__all__=['创建工具名','收窄日程记录','日程创建卡模型']

创建工具名='schedule_create'

def _解析(文本):
    '不是 JSON 则 None'
    if not isinstance(文本,str) or 文本=='':
        return None
    try:
        return json.loads(文本)
    except ValueError:
        return None

def _首行(文本):
    '指令第一行'
    if not isinstance(文本,str):
        return ''
    return 文本.split('\n',1)[0].strip()

def 收窄日程记录(值):
    '缺身份或规则字段则 None'
    if not isinstance(值,dict):
        return None
    标识=值['id'] if 'id' in 值 else None
    提示=值['prompt'] if 'prompt' in 值 else None
    计划=值['scheduledAt'] if 'scheduledAt' in 值 else None
    种=值['kind'] if 'kind' in 值 else None
    if not isinstance(标识,str) or 标识=='' or not isinstance(提示,str) or 提示=='' or not isinstance(计划,str):
        return None
    标题=值['title'] if 'title' in 值 and isinstance(值['title'],str) and 值['title'].strip()!='' else _首行(提示)
    if 标题=='':
        return None
    基={'id':标识,'title':标题,'prompt':提示,'scheduledAt':计划}
    if 种=='after' and 'afterSeconds' in 值 and isinstance(值['afterSeconds'],(int,float)) and not isinstance(值['afterSeconds'],bool):
        return {**基,'kind':'after','afterSeconds':值['afterSeconds']}
    if 种=='at':
        return {**基,'kind':'at'}
    if 种=='every' and 'everySeconds' in 值 and isinstance(值['everySeconds'],(int,float)) and not isinstance(值['everySeconds'],bool):
        return {**基,'kind':'every','everySeconds':值['everySeconds']}
    if 种=='daily' and isinstance(值.get('time'),str) and isinstance(值.get('timeZone'),str):
        return {**基,'kind':'daily','time':值['time'],'timeZone':值['timeZone']}
    if 种=='weekly' and isinstance(值.get('time'),str) and isinstance(值.get('timeZone'),str) and isinstance(值.get('weekdays'),list):
        return {**基,'kind':'weekly','time':值['time'],'timeZone':值['timeZone'],'weekdays':值['weekdays']}
    if 种=='cron' and isinstance(值.get('expression'),str) and isinstance(值.get('timeZone'),str):
        return {**基,'kind':'cron','expression':值['expression'],'timeZone':值['timeZone']}
    return None

def _结果文本(块):
    '恰好一块文本才算结果'
    内容=块['content'] if isinstance(块,dict) and 'content' in 块 else None
    if not isinstance(内容,list) or len(内容)!=1:
        return None
    第一=内容[0]
    if not isinstance(第一,dict) or 第一.get('type')!='text' or not isinstance(第一.get('text'),str) or 第一['text']=='':
        return None
    return 第一['text']

def _待定标题(参数原文):
    '还在跑的调用从参数里取标题'
    解析=_解析(参数原文)
    if not isinstance(解析,dict):
        return None
    if isinstance(解析.get('title'),str) and 解析['title'].strip()!='':
        return 解析['title'].strip()
    if not isinstance(解析.get('prompt'),str):
        return None
    标题=_首行(解析['prompt'])
    return 标题 if 标题!='' else None

def 日程创建卡模型(块,工具名):
    '任务、标题、失败时的原文'
    已结算=isinstance(块,dict) and 块.get('kind')=='tool-result'
    if 已结算:
        调用=块['call'] if 'call' in 块 and isinstance(块['call'],dict) else {}
        参数=调用['argsRaw'] if 'argsRaw' in 调用 and isinstance(调用['argsRaw'],str) else ''
        输出=_结果文本(块)
        任务=收窄日程记录(_解析(输出 if 输出 is not None else ''))
    else:
        参数=块['argsRaw'] if isinstance(块,dict) and 块.get('phase')=='start' and isinstance(块.get('argsRaw'),str) else ''
        输出=None
        任务=None
    if 任务 is None:
        待定=_待定标题(参数)
        标题=待定 if 待定 is not None else 工具名
    else:
        标题=任务名(任务)
    return {'task':任务,'title':标题,'output':输出}
