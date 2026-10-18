from .....内核.会话.类型 import 安全整数上限

__all__=['聊天合成序号偏移','上下文位置','位置坐标','聊天节点','坐标']

聊天合成序号偏移={
    'interruptedAssistant':-0.9,
    'interruptedFollowup':-0.8,
    'processControl':-0.1,
    'maxTokensNotice':0.05,
    'finalizedFollowup':0.1,
}


def 上下文位置(上下文):
    '这份上下文目前加载到的最好位置。没有就 unresolved'
    起点=上下文.get('start') if isinstance(上下文,dict) else None
    if isinstance(起点,dict) and isinstance(起点.get('location'),dict):
        return 起点['location']
    匹配=上下文.get('matches') if isinstance(上下文,dict) else None
    if isinstance(匹配,list) and len(匹配)>0 and isinstance(匹配[0],dict):
        位置=匹配[0].get('location')
        if isinstance(位置,dict):
            return 位置
    return {'kind':'unresolved'}


def 位置坐标(位置):
    '位置落到的回合和步骤。会话级和 unresolved 没有坐标'
    if not isinstance(位置,dict):
        return {}
    if 位置.get('kind')=='step':
        回合=位置.get('turn') if isinstance(位置.get('turn'),dict) else {}
        步=位置.get('step') if isinstance(位置.get('step'),dict) else {}
        return {'turn':回合.get('turn'),'step':步.get('step')}
    if 位置.get('kind')=='turn':
        回合=位置.get('turn') if isinstance(位置.get('turn'),dict) else {}
        return {'turn':回合.get('turn')}
    return {}


def 聊天节点(上下文,种类,锚序号,数据,选项=None):
    '用引擎持有的稳定键做成最终聊天节点'
    if 选项 is None:
        选项={}
    位置=选项['location'] if 'location' in 选项 else 上下文位置(上下文)
    可见=选项['visibility'] if 'visibility' in 选项 else 'visible'
    节点={
        'key':上下文.get('key'),
        'kind':种类,
        'id':上下文.get('id'),
        'target':'chat',
        'anchorSeq':锚序号,
        'location':位置,
        'visibility':可见,
        'data':数据,
    }
    if 'groupTree' in 选项:
        节点['groupTree']=选项['groupTree']
    return 节点


def 坐标(值):
    '有限非负安全整数才是坐标，否则 None'
    if isinstance(值,bool) or not isinstance(值,int):
        return None
    if 值<0 or 值>安全整数上限:
        return None
    return 值
