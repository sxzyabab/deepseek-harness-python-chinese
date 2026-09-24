import json
from datetime import datetime as 日期时间,timezone as 时区
from .详情模型共享 import 详情json,详情记录,非空文本
from .控制详情模型 import 控制详情
from .检视结果详情模型 import 检视结果详情

__all__=['待办详情','详情卡片模型']

待办状态=frozenset(['completed','in_progress','pending'])
目标阶段=frozenset(['active','paused','blocked','complete'])
激活态=frozenset(['armed','disarmed'])
日程状态=frozenset(['scheduled','overdue'])

def 解析工具调用(块):
    """解析调用头的 JSON 对象参数；准备中或非法则 None。块为 dict。"""
    if 'kind' not in 块 and 块['phase']=='preparing':
        return None
    调用=块['call'] if 'kind' in 块 else 块
    if 调用 is None:
        return None
    try:
        值=json.loads(调用['argsRaw'])
    except (TypeError,ValueError,json.JSONDecodeError):
        return None
    if not isinstance(值,dict):
        return None
    return {'name':调用['name'],'args':值}

def 单结果文本(块):
    """仅一块文本的已结算结果。"""
    内容=块['content'] if 'content' in 块 else []
    if len(内容)!=1:
        return None
    仅=内容[0]
    if not isinstance(仅,dict) or 'type' not in 仅 or 仅['type']!='text':
        return None
    return 仅['text'] if 'text' in 仅 else None

def 非负整数(值):
    """入口校验：非负安全整数。"""
    return isinstance(值,int) and not isinstance(值,bool) and 值>=0

def 格式化日期(时刻,语言,回退):
    """当地时区短日期；失败回退。"""
    try:
        return 时刻.astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')
    except (OSError,ValueError,OverflowError):
        return 回退

def 待办详情(参数,翻译):
    """从 todo_write 参数派生紧凑待办列表。"""
    if 'todos' not in 参数 or not isinstance(参数['todos'],list):
        return None
    条目=[]
    已见=set()
    for 待办 in 参数['todos']:
        if not 详情记录(待办) or not 非空文本(待办['content'] if 'content' in 待办 else None):
            return None
        状态=待办['status'] if 'status' in 待办 else None
        if 状态 not in 待办状态:
            return None
        标题=待办['content'].strip()
        if 标题 in 已见:
            return None
        已见.add(标题)
        条目.append({'title':标题,'status':{'value':状态,'label':翻译('detail.todo.'+状态)},'fields':[]})
    return {'items':条目,'empty':翻译('detail.todo.empty')}

def 目标详情(值,翻译):
    """create/get/update_goal 结果。"""
    if not 详情记录(值):
        return None
    if 'goal' in 值 and 值['goal'] is None:
        return {'items':[],'empty':翻译('detail.goal.empty')}
    目标=值['goal'] if 'goal' in 值 else None
    if not 详情记录(目标) or not 非空文本(目标['id'] if 'id' in 目标 else None):
        return None
    if not 非空文本(目标['objective'] if 'objective' in 目标 else None):
        return None
    if not 非负整数(目标['revision'] if 'revision' in 目标 else None):
        return None
    if not 非负整数(目标['roundsStarted'] if 'roundsStarted' in 目标 else None):
        return None
    if not 非负整数(目标['maxGoalRounds'] if 'maxGoalRounds' in 目标 else None):
        return None
    阶段=目标['phase'] if 'phase' in 目标 else None
    if 阶段 not in 目标阶段:
        return None
    激活=值['activation'] if 'activation' in 值 else None
    if 激活 not in 激活态:
        return None
    状态键='detail.goal.disarmed' if 阶段=='active' and 激活=='disarmed' else 'detail.goal.'+阶段
    字段=[
        {'label':翻译('detail.state'),'value':翻译(状态键)},
        {'label':翻译('detail.goal.rounds'),'value':str(目标['roundsStarted'])+' / '+str(目标['maxGoalRounds'])},
    ]
    if 'blockedReason' in 目标:
        原因=目标['blockedReason']
        if not 详情记录(原因) or not 非空文本(原因['code'] if 'code' in 原因 else None) or not 非空文本(原因['message'] if 'message' in 原因 else None):
            return None
        字段.append({'label':翻译('detail.goal.reason'),'value':原因['message']})
    return {'items':[{'title':目标['objective'],'fields':字段}]}

def 间隔文案(秒,翻译):
    """把秒数收成日/时/分/秒文案。"""
    if 秒%86400==0:
        return 翻译('detail.days',{'count':秒//86400})
    if 秒%3600==0:
        return 翻译('detail.hours',{'count':秒//3600})
    if 秒%60==0:
        return 翻译('detail.minutes',{'count':秒//60})
    return 翻译('detail.seconds',{'count':秒})

def 解析计划时刻(文本):
    """报文 ISO-8601 毫秒 Z 时刻。"""
    try:
        时刻=日期时间.strptime(文本,'%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=时区.utc)
    except ValueError:
        return None
    重构=时刻.strftime('%Y-%m-%dT%H:%M:%S.')+f'{时刻.microsecond//1000:03d}Z'
    if 重构!=文本:
        return None
    return 时刻

def 日程条目(值,翻译,语言):
    """一条 session-local 日程。"""
    if not 详情记录(值) or not 非空文本(值['id'] if 'id' in 值 else None) or not 非空文本(值['prompt'] if 'prompt' in 值 else None):
        return None
    if 'scheduledAt' not in 值 or not isinstance(值['scheduledAt'],str):
        return None
    if 值['deliveryMode']!='session-local' if 'deliveryMode' in 值 else True:
        return None
    状态=值['state'] if 'state' in 值 else None
    if 状态 not in 日程状态:
        return None
    时刻=解析计划时刻(值['scheduledAt'])
    if 时刻 is None:
        return None
    种=值['kind'] if 'kind' in 值 else None
    if 种=='at':
        频率=翻译('detail.schedule.once')
    elif 种=='after':
        秒=值['afterSeconds'] if 'afterSeconds' in 值 else None
        if not 非负整数(秒) or 秒==0:
            return None
        频率=翻译('detail.schedule.once')
    elif 种=='every':
        秒=值['everySeconds'] if 'everySeconds' in 值 else None
        if not 非负整数(秒) or 秒==0:
            return None
        频率=翻译('detail.schedule.every',{'interval':间隔文案(秒,翻译)})
    else:
        return None
    日期文=格式化日期(时刻,语言,值['scheduledAt'])
    return {
        'title':值['prompt'],
        'fields':[
            {'label':翻译('detail.schedule.when'),'value':日期文},
            {'label':翻译('detail.schedule.frequency'),'value':频率},
            {'label':翻译('detail.state'),'value':翻译('detail.schedule.'+状态)},
        ],
    }

def 详情卡片模型(块,翻译,语言):
    """已支持的成功结果；未知或畸形保留通用输出。块为 dict。"""
    if 'kind' not in 块 or ('isError' in 块 and 块['isError']):
        return None
    调用=解析工具调用(块)
    if 调用 is None:
        return None
    文本=单结果文本(块)
    if 文本 is None:
        return None
    值=详情json(文本)
    详情=控制详情(调用['name'],调用['args'],文本,值,翻译)
    if 详情 is None:
        详情=检视结果详情(调用['name'],调用['args'],文本,值,翻译,语言)
    if 详情 is not None:
        return 详情
    if 值 is None:
        return None
    名=调用['name']
    if 名=='create_goal' or 名=='get_goal' or 名=='update_goal':
        return 目标详情(值,翻译)
    if 名=='schedule_create':
        项=日程条目(值,翻译,语言)
        return None if 项 is None else {'items':[项]}
    if 名=='schedule_list':
        if not isinstance(值,list):
            return None
        条目=[]
        for 笔 in 值:
            项=日程条目(笔,翻译,语言)
            if 项 is None:
                return None
            条目.append(项)
        return {'items':条目,'summary':翻译('detail.schedule.count',{'count':len(条目)}),'empty':翻译('detail.schedule.empty')}
    if 名=='schedule_delete':
        if not 详情记录(值) or not 非空文本(值['id'] if 'id' in 值 else None) or ('deleted' not in 值) or 值['deleted'] is not True:
            return None
        return {'items':[{'title':值['id'],'fields':[{'label':翻译('detail.state'),'value':翻译('detail.schedule.deleted')}]}]}
    return None
