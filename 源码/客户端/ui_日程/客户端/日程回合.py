'把本回合里落定的 schedule_create 记到回合数据上'
from .日程创建模型 import 日程创建卡模型

创建工具='schedule_create'
表面类型=('system/message','developer/message','user/message','assistant/message','tool/result')

__all__=['创建工具','日程回合定义']

def 是追加表面(事件):
    '工具结果是追加进表面尾部，而不是替换副本'
    if 事件.get('type') not in 表面类型:
        return False
    return 事件.get('surfaceOp')=='append'

日程回合定义={
    'kind':'schedule-created',
    'match':None,
    'start':None,
    'update':None,
    'buildLocationData':None,
}

def 匹配(事件):
    '回合开始、工具调用、追加的工具结果才进这一条'
    类型=事件.get('type')
    数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}
    if 类型=='turn/start':
        return {'id':str(数据.get('turn')),'role':'start'}
    if 类型=='tool/call':
        return {'id':str(数据.get('turn')),'role':'update'}
    if 类型=='tool/result' and 是追加表面(事件):
        return {'id':str(数据.get('turn')),'role':'update'}
    return None

def 开始(_上下文,匹配项):
    '只接受 turn/start'
    事件=匹配项['event']
    if 事件.get('type')!='turn/start':
        raise Exception('schedule-created start requires turn/start')
    return {'turn':事件['data']['turn'],'calls':{},'created':[]}

def 更新(上下文,匹配项):
    '配对调用头。只有完整的 schedule_create 结果才记进回合'
    事件=匹配项['event']
    状态=上下文['state']
    if 事件.get('type')=='tool/call':
        调用=dict(状态['calls'])
        数据=事件['data']
        调用[str(数据['callId'])]={'name':数据['name'],'argsRaw':数据['arguments'],'time':事件['seq']}
        return {**状态,'calls':调用}
    if 事件.get('type')!='tool/result':
        return 状态
    来源=事件['data']['message']['source']
    调用=状态['calls'].get(str(来源['callId']))
    if 调用 is None or 调用.get('name')!=创建工具:
        return 状态
    消息=事件['data']['message']
    if 消息.get('isError') is True:
        return 状态
    节点={
        'kind':'tool-result',
        'seq':事件['seq'],
        'time':事件['time'],
        'callId':str(来源['callId']),
        'name':调用['name'],
        'args':{'text':调用['argsRaw']},
        'call':{'name':调用['name'],'argsRaw':调用['argsRaw']},
        'callTime':调用['time'],
        'content':消息.get('content'),
        'isError':False,
        'subCalls':[],
    }
    if 日程创建卡模型(节点,创建工具)['task'] is None:
        return 状态
    return {**状态,'created':[*状态['created'],节点]}

def 建立位置数据(上下文,范围,先前):
    '只往回合上发布。内容和上次一样就沿用那一份'
    状态=上下文.get('state')
    if 范围!='turn' or 状态 is None:
        return None
    if isinstance(先前,dict) and 先前.get('kind')=='turn' and 先前.get('turn')==状态['turn'] and 先前.get('key')=='schedule-created' and 先前.get('value',{}).get('created') is 状态['created']:
        return 先前
    return {'kind':'turn','turn':状态['turn'],'key':'schedule-created','value':{'created':状态['created']}}

日程回合定义['match']=匹配
日程回合定义['start']=开始
日程回合定义['update']=更新
日程回合定义['buildLocationData']=建立位置数据
