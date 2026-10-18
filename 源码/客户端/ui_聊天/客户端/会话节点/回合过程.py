from ...异常 import 聊天错误
from ..约定.助手内容 import 有助手回复内容
from ..约定.回合过程 import 回合过程规格相同,是子智能体委派工具
from .事件投影 import 转助手块列表
from .节点工厂 import 聊天合成序号偏移,聊天节点

__all__=['回合过程定义','登记回合过程']


def 事件回合(事件):
    '载荷里的回合号'
    数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}
    回合=数据.get('turn')
    if isinstance(回合,bool) or not isinstance(回合,int):
        return None
    return 回合


def 可见块(块):
    '这条流式块会不会让助手变得可见'
    if not isinstance(块,dict):
        return False
    类型=块.get('type')
    if 类型 in ('text-delta','reasoning-delta'):
        文=块.get('text')
        return isinstance(文,str) and 文.strip()!=''
    if 类型=='block-start':
        return 块.get('blockType') not in ('text','reasoning','tool-call')
    if 类型!='block-end':
        return False
    内容=块.get('block') if isinstance(块.get('block'),dict) else {}
    if 内容.get('type')=='tool-call':
        return False
    if 内容.get('type') in ('text','reasoning'):
        文=内容.get('text')
        return isinstance(文,str) and 文.strip()!=''
    return True


def 可见助手事件(事件):
    '可见的流式块，或追加的有可见内容的助手消息'
    if 事件.get('type')=='assistant/live-chunk':
        数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}
        return 可见块(数据.get('chunk'))
    if 事件.get('type')=='assistant/attempt':
        return False
    if 事件.get('type')=='assistant/message' and 事件.get('surfaceOp')=='append':
        数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}
        消息=数据.get('message') if isinstance(数据.get('message'),dict) else {}
        内容=消息.get('content') if isinstance(消息.get('content'),list) else []
        for 块 in 转助手块列表(内容):
            if 块.get('kind')=='tool-call':
                continue
            if 块.get('kind') in ('text','reasoning'):
                文=块.get('text')
                if isinstance(文,str) and 文.strip()!='':
                    return True
                continue
            return True
    return False


def 过程证据(事件):
    '可见助手，或工具、追加结果、重试'
    if 可见助手事件(事件):
        if 事件.get('type') not in ('assistant/live-chunk','assistant/message','assistant/attempt'):
            return None
        数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}
        return {'kind':'assistant','seq':事件.get('seq'),'step':数据.get('step')}
    if 事件.get('type')=='tool/call' or (事件.get('type')=='tool/result' and 事件.get('surfaceOp')=='append') or 事件.get('type')=='llm/retry':
        return {'kind':'other','seq':事件.get('seq')}
    return None


def 回合位置(上下文):
    '这份上下文所属回合'
    起点=上下文.get('start') if isinstance(上下文.get('start'),dict) else None
    匹配=上下文.get('matches') if isinstance(上下文.get('matches'),list) else []
    位置=起点.get('location') if isinstance(起点,dict) else None
    if not isinstance(位置,dict) and len(匹配)>0 and isinstance(匹配[-1],dict):
        位置=匹配[-1].get('location')
    if isinstance(位置,dict) and 位置.get('kind') in ('turn','step'):
        return 位置.get('turn') if isinstance(位置.get('turn'),dict) else None
    return None


def 更新过程状态(状态,事件):
    '累加回复条数、工具次数，并记下过程从哪条序号开始'
    当前=dict(状态)
    当前['assistantStartByStep']=dict(状态.get('assistantStartByStep') or {})
    当前['messageCountByStep']=dict(状态.get('messageCountByStep') or {})
    if 事件.get('type')=='assistant/message' and 事件.get('surfaceOp')=='append':
        数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}
        消息=数据.get('message') if isinstance(数据.get('message'),dict) else {}
        内容=消息.get('content') if isinstance(消息.get('content'),list) else []
        if 有助手回复内容(转助手块列表(内容)):
            步=数据.get('step')
            当前['messageCountByStep'][步]=当前['messageCountByStep'].get(步,0)+1
            当前['messageCount']=当前.get('messageCount',0)+1
    if 事件.get('type')=='tool/call':
        数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}
        委派=是子智能体委派工具(数据.get('name'))
        if 委派:
            当前['subagentCount']=当前.get('subagentCount',0)+1
        else:
            当前['toolCallCount']=当前.get('toolCallCount',0)+1
    证据=过程证据(事件)
    if 证据 is None:
        return 当前
    if 证据['kind']=='other':
        if 当前.get('otherStartSeq') is not None:
            return 当前
        当前['otherStartSeq']=证据['seq']
        已有=当前.get('controlAnchorSeq')
        当前['controlAnchorSeq']=证据['seq'] if 已有 is None else min(已有,证据['seq'])
        return 当前
    if 证据['step'] in 当前['assistantStartByStep']:
        return 当前
    当前['assistantStartByStep'][证据['step']]=证据['seq']
    已有=当前.get('controlAnchorSeq')
    当前['controlAnchorSeq']=证据['seq'] if 已有 is None else min(已有,证据['seq'])
    return 当前


def 最新回答(回合):
    '最后一步里有回复、且没有工具调用块的定稿助手'
    步表=回合.get('steps') if isinstance(回合.get('steps'),list) else []
    if len(步表)==0 or not isinstance(步表[-1],dict):
        return None
    数据=步表[-1].get('data')
    材料=数据.get('assistant-step') if hasattr(数据,'get') else None
    if not isinstance(材料,dict) or not isinstance(材料.get('finalNode'),dict):
        return None
    块表=材料.get('blocks') if isinstance(材料.get('blocks'),list) else []
    if not 有助手回复内容(块表):
        return None
    for 块 in 块表:
        if isinstance(块,dict) and 块.get('kind')=='tool-call':
            return None
    return 材料


def 过程规格(状态,回合):
    '控制锚、过程起点和定稿回答边界'
    起点=回合.get('start') if isinstance(回合.get('start'),dict) else None
    控制=状态.get('controlAnchorSeq')
    if 控制 is None and isinstance(起点,dict):
        控制=起点.get('seq')
    if 控制 is None:
        return None
    回答=最新回答(回合)
    if 回答 is None:
        return {
            'turn':回合.get('turn'),
            'controlAnchorSeq':控制,
            'processStartSeq':控制,
            'answerAnchorSeq':None,
            'answerStep':None,
            'inlineReasoning':False,
            'messageCount':状态.get('messageCount',0),
            'toolCallCount':状态.get('toolCallCount',0),
            'subagentCount':状态.get('subagentCount',0),
        }
    回答步=回答.get('step')
    消息数=0
    for 步,次数 in (状态.get('messageCountByStep') or {}).items():
        if 步<回答步:
            消息数+=次数
    行内推理=False
    for 块 in 回答.get('blocks') if isinstance(回答.get('blocks'),list) else []:
        if isinstance(块,dict) and 块.get('kind')=='reasoning':
            文=块.get('text')
            if isinstance(文,str) and 文.strip()!='':
                行内推理=True
    更早=None
    for 步,序号 in (状态.get('assistantStartByStep') or {}).items():
        if 步<回答步 and (更早 is None or 序号<更早):
            更早=序号
    外部=状态.get('otherStartSeq')
    if 更早 is not None and (外部 is None or 更早<外部):
        外部=更早
    if isinstance(起点,dict) and 起点.get('seq') is not None:
        过程起=起点.get('seq')
    elif 外部 is not None:
        过程起=外部
    else:
        过程起=回答['finalNode'].get('seq')
    return {
        'turn':回合.get('turn'),
        'controlAnchorSeq':控制,
        'processStartSeq':过程起,
        'answerAnchorSeq':回答['finalNode'].get('seq'),
        'answerStep':回答步,
        'inlineReasoning':行内推理,
        'messageCount':消息数,
        'toolCallCount':状态.get('toolCallCount',0),
        'subagentCount':状态.get('subagentCount',0),
    }


def 空过程状态(回合):
    '一个回合的过程计数从零开始'
    return {
        'turn':回合,
        'assistantStartByStep':{},
        'messageCountByStep':{},
        'messageCount':0,
        'toolCallCount':0,
        'subagentCount':0,
    }


def 过程回退(上下文):
    '没有状态时按已加载匹配重放'
    匹配=上下文.get('matches') if isinstance(上下文.get('matches'),list) else []
    回合=None
    for 项 in 匹配:
        事件=项.get('event') if isinstance(项,dict) else None
        if isinstance(事件,dict):
            回合=事件回合(事件)
            if 回合 is not None:
                break
    if 回合 is None:
        return None
    状态=空过程状态(回合)
    for 项 in 匹配:
        事件=项.get('event') if isinstance(项,dict) else None
        if isinstance(事件,dict):
            状态=更新过程状态(状态,事件)
    return 状态


def 回合过程匹配(事件):
    '回合开始认领。过程里的助手、工具、步骤和结束都更新'
    if 事件.get('type')=='turn/start':
        数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}
        return {'id':str(数据.get('turn')),'role':'start'}
    回合=事件回合(事件)
    if 回合 is None:
        return None
    if 事件.get('type') in ('assistant/live-chunk','assistant/message','tool/call','tool/result','llm/retry','step/start','step/end','turn/end'):
        return {'id':str(回合),'role':'update'}
    return None


def 回合过程开始(上下文,匹配项):
    '必须从 turn/start 开始'
    事件=匹配项.get('event') if isinstance(匹配项,dict) else None
    if not isinstance(事件,dict) or 事件.get('type')!='turn/start':
        raise 聊天错误('turn-process start requires turn/start')
    数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}
    return 空过程状态(数据.get('turn'))


def 回合过程更新(上下文,匹配项):
    '把这一条事件折进过程计数'
    状态=上下文.get('state') if isinstance(上下文.get('state'),dict) else 空过程状态(None)
    事件=匹配项.get('event') if isinstance(匹配项,dict) else {}
    return 更新过程状态(状态,事件)


def 回合过程公布(匹配项):
    '流式块跟动画帧。用量和结束不单独公布'
    事件=匹配项.get('event') if isinstance(匹配项,dict) else {}
    if 事件.get('type')=='assistant/live-chunk':
        数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}
        块=数据.get('chunk') if isinstance(数据.get('chunk'),dict) else {}
        if 块.get('type') in ('usage','finish'):
            return 'none'
        return 'animation-frame'
    return 'immediate'


def 回合过程建位置数据(上下文,范围,先前=None):
    '过程规格写在回合数据上。没变就留着上一份'
    if 范围!='turn':
        return None
    状态=上下文.get('state')
    if not isinstance(状态,dict):
        状态=过程回退(上下文)
    if not isinstance(状态,dict):
        return None
    回合=回合位置(上下文)
    if not isinstance(回合,dict):
        return None
    规格=过程规格(状态,回合)
    if 规格 is None:
        return None
    if (
        isinstance(先前,dict)
        and 先前.get('kind')=='turn'
        and 先前.get('turn')==规格['turn']
        and 先前.get('key')=='turn-process'
        and isinstance(先前.get('value'),dict)
        and 回合过程规格相同(先前['value'],规格)
    ):
        return 先前
    return {'kind':'turn','turn':回合.get('turn'),'key':'turn-process','value':规格}


def 回合过程建视图(上下文):
    '控制行在过程锚上，组树位置是回合'
    回合=回合位置(上下文)
    数据=None
    if isinstance(回合,dict) and hasattr(回合.get('data'),'get'):
        数据=回合['data'].get('turn-process')
    if not isinstance(回合,dict) or not isinstance(数据,dict):
        return None
    return 聊天节点(
        上下文,
        'turn-process',
        数据.get('controlAnchorSeq')+聊天合成序号偏移['processControl'],
        数据,
        {'groupTree':'turn'},
    )


回合过程定义={
    'kind':'turn-process',
    'target':'chat',
    'match':回合过程匹配,
    'start':回合过程开始,
    'update':回合过程更新,
    'publication':回合过程公布,
    'buildLocationData':回合过程建位置数据,
    'buildViewNode':回合过程建视图,
}


def 登记回合过程(上下文):
    '按事件类型分发匹配'
    def 匹配(事件):
        '转给定义上的匹配'
        return 回合过程匹配(事件)
    登记=dict(回合过程定义)
    登记['match']={
        'turn/start':匹配,
        'assistant/live-chunk':匹配,
        'assistant/message':匹配,
        'tool/call':匹配,
        'tool/result':匹配,
        'llm/retry':匹配,
        'step/start':匹配,
        'step/end':匹配,
        'turn/end':匹配,
    }
    上下文.uiConversation.events.register(登记)
