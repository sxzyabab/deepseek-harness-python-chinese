import json

__all__=['解析工具调用','单结果文本']

def 解析工具调用(块):
    '工具名与对象参数。准备中、调用头缺失或参数不是 JSON 对象时为 None'
    if 'kind' not in 块 and 块.get('phase')=='preparing':
        return None
    调用=块['call'] if 'kind' in 块 else 块
    if 调用 is None:
        return None
    try:
        值=json.loads(调用['argsRaw'])
    except json.JSONDecodeError:
        return None
    if not isinstance(值,dict):
        return None
    return {'name':调用['name'],'args':值}

def 单结果文本(块):
    '已结算结果恰有一块文本时返回该文本，其余布局为 None'
    内容=块['content']
    if len(内容)!=1:
        return None
    仅有=内容[0]
    if isinstance(仅有,dict) and 仅有.get('type')=='text':
        return 仅有.get('text')
    return None
