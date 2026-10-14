'把一轮里结算的 schedule_create 记到回合数据上'
from .日程创建模型 import 创建工具名,日程创建卡模型

__all__=['创建工具名','选取日程任务','日程回合定义']

def 取(对象,键):
    '字典或对象'
    if 对象 is None:
        return None
    if isinstance(对象,dict):
        return 对象[键] if 键 in 对象 else None
    return getattr(对象,键,None)

def 选取日程任务(属性):
    '这一轮创建的任务；没有则 None'
    回合=取(属性,'turn')
    数据=取(回合,'data')
    载荷=None
    if 数据 is not None and hasattr(数据,'get'):
        载荷=数据.get('schedule-created')
    elif isinstance(数据,dict) and 'schedule-created' in 数据:
        载荷=数据['schedule-created']
    创建=取(载荷,'created')
    if not isinstance(创建,list) or len(创建)==0:
        return None
    序号=取(取(回合,'end'),'seq')
    if 序号 is None:
        序号=取(属性,'seq')
    if isinstance(序号,(int,float)) and not isinstance(序号,bool):
        创建=[项 for 项 in 创建 if not isinstance(项,dict) or 'seq' not in 项 or 项['seq']<=序号]
    if len(创建)==0:
        return None
    return {'created':创建}

def 匹配(事件):
    '回合开始开状态，工具调用和结果更新同一轮'
    if not isinstance(事件,dict) or 'type' not in 事件:
        return None
    数据=事件['data'] if 'data' in 事件 and isinstance(事件['data'],dict) else {}
    if 事件['type']=='turn/start':
        return {'id':str(数据['turn'] if 'turn' in 数据 else ''),'role':'start'}
    if 事件['type']=='tool/call' or 事件['type']=='tool/result':
        return {'id':str(数据['turn'] if 'turn' in 数据 else ''),'role':'update'}
    return None

def 起始(_上下文,匹配结果):
    '必须从 turn/start 开始'
    事件=匹配结果['event']
    if 事件['type']!='turn/start':
        raise RuntimeError('schedule-created start requires turn/start')
    return {'turn':事件['data']['turn'],'calls':{},'created':[]}

def _创建块(匹配结果,调用):
    '失败或没有完整任务则不记卡'
    事件=匹配结果['event']
    if 事件['type']!='tool/result':
        return None
    消息=事件['data']['message'] if 'data' in 事件 and isinstance(事件['data'],dict) and 'message' in 事件['data'] else {}
    if isinstance(消息,dict) and 消息.get('isError') is True:
        return None
    来源=消息['source'] if isinstance(消息,dict) and 'source' in 消息 and isinstance(消息['source'],dict) else {}
    块={
        'kind':'tool-result',
        'seq':事件['seq'] if 'seq' in 事件 else 0,
        'time':事件['time'] if 'time' in 事件 else 0,
        'callId':str(来源['callId'] if 'callId' in 来源 else ''),
        'name':调用['name'],
        'call':{'name':调用['name'],'argsRaw':调用['argsRaw']},
        'callTime':调用['time'],
        'content':消息['content'] if isinstance(消息,dict) and 'content' in 消息 else [],
        'isError':False,
    }
    if 日程创建卡模型(块,创建工具名)['task'] is None:
        return None
    return 块

def 更新(上下文,匹配结果):
    '记下调用头，结果里有任务才追加'
    事件=匹配结果['event']
    状态=上下文['state']
    if 事件['type']=='tool/call':
        数据=事件['data'] if 'data' in 事件 and isinstance(事件['data'],dict) else {}
        调用表=dict(状态['calls'])
        调用表[str(数据['callId'] if 'callId' in 数据 else '')]={
            'name':数据['name'] if 'name' in 数据 else '',
            'argsRaw':数据['arguments'] if 'arguments' in 数据 else '',
            'time':事件['seq'] if 'seq' in 事件 else 0,
        }
        return {**状态,'calls':调用表}
    if 事件['type']!='tool/result':
        return 状态
    消息=事件['data']['message'] if 'data' in 事件 and isinstance(事件['data'],dict) else {}
    来源=消息['source'] if isinstance(消息,dict) and 'source' in 消息 else {}
    调用标识=str(来源['callId'] if isinstance(来源,dict) and 'callId' in 来源 else '')
    调用=状态['calls'][调用标识] if 调用标识 in 状态['calls'] else None
    if not isinstance(调用,dict) or 调用.get('name')!=创建工具名:
        return 状态
    块=_创建块(匹配结果,调用)
    if 块 is None:
        return 状态
    return {**状态,'created':[*状态['created'],块]}

def 建位置数据(上下文,作用域,先前):
    '把创建列表写到回合数据 schedule-created'
    if 作用域!='turn' or 'state' not in 上下文 or 上下文['state'] is None:
        return None
    状态=上下文['state']
    if isinstance(先前,dict) and 先前.get('kind')=='turn' and 先前.get('turn')==状态['turn'] and 先前.get('key')=='schedule-created':
        旧=先前['value'] if 'value' in 先前 else None
        if isinstance(旧,dict) and 旧.get('created') is 状态['created']:
            return 先前
    return {'kind':'turn','turn':状态['turn'],'key':'schedule-created','value':{'created':状态['created']}}

日程回合定义={
    'kind':'schedule-created',
    'match':匹配,
    'start':起始,
    'update':更新,
    'buildLocationData':建位置数据,
}
