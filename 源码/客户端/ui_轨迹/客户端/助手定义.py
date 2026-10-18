from ....模型后端.llm import 助手流首令牌时间#定稿流的首 token
from .轨迹节点 import 轨迹节点#目标信封
from .轨迹表投影 import 展示失败,空助手块,是否令牌增量,转助手块,转助手块列表#块与失败

__all__=['登记轨迹助手定义']

def 初始状态(回合,步号,起始序号,起始时间,已开始):
    '一步助手的空状态'
    return {
        'turn':回合,
        'step':步号,
        'startSeq':起始序号,
        'startTime':起始时间,
        'started':已开始,
        'blocks':[],
        'visibleBlocks':0,
        'firstVisibleSeq':None,
        'firstVisibleTime':None,
        'firstTokenTime':None,
        'final':None,
        'usage':None,
        'retry':None,
        'stepEnd':None,
    }

def 压缩块(块列表):
    '丢掉还没填上的空位'
    return [块 for 块 in 块列表 if 块 is not None]

def 块可见(块):
    '工具调用不算可见正文；空文本也不算'
    if 块 is None or not isinstance(块,dict) or 块.get('kind')=='tool-call':
        return False
    if 块.get('kind') in ('text','reasoning'):
        return str(块.get('text') or '').strip()!=''
    return True

def 累加用量(当前,下一):
    '把一次 usage 块加进已有用量'
    结果={
        'inputTokens':(0 if not isinstance(当前,dict) else 当前.get('inputTokens') or 0)+(下一.get('inputTokens') or 0),
        'outputTokens':(0 if not isinstance(当前,dict) else 当前.get('outputTokens') or 0)+(下一.get('outputTokens') or 0),
    }
    当前读=None if not isinstance(当前,dict) else 当前.get('cacheReadTokens')
    下一读=下一.get('cacheReadTokens')
    if 当前读 is not None or 下一读 is not None:
        结果['cacheReadTokens']=(当前读 or 0)+(下一读 or 0)
    当前写=None if not isinstance(当前,dict) else 当前.get('cacheWriteTokens')
    下一写=下一.get('cacheWriteTokens')
    if 当前写 is not None or 下一写 is not None:
        结果['cacheWriteTokens']=(当前写 or 0)+(下一写 or 0)
    当前推理=None if not isinstance(当前,dict) else 当前.get('reasoningTokens')
    下一推理=下一.get('reasoningTokens')
    if 当前推理 is not None or 下一推理 is not None:
        结果['reasoningTokens']=(当前推理 or 0)+(下一推理 or 0)
    return 结果

def 更新块(状态,块,序号,时间):
    '把一条流式块折进助手状态'
    if 块.get('type')=='usage':
        改=dict(状态)
        改['usage']=累加用量(状态.get('usage'),块.get('usage') or {})
        return 改
    块列表=list(状态.get('blocks') or [])
    改下标=-1
    先前可见=False
    类型=块.get('type')
    if 类型=='block-start':
        改下标=块.get('index') or 0
        while len(块列表)<=改下标:
            块列表.append(None)
        先前可见=块可见(块列表[改下标])
        块列表[改下标]=空助手块(块.get('blockType'))
    elif 类型=='text-delta':
        改下标=块.get('index') or 0
        while len(块列表)<=改下标:
            块列表.append(None)
        先前=块列表[改下标]
        先前可见=块可见(先前)
        原文=先前.get('text') if isinstance(先前,dict) and 先前.get('kind')=='text' else ''
        块列表[改下标]={'kind':'text','text':(原文 or '')+(块.get('text') or '')}
    elif 类型=='reasoning-delta':
        改下标=块.get('index') or 0
        while len(块列表)<=改下标:
            块列表.append(None)
        先前=块列表[改下标]
        先前可见=块可见(先前)
        原文=先前.get('text') if isinstance(先前,dict) and 先前.get('kind')=='reasoning' else ''
        块列表[改下标]={'kind':'reasoning','text':(原文 or '')+(块.get('text') or '')}
    elif 类型=='tool-call-delta':
        改下标=块.get('index') or 0
        while len(块列表)<=改下标:
            块列表.append(None)
        先前=块列表[改下标]
        先前可见=块可见(先前)
        if isinstance(先前,dict) and 先前.get('kind')=='tool-call':
            基=先前
        else:
            基={'kind':'tool-call','callId':'','name':'','argsRaw':''}
        块列表[改下标]={
            'kind':'tool-call',
            'callId':基.get('callId') or str(块.get('id') or ''),
            'name':块.get('name') if 块.get('name') is not None else 基.get('name') or '',
            'argsRaw':(基.get('argsRaw') or '')+(块.get('argumentsDelta') or ''),
        }
    elif 类型=='block-end':
        改下标=块.get('index') or 0
        while len(块列表)<=改下标:
            块列表.append(None)
        先前可见=块可见(块列表[改下标])
        块列表[改下标]=转助手块(块.get('block') or {})
    else:
        return 状态
    可见数=(状态.get('visibleBlocks') or 0)-(1 if 先前可见 else 0)+(1 if 块可见(块列表[改下标]) else 0)
    改=dict(状态)
    改['blocks']=块列表
    改['visibleBlocks']=可见数
    if 可见数>0 and 状态.get('firstVisibleSeq') is None:
        改['firstVisibleSeq']=序号
        改['firstVisibleTime']=时间
    if 是否令牌增量(块) and 状态.get('firstTokenTime') is None:
        改['firstTokenTime']=时间
    return 改

def 结算计时(状态,事件):
    '这一步的首 token 以先到的为准'
    改=dict(状态)
    if 改.get('firstTokenTime') is None:
        流=(事件.get('data') or {}).get('stream') or []
        改['firstTokenTime']=助手流首令牌时间(流)
    return 改

def 结算消息(状态,匹配,事件):
    '定稿消息替换块，并记下用量'
    块列表=转助手块列表((事件.get('data') or {}).get('message',{}).get('content') or [])
    可见=0
    for 块 in 块列表:
        if 块可见(块):
            可见+=1
    改=结算计时(状态,事件)
    改['blocks']=块列表
    改['visibleBlocks']=可见
    改['final']=匹配
    改['usage']=(事件.get('data') or {}).get('usage')
    return 改

def 闭合边界(上下文):
    '步或回合已经关上时的结束点'
    状态=上下文.get('state') or {}
    步结束=状态.get('stepEnd') or {}
    if (步结束.get('event') or {}).get('type')=='step/end':
        return 步结束.get('event')
    起点=上下文.get('start') or {}
    匹配列表=上下文.get('matches') or []
    位置=起点.get('location')
    if 位置 is None and len(匹配列表)>0:
        位置=(匹配列表[-1] or {}).get('location')
    if isinstance(位置,dict) and 位置.get('kind')=='step' and isinstance(位置.get('step'),dict) and 位置['step'].get('status')=='closed':
        return 位置['step'].get('end')
    if isinstance(位置,dict) and 位置.get('kind') in ('step','turn') and isinstance(位置.get('turn'),dict) and 位置['turn'].get('status')=='closed':
        return 位置['turn'].get('end')
    return None

def 登记轨迹助手定义(上下文):
    '登记轨迹助手生命周期和回合结束'
    def 助手匹配(事件):
        '步开始、助手流、定稿、尝试、重试和步结束归到同一步'
        类型=事件.get('type')
        数据=事件.get('data') or {}
        if 类型=='step/start':
            return {'id':str(数据.get('turn'))+':'+str(数据.get('step')),'role':'start'}
        if 类型 in ('assistant/live-chunk','assistant/message','assistant/attempt','llm/retry','step/end'):
            return {'id':str(数据.get('turn'))+':'+str(数据.get('step')),'role':'update'}
        return None

    def 助手开始(_上下文,匹配,_读取器=None):
        '步开始记下回合、步和起始时间'
        if 匹配['event'].get('type')!='step/start':
            raise Exception('trajectory-assistant-step start requires step/start')
        数据=匹配['event'].get('data') or {}
        return 初始状态(数据.get('turn'),数据.get('step'),匹配['event'].get('seq'),匹配['event'].get('time'),True)

    def 助手更新(上下文,匹配):
        '流式块、定稿、尝试、步结束和重试'
        事件=匹配['event']
        类型=事件.get('type')
        if 类型=='assistant/live-chunk':
            数据=事件.get('data') or {}
            return 更新块(上下文.get('state') or {},数据.get('chunk') or {},事件.get('seq'),事件.get('time'))
        if 类型=='assistant/message':
            return 结算消息(上下文.get('state') or {},匹配,事件)
        if 类型=='assistant/attempt':
            return 结算计时(上下文.get('state') or {},事件)
        if 类型=='step/end':
            改=dict(上下文.get('state') or {})
            改['stepEnd']=匹配
            return 改
        if 类型!='llm/retry':
            return 上下文.get('state')
        数据=事件.get('data') or {}
        失败=展示失败(数据.get('failure'))
        改=初始状态(
            (上下文.get('state') or {}).get('turn'),
            (上下文.get('state') or {}).get('step'),
            (上下文.get('state') or {}).get('startSeq'),
            (上下文.get('state') or {}).get('startTime'),
            True,
        )
        改['firstTokenTime']=(上下文.get('state') or {}).get('firstTokenTime')
        改['usage']=(上下文.get('state') or {}).get('usage')
        重试={'message':失败.get('message'),'retry':数据.get('retry'),'delayMs':数据.get('delayMs')}
        if 失败.get('code') is not None:
            重试['code']=失败['code']
        if 数据.get('mode')=='normal':
            重试['maxRetries']=数据.get('maxRetries')
        改['retry']=重试
        return 改

    def 助手发布(匹配):
        '步开始和尝试不发布；用量与结束块也不发布'
        类型=匹配['event'].get('type')
        if 类型 in ('step/start','assistant/attempt'):
            return 'none'
        if 类型!='assistant/live-chunk':
            return 'immediate'
        块类型=((匹配['event'].get('data') or {}).get('chunk') or {}).get('type')
        if 块类型 in ('usage','finish'):
            return 'none'
        return 'animation-frame'

    def 助手视图(上下文):
        '定稿、打断或仍在流的助手贡献'
        状态=上下文.get('state')
        if 状态 is None:
            状态=None
            for 匹配 in 上下文.get('matches') or []:
                事件=匹配.get('event') or {}
                类型=事件.get('type')
                数据=事件.get('data') or {}
                if 类型=='assistant/live-chunk':
                    if 状态 is None:
                        状态=初始状态(数据.get('turn'),数据.get('step'),事件.get('seq'),事件.get('time'),False)
                    状态=更新块(状态,数据.get('chunk') or {},事件.get('seq'),事件.get('time'))
                elif 类型=='assistant/attempt':
                    if 状态 is None:
                        状态=初始状态(数据.get('turn'),数据.get('step'),事件.get('seq'),事件.get('time'),False)
                    状态=结算计时(状态,事件)
                elif 类型=='assistant/message':
                    if 状态 is None:
                        状态=初始状态(数据.get('turn'),数据.get('step'),事件.get('seq'),事件.get('time'),False)
                    状态=结算消息(状态,匹配,事件)
                elif 类型=='step/end' and 状态 is not None:
                    状态=dict(状态)
                    状态['stepEnd']=匹配
        if 状态 is None:
            return None
        定稿匹配=状态.get('final') or {}
        定稿事件=定稿匹配.get('event') or {}
        节点=None
        if 定稿事件.get('type')=='assistant/message':
            数据=定稿事件.get('data') or {}
            消息=数据.get('message') or {}
            来源=消息.get('source') or {}
            节点={
                'kind':'assistant',
                'seq':定稿事件.get('seq'),
                'messageId':消息.get('id'),
                'time':定稿事件.get('time'),
                'turn':状态.get('turn'),
                'step':状态.get('step'),
                'blocks':转助手块列表(消息.get('content') or []),
                'usage':数据.get('usage'),
                'providerMetadata':{'provider':来源.get('provider'),'model':来源.get('model')},
                'timing':{
                    'stepStartTime':状态.get('startTime') if 状态.get('started') else None,
                    'firstTokenTime':状态.get('firstTokenTime'),
                    'completedTime':定稿事件.get('time'),
                },
            }
            if 数据.get('interrupted') is True:
                节点['interrupted']=True
        else:
            边界=闭合边界(上下文)
            块列表=压缩块(状态.get('blocks') or [])
            有证据=False
            for 块 in 块列表:
                if isinstance(块,dict) and 块.get('kind') in ('text','reasoning'):
                    if str(块.get('text') or '').strip()!='':
                        有证据=True
                        break
                elif 块 is not None:
                    有证据=True
                    break
            if isinstance(边界,dict) and 有证据:
                节点={
                    'kind':'assistant',
                    'seq':(边界.get('seq') or 0)-0.9,
                    'time':边界.get('time'),
                    'turn':状态.get('turn'),
                    'step':状态.get('step'),
                    'blocks':块列表,
                    'interrupted':True,
                }
            else:
                边界=闭合边界(上下文) if not isinstance(边界,dict) else 边界
        边界=闭合边界(上下文)
        流式=None
        if 节点 is None and 边界 is None and len(状态.get('blocks') or [])>0:
            流式={
                'turn':状态.get('turn'),
                'step':状态.get('step'),
                'blocks':压缩块(状态.get('blocks') or []),
                'timing':{
                    'stepStartTime':状态.get('startTime') if 状态.get('started') else None,
                    'firstTokenTime':状态.get('firstTokenTime'),
                },
            }
        请求=None
        if 状态.get('started'):
            if 节点 is not None:
                状态名='error' if 节点.get('interrupted') is True else 'complete'
            elif 边界 is not None:
                状态名='error'
            else:
                状态名='running'
            请求={
                'purpose':'assistant',
                'startSeq':状态.get('startSeq'),
                'turn':状态.get('turn'),
                'step':状态.get('step'),
                'startedAt':状态.get('startTime'),
                'completedAt':None if 节点 is None else 节点.get('time'),
                'status':状态名,
            }
            if 请求['completedAt'] is None and isinstance(边界,dict):
                请求['completedAt']=边界.get('time')
            if isinstance(状态.get('retry'),dict):
                重试=状态['retry']
                请求['error']=重试.get('message')
                if 重试.get('code') is not None:
                    请求['errorCode']=重试['code']
                请求['retry']=重试.get('retry')
                if 重试.get('maxRetries') is not None:
                    请求['maxRetries']=重试['maxRetries']
                请求['retryDelayMs']=重试.get('delayMs')
            if 节点 is not None and 节点.get('messageId') is not None:
                请求['resultSeq']=节点.get('seq')
                if 节点.get('providerMetadata') is not None:
                    请求['providerMetadata']=节点['providerMetadata']
            if 状态.get('usage') is not None:
                请求['usage']=状态['usage']
        if 节点 is None and 流式 is None and 请求 is None:
            return None
        数据={'kind':'assistant','partial':流式}
        if 节点 is not None:
            数据['node']=节点
        if 请求 is not None:
            数据['request']=请求
        return 轨迹节点(上下文,状态.get('startSeq'),数据)

    def 回合结束匹配(事件):
        '回合结束各开一条'
        if 事件.get('type')=='turn/end':
            return {'id':str(事件.get('seq')),'role':'start'}
        return None

    def 回合结束开始(_上下文,匹配,_读取器=None):
        '错误原因收成可展示的失败字段'
        if 匹配['event'].get('type')!='turn/end':
            raise Exception('trajectory-turn-end start requires turn/end')
        数据=匹配['event'].get('data') or {}
        原因=数据.get('reason') or {}
        失败=展示失败(原因.get('error')) if 原因.get('kind')=='error' else None
        状态={'turn':数据.get('turn'),'seq':匹配['event'].get('seq'),'time':匹配['event'].get('time')}
        if isinstance(失败,dict):
            状态['error']=失败.get('message')
            if 失败.get('code') is not None:
                状态['errorCode']=失败['code']
        return 状态

    def 回合结束更新(上下文,_匹配=None):
        '更新不改状态'
        return 上下文.get('state')

    def 回合结束视图(上下文):
        '有状态才贡献回合结束'
        状态=上下文.get('state')
        if 状态 is None:
            return None
        数据={'kind':'turn-end','turn':状态.get('turn'),'time':状态.get('time')}
        if 状态.get('error') is not None:
            数据['error']=状态['error']
        if 状态.get('errorCode') is not None:
            数据['errorCode']=状态['errorCode']
        return 轨迹节点(上下文,状态.get('seq'),数据)

    上下文.uiConversation.events.register({
        'kind':'trajectory-assistant-step',
        'target':'trajectory',
        'match':助手匹配,
        'start':助手开始,
        'update':助手更新,
        'publication':助手发布,
        'buildViewNode':助手视图,
    })
    上下文.uiConversation.events.register({
        'kind':'trajectory-turn-end',
        'target':'trajectory',
        'match':回合结束匹配,
        'start':回合结束开始,
        'update':回合结束更新,
        'buildViewNode':回合结束视图,
    })
