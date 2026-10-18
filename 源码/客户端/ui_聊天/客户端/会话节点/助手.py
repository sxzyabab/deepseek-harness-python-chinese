from ...异常 import 聊天错误
from .事件投影 import 空助手块,是令牌增量,转助手块,转助手块列表
from .节点工厂 import 聊天合成序号偏移,聊天节点

__all__=['助手定义','登记助手会话节点']


def 初始状态(回合,步):
    '一步助手从空块表开始'
    return {
        'turn':回合,
        'step':步,
        'blocks':[],
        'visibleBlocks':0,
        'firstVisibleSeq':None,
        'firstVisibleTime':None,
        'firstTokenTime':None,
        'final':None,
        'usage':None,
    }


def 压紧块(块表):
    '去掉还没填上的空位'
    return [块 for 块 in 块表 if 块 is not None]


def 块可见(块):
    '工具调用块不占助手可见内容。空文本和空推理也不算'
    if 块 is None or not isinstance(块,dict) or 块.get('kind')=='tool-call':
        return False
    if 块.get('kind') in ('text','reasoning'):
        文=块.get('text')
        return isinstance(文,str) and 文.strip()!=''
    return True


def 数可见块(块表):
    '可见块的个数'
    数=0
    for 块 in 块表:
        if 块可见(块):
            数+=1
    return 数


def 有可见内容(块表):
    '有任何可见块'
    for 块 in 块表:
        if 块可见(块):
            return True
    return False


def 有中断证据(块表):
    '中断时除了空文本空推理，别的块都算已经写出的内容'
    for 块 in 块表:
        if not isinstance(块,dict):
            continue
        if 块.get('kind') in ('text','reasoning'):
            文=块.get('text')
            if isinstance(文,str) and 文.strip()!='':
                return True
        else:
            return True
    return False


def 为重试重置(状态):
    '重试清掉已写出的块，首 token 时间留下'
    下一=初始状态(状态.get('turn'),状态.get('step'))
    下一['firstTokenTime']=状态.get('firstTokenTime')
    return 下一


def 更新块(状态,块,序号,时间):
    '把一条流式块折进这一步。用量只改 usage'
    if isinstance(块,dict) and 块.get('type')=='tool-call-delta':
        下标=块.get('index') if isinstance(块.get('index'),int) else 0
        先前=状态['blocks'][下标] if 下标<len(状态['blocks']) else None
        if (
            isinstance(先前,dict)
            and 先前.get('kind')=='tool-call'
            and 先前.get('callId')!=''
            and (块.get('name') is None or 块.get('name')==先前.get('name'))
            and (状态.get('firstTokenTime') is not None or not 是令牌增量(块))
        ):
            return 状态
    块表=list(状态.get('blocks') if isinstance(状态.get('blocks'),list) else [])
    改下标=-1
    先前可见=False
    类型=块.get('type') if isinstance(块,dict) else None
    if 类型=='block-start':
        改下标=块.get('index') if isinstance(块.get('index'),int) else 0
        while len(块表)<=改下标:
            块表.append(None)
        先前可见=块可见(块表[改下标])
        块表[改下标]=空助手块(块.get('blockType'))
    elif 类型=='text-delta':
        改下标=块.get('index') if isinstance(块.get('index'),int) else 0
        while len(块表)<=改下标:
            块表.append(None)
        先前=块表[改下标]
        先前可见=块可见(先前)
        旧文=先前.get('text') if isinstance(先前,dict) and 先前.get('kind')=='text' else ''
        块表[改下标]={'kind':'text','text':旧文+(块.get('text') or '')}
    elif 类型=='reasoning-delta':
        改下标=块.get('index') if isinstance(块.get('index'),int) else 0
        while len(块表)<=改下标:
            块表.append(None)
        先前=块表[改下标]
        先前可见=块可见(先前)
        旧文=先前.get('text') if isinstance(先前,dict) and 先前.get('kind')=='reasoning' else ''
        块表[改下标]={'kind':'reasoning','text':旧文+(块.get('text') or '')}
    elif 类型=='tool-call-delta':
        改下标=块.get('index') if isinstance(块.get('index'),int) else 0
        while len(块表)<=改下标:
            块表.append(None)
        先前=块表[改下标]
        先前可见=块可见(先前)
        旧标识=先前.get('callId') if isinstance(先前,dict) and 先前.get('kind')=='tool-call' else ''
        旧名=先前.get('name') if isinstance(先前,dict) and 先前.get('kind')=='tool-call' else ''
        旧参=先前.get('argsRaw') if isinstance(先前,dict) and 先前.get('kind')=='tool-call' else ''
        块表[改下标]={
            'kind':'tool-call',
            'callId':旧标识 or str(块.get('id')),
            'name':块.get('name') if 块.get('name') is not None else 旧名,
            'argsRaw':旧参,
        }
    elif 类型=='block-end':
        改下标=块.get('index') if isinstance(块.get('index'),int) else 0
        while len(块表)<=改下标:
            块表.append(None)
        先前可见=块可见(块表[改下标])
        块表[改下标]=转助手块(块.get('block') if isinstance(块.get('block'),dict) else {})
    elif 类型=='usage':
        下一=dict(状态)
        下一['usage']=块.get('usage')
        return 下一
    else:
        return 状态
    可见数=状态.get('visibleBlocks') or 0
    可见数=可见数-(1 if 先前可见 else 0)+(1 if 块可见(块表[改下标]) else 0)
    下一=dict(状态)
    下一['blocks']=块表
    下一['visibleBlocks']=可见数
    if 可见数>0 and 状态.get('firstVisibleSeq') is None:
        下一['firstVisibleSeq']=序号
        下一['firstVisibleTime']=时间
    if 是令牌增量(块) and 状态.get('firstTokenTime') is None:
        下一['firstTokenTime']=时间
    return 下一


def 定稿消息(状态,匹配项,事件):
    '助手消息落地，块表换成定稿内容'
    数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}
    消息=数据.get('message') if isinstance(数据.get('message'),dict) else {}
    内容=消息.get('content') if isinstance(消息.get('content'),list) else []
    块表=转助手块列表(内容)
    下一=dict(状态)
    下一['blocks']=块表
    下一['visibleBlocks']=数可见块(块表)
    下一['final']=匹配项
    下一['usage']=数据.get('usage')
    return 下一


def 关闭边界(位置):
    '步骤或回合已经关闭时的结束点'
    if not isinstance(位置,dict):
        return None
    if 位置.get('kind')=='step':
        步=位置.get('step') if isinstance(位置.get('step'),dict) else {}
        if 步.get('status')=='closed' and 步.get('end') is not None:
            return 步.get('end')
    if 位置.get('kind') in ('step','turn'):
        回合=位置.get('turn') if isinstance(位置.get('turn'),dict) else {}
        if 回合.get('status')=='closed' and 回合.get('end') is not None:
            return 回合.get('end')
    return None


def 终节点(状态,上下文):
    '定稿消息，或边界关闭后用已写出的块合成中断助手'
    定稿=状态.get('final') if isinstance(状态.get('final'),dict) else None
    定稿事件=定稿.get('event') if isinstance(定稿,dict) else None
    if isinstance(定稿事件,dict) and 定稿事件.get('type')=='assistant/message':
        数据=定稿事件.get('data') if isinstance(定稿事件.get('data'),dict) else {}
        消息=数据.get('message') if isinstance(数据.get('message'),dict) else {}
        内容=消息.get('content') if isinstance(消息.get('content'),list) else []
        起点=上下文.get('start') if isinstance(上下文.get('start'),dict) else None
        起点事件=起点.get('event') if isinstance(起点,dict) else None
        节点={
            'kind':'assistant',
            'seq':定稿事件.get('seq'),
            'messageId':消息.get('id'),
            'time':定稿事件.get('time'),
            'turn':状态.get('turn'),
            'step':状态.get('step'),
            'blocks':转助手块列表(内容),
            'usage':数据.get('usage'),
            'timing':{
                'stepStartTime':起点事件.get('time') if isinstance(起点事件,dict) else None,
                'firstTokenTime':状态.get('firstTokenTime'),
                'completedTime':定稿事件.get('time'),
            },
        }
        if 数据.get('interrupted') is True:
            节点['interrupted']=True
        return 节点
    起点=上下文.get('start') if isinstance(上下文.get('start'),dict) else None
    匹配=上下文.get('matches') if isinstance(上下文.get('matches'),list) else []
    位置=起点.get('location') if isinstance(起点,dict) else None
    if not isinstance(位置,dict) and len(匹配)>0 and isinstance(匹配[-1],dict):
        位置=匹配[-1].get('location')
    边界=关闭边界(位置)
    if not isinstance(边界,dict):
        return None
    块表=压紧块(状态.get('blocks') if isinstance(状态.get('blocks'),list) else [])
    if not 有中断证据(块表):
        return None
    return {
        'kind':'assistant',
        'seq':边界.get('seq')+聊天合成序号偏移['interruptedAssistant'],
        'time':边界.get('time'),
        'turn':状态.get('turn'),
        'step':状态.get('step'),
        'blocks':块表,
        'interrupted':True,
    }


def 助手回退(上下文):
    '没有状态时按已加载匹配重放'
    状态=None
    匹配=上下文.get('matches') if isinstance(上下文.get('matches'),list) else []
    for 项 in 匹配:
        事件=项.get('event') if isinstance(项,dict) else None
        if not isinstance(事件,dict):
            continue
        if 事件.get('type')=='assistant/live-chunk':
            数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}
            if 状态 is None:
                状态=初始状态(数据.get('turn'),数据.get('step'))
            状态=更新块(状态,数据.get('chunk'),事件.get('seq'),事件.get('time'))
        elif 事件.get('type')=='assistant/message':
            数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}
            if 状态 is None:
                状态=初始状态(数据.get('turn'),数据.get('step'))
            状态=定稿消息(状态,项,事件)
        elif 事件.get('type')=='llm/retry' and 状态 is not None:
            状态=为重试重置(状态)
    return 状态


def 已公布助手数据(上下文):
    '步骤数据里已经公布的助手材料'
    起点=上下文.get('start') if isinstance(上下文.get('start'),dict) else None
    匹配=上下文.get('matches') if isinstance(上下文.get('matches'),list) else []
    位置=起点.get('location') if isinstance(起点,dict) else None
    if not isinstance(位置,dict) and len(匹配)>0 and isinstance(匹配[-1],dict):
        位置=匹配[-1].get('location')
    if not isinstance(位置,dict) or 位置.get('kind')!='step':
        return None
    步=位置.get('step') if isinstance(位置.get('step'),dict) else {}
    数据=步.get('data')
    if hasattr(数据,'get'):
        return 数据.get('assistant-step')
    return None


def 助手匹配(事件):
    '步骤开始认领。流、追加的助手消息和重试都更新同一步'
    数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}
    if 事件.get('type')=='step/start':
        return {'id':str(数据.get('turn'))+':'+str(数据.get('step')),'role':'start'}
    if 事件.get('type')=='assistant/live-chunk' or (事件.get('type')=='assistant/message' and 事件.get('surfaceOp')=='append'):
        return {'id':str(数据.get('turn'))+':'+str(数据.get('step')),'role':'update'}
    if 事件.get('type')=='llm/retry':
        return {'id':str(数据.get('turn'))+':'+str(数据.get('step')),'role':'update'}
    return None


def 助手开始(上下文,匹配项):
    '必须从 step/start 开始'
    事件=匹配项.get('event') if isinstance(匹配项,dict) else None
    if not isinstance(事件,dict) or 事件.get('type')!='step/start':
        raise 聊天错误('assistant-step start requires step/start')
    数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}
    return 初始状态(数据.get('turn'),数据.get('step'))


def 助手更新(上下文,匹配项):
    '流式块、定稿消息或重试'
    状态=上下文.get('state') if isinstance(上下文.get('state'),dict) else {}
    事件=匹配项.get('event') if isinstance(匹配项,dict) else None
    if not isinstance(事件,dict):
        return 状态
    if 事件.get('type')=='assistant/live-chunk':
        数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}
        return 更新块(状态,数据.get('chunk'),事件.get('seq'),事件.get('time'))
    if 事件.get('type')=='assistant/message':
        return 定稿消息(状态,匹配项,事件)
    if 事件.get('type')=='llm/retry':
        return 为重试重置(状态)
    return 状态


def 助手公布(匹配项):
    '步骤开始和用量、结束不单独公布。流式块跟动画帧'
    事件=匹配项.get('event') if isinstance(匹配项,dict) else {}
    if 事件.get('type')=='step/start':
        return 'none'
    if 事件.get('type')!='assistant/live-chunk':
        return 'immediate'
    数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}
    块=数据.get('chunk') if isinstance(数据.get('chunk'),dict) else {}
    if 块.get('type') in ('usage','finish'):
        return 'none'
    return 'animation-frame'


def 助手建位置数据(上下文,范围):
    '只往步骤数据上写助手材料'
    if 范围!='step':
        return None
    状态=上下文.get('state')
    if not isinstance(状态,dict):
        状态=助手回退(上下文)
    if not isinstance(状态,dict):
        return None
    定稿=终节点(状态,上下文)
    块表=定稿.get('blocks') if isinstance(定稿,dict) else 压紧块(状态.get('blocks') if isinstance(状态.get('blocks'),list) else [])
    可见=状态.get('visibleBlocks',0)>0 if 定稿 is None else 有可见内容(块表)
    if isinstance(定稿,dict) and 定稿.get('interrupted') is True:
        状况='interrupted'
    elif 定稿 is None:
        状况='running'
    else:
        状况='settled'
    锚=状态.get('firstVisibleSeq')
    if isinstance(定稿,dict) and 定稿.get('interrupted') is True:
        锚=定稿.get('seq')
    elif 锚 is None and isinstance(定稿,dict):
        锚=定稿.get('seq')
    匹配=上下文.get('matches') if isinstance(上下文.get('matches'),list) else []
    if 锚 is None and len(匹配)>0 and isinstance(匹配[0],dict) and isinstance(匹配[0].get('event'),dict):
        锚=匹配[0]['event'].get('seq')
    if 锚 is None:
        锚=0
    时间=定稿.get('time') if isinstance(定稿,dict) else 状态.get('firstVisibleTime')
    if 时间 is None and len(匹配)>0 and isinstance(匹配[0],dict) and isinstance(匹配[0].get('event'),dict):
        时间=匹配[0]['event'].get('time')
    if 时间 is None:
        时间=0
    数据={
        'status':状况,
        'turn':状态.get('turn'),
        'step':状态.get('step'),
        'blocks':块表,
        'time':时间,
    }
    if 状态.get('usage') is not None:
        数据['usage']=状态['usage']
    if isinstance(定稿,dict):
        数据['finalNode']=定稿
    return {
        'kind':'step',
        'turn':数据['turn'],
        'step':数据['step'],
        'key':'assistant-step',
        'value':数据,
    }


def 助手建视图(上下文):
    '已物化的键在流被清掉后仍留成隐藏节点'
    当前表=上下文.get('current')
    当前=当前表.get('chat') if hasattr(当前表,'get') else None
    状态=上下文.get('state')
    if not isinstance(状态,dict):
        状态=助手回退(上下文)
    数据=已公布助手数据(上下文)
    if not isinstance(状态,dict) or not isinstance(数据,dict):
        if 当前 is None:
            return None
        隐藏=dict(当前)
        隐藏['visibility']='hidden'
        return 隐藏
    定稿=数据.get('finalNode')
    可见=(状态.get('visibleBlocks') or 0)>0 if 定稿 is None else 有可见内容(数据.get('blocks') if isinstance(数据.get('blocks'),list) else [])
    if 定稿 is None and not 可见 and 当前 is None:
        return None
    锚=状态.get('firstVisibleSeq')
    if isinstance(定稿,dict) and 定稿.get('interrupted') is True:
        锚=定稿.get('seq')
    elif 锚 is None and isinstance(定稿,dict):
        锚=定稿.get('seq')
    匹配=上下文.get('matches') if isinstance(上下文.get('matches'),list) else []
    if 锚 is None and len(匹配)>0 and isinstance(匹配[0],dict) and isinstance(匹配[0].get('event'),dict):
        锚=匹配[0]['event'].get('seq')
    if 锚 is None:
        锚=0
    可见性='visible' if (isinstance(定稿,dict) and 定稿.get('interrupted') is True) or 可见 else 'hidden'
    return 聊天节点(上下文,'assistant-step',锚,数据,{'visibility':可见性})


助手定义={
    'kind':'assistant-step',
    'target':'chat',
    'match':助手匹配,
    'start':助手开始,
    'update':助手更新,
    'publication':助手公布,
    'buildLocationData':助手建位置数据,
    'buildViewNode':助手建视图,
}


def 登记助手会话节点(上下文):
    '按事件类型分发匹配，避免每条事件都进同一个函数'
    def 匹配(事件):
        '转给定义上的匹配'
        return 助手匹配(事件)
    登记=dict(助手定义)
    登记['match']={
        'step/start':匹配,
        'assistant/live-chunk':匹配,
        'assistant/message':匹配,
        'llm/retry':匹配,
    }
    上下文.uiConversation.events.register(登记)
