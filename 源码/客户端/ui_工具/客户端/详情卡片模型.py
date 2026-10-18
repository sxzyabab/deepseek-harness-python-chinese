import re
from .文案 import 中文文案
from .原始工具调用 import 解析工具调用,单结果文本
from .控制详情模型 import 控制详情
from .检视结果详情模型 import 检视结果详情
from .详情模型共享 import 详情json,详情记录,非空文本

__all__=['待办详情','详情卡片模型']

待办状态=frozenset(['completed','in_progress','pending'])
目标阶段=frozenset(['active','paused','blocked','complete'])
星期键=(
    'detail.weekday.1','detail.weekday.2','detail.weekday.3','detail.weekday.4',
    'detail.weekday.5','detail.weekday.6','detail.weekday.7',
)
零秒=re.compile(r':00\.000$')
零毫秒=re.compile(r'\.000$')
安全整数上限=9007199254740991

def 非负整数(值):
    '非负安全整数'
    return isinstance(值,int) and not isinstance(值,bool) and 0<=值<=安全整数上限

def 格式化日期(窗口,时刻文本,语言,回退):
    '浏览器 Intl 短日期。失败回退原文'
    try:
        日期=窗口.Date(时刻文本)
        毫秒=日期.getTime()
        if 毫秒!=毫秒:
            return 回退
        return 窗口.Intl.DateTimeFormat(语言,{
            'year':'numeric',
            'month':'short',
            'day':'numeric',
            'hour':'2-digit',
            'minute':'2-digit',
            'second':'2-digit',
            'timeZoneName':'short',
        }).format(日期)
    except Exception:
        return 回退

def 待办详情(参数):
    '从 todo_write 参数派生紧凑待办列表。字段非法则 None'
    if not isinstance(参数.get('todos'),list):
        return None
    条目表=[]
    已见=set()
    for 待办 in 参数['todos']:
        if not 详情记录(待办) or not 非空文本(待办.get('content')):
            return None
        状态=待办.get('status')
        if 状态 not in 待办状态:
            return None
        标题=待办['content'].strip()
        if 标题 in 已见:
            return None
        已见.add(标题)
        条目表.append({
            'title':标题,
            'status':{'value':状态,'label':中文文案('detail.todo.'+状态)},
            'fields':[],
        })
    return {'items':条目表,'empty':中文文案('detail.todo.empty')}

def 目标详情(值):
    'create、get、update_goal 的结果'
    if not 详情记录(值):
        return None
    if 值.get('goal') is None:
        return {'items':[],'empty':中文文案('detail.goal.empty')}
    目标=值['goal']
    if not 详情记录(目标) or not 非空文本(目标.get('id')) or not 非空文本(目标.get('objective')):
        return None
    if not 非负整数(目标.get('revision')) or not 非负整数(目标.get('roundsStarted')) or not 非负整数(目标.get('maxGoalRounds')):
        return None
    阶段=目标.get('phase')
    if 阶段 not in 目标阶段:
        return None
    if 值.get('activation')!='armed' and 值.get('activation')!='disarmed':
        return None
    if 阶段=='active' and 值['activation']=='disarmed':
        阶段文=中文文案('detail.goal.disarmed')
    else:
        阶段文=中文文案('detail.goal.'+阶段)
    字段=[
        {'label':中文文案('detail.state'),'value':阶段文},
        {'label':中文文案('detail.goal.rounds'),'value':str(目标['roundsStarted'])+' / '+str(目标['maxGoalRounds'])},
    ]
    if 'blockedReason' in 目标:
        原因=目标['blockedReason']
        if not 详情记录(原因) or not 非空文本(原因.get('code')) or not 非空文本(原因.get('message')):
            return None
        字段.append({'label':中文文案('detail.goal.reason'),'value':原因['message']})
    return {'items':[{'title':目标['objective'],'fields':字段}]}

def 间隔文案(秒):
    '把秒数收成日、时、分、秒'
    if 秒%86400==0:
        return 中文文案('detail.days',{'count':秒//86400})
    if 秒%3600==0:
        return 中文文案('detail.hours',{'count':秒//3600})
    if 秒%60==0:
        return 中文文案('detail.minutes',{'count':秒//60})
    return 中文文案('detail.seconds',{'count':秒})

def 短时间(时间):
    '去掉零秒与零毫秒'
    return 零毫秒.sub('',零秒.sub('',时间))

def 星期文本(日列表):
    '1 到 7。空或越界则 None'
    if not isinstance(日列表,list) or len(日列表)==0:
        return None
    标签=[]
    for 日 in 日列表:
        if isinstance(日,bool) or not isinstance(日,int):
            return None
        if 日<1 or 日>7:
            return None
        标签.append(中文文案(星期键[日-1]))
    return 中文文案('detail.weekday.join').join(标签)

def 日程条目(值,窗口,语言):
    '一条日程。时刻必须是报文里的 ISO 毫秒 Z'
    if not 详情记录(值) or not 非空文本(值.get('id')) or not 非空文本(值.get('prompt')):
        return None
    if not isinstance(值.get('scheduledAt'),str):
        return None
    if 值.get('deliveryMode')!='host' and 值.get('deliveryMode')!='session-local':
        return None
    if 值.get('state')!='scheduled' and 值.get('state')!='overdue':
        return None
    try:
        日期=窗口.Date(值['scheduledAt'])
        毫秒=日期.getTime()
        if 毫秒!=毫秒 or 日期.toISOString()!=值['scheduledAt']:
            return None
    except Exception:
        return None
    种类=值.get('kind')
    if 种类=='at':
        频率=中文文案('detail.schedule.once')
    elif 种类=='after':
        if not 非负整数(值.get('afterSeconds')) or 值['afterSeconds']==0:
            return None
        频率=中文文案('detail.schedule.once')
    elif 种类=='every':
        if not 非负整数(值.get('everySeconds')) or 值['everySeconds']==0:
            return None
        频率=中文文案('detail.schedule.every',{'interval':间隔文案(值['everySeconds'])})
    elif 种类=='daily':
        if not 非空文本(值.get('time')) or not 非空文本(值.get('timeZone')):
            return None
        频率=中文文案('detail.schedule.daily',{'time':短时间(值['time']),'zone':值['timeZone']})
    elif 种类=='weekly':
        日文=星期文本(值.get('weekdays'))
        if not 非空文本(值.get('time')) or not 非空文本(值.get('timeZone')) or 日文 is None:
            return None
        频率=中文文案('detail.schedule.weekly',{'days':日文,'time':短时间(值['time']),'zone':值['timeZone']})
    elif 种类=='cron':
        if not 非空文本(值.get('expression')) or not 非空文本(值.get('timeZone')):
            return None
        频率=中文文案('detail.schedule.cron',{'expression':值['expression'],'zone':值['timeZone']})
    else:
        return None
    日期文=格式化日期(窗口,值['scheduledAt'],语言,值['scheduledAt'])
    标题=值['title'] if 非空文本(值.get('title')) else 值['prompt']
    return {
        'title':标题,
        'fields':[
            {'label':中文文案('detail.schedule.when'),'value':日期文},
            {'label':中文文案('detail.schedule.frequency'),'value':频率},
            {'label':中文文案('detail.state'),'value':中文文案('detail.schedule.'+值['state'])},
        ],
    }

def 详情卡片模型(块,窗口,语言):
    '已支持的成功结果。未知或畸形返回 None，行保留通用输出'
    if 'kind' not in 块 or 块.get('isError') is True:
        return None
    调用=解析工具调用(块)
    if 调用 is None:
        return None
    文本=单结果文本(块)
    if 文本 is None:
        return None
    值=详情json(文本)
    详情=控制详情(调用['name'],调用['args'],文本,值)
    if 详情 is None:
        详情=检视结果详情(调用['name'],调用['args'],文本,值,窗口,语言)
    if 详情 is not None:
        return 详情
    if 值 is None:
        return None
    名称=调用['name']
    if 名称=='create_goal' or 名称=='get_goal' or 名称=='update_goal':
        return 目标详情(值)
    if 名称=='schedule_create' or 名称=='schedule_update':
        条目=日程条目(值,窗口,语言)
        if 条目 is None:
            return None
        return {'items':[条目]}
    if 名称=='schedule_list':
        if not isinstance(值,list):
            return None
        条目表=[]
        for 项 in 值:
            条目=日程条目(项,窗口,语言)
            if 条目 is None:
                return None
            条目表.append(条目)
        return {
            'items':条目表,
            'summary':中文文案('detail.schedule.count',{'count':len(条目表)}),
            'empty':中文文案('detail.schedule.empty'),
        }
    if 名称=='schedule_delete':
        if not 详情记录(值) or not 非空文本(值.get('id')) or 值.get('deleted') is not True:
            return None
        return {'items':[{
            'title':值['id'],
            'fields':[{'label':中文文案('detail.state'),'value':中文文案('detail.schedule.deleted')}],
        }]}
    return None
