import json
from .....内核.会话.表面 import 是否追加表面事件
from ...异常 import 聊天错误
from .节点工厂 import 上下文位置,聊天合成序号偏移,聊天节点

__all__=['工具定义','登记工具会话节点','最大工具深度']

最大工具深度=256
投影缓存={}


def 取部分参数():
    '参数增量视图。工具.值 里还没有 PartialArguments 时，调用处报缺'
    try:
        from .....工具.值 import PartialArguments
    except ImportError:
        raise 聊天错误('缺少 工具.值 的 PartialArguments')
    return PartialArguments


def 引用相同(左,右):
    '长度和每一项身份都一样'
    if len(左)!=len(右):
        return False
    下标=0
    for 项 in 左:
        if 项 is not 右[下标]:
            return False
        下标+=1
    return True


def 根调用(匹配项,先前=None):
    'tool/call 变成已开始的根'
    事件=匹配项.get('event') if isinstance(匹配项,dict) else None
    if not isinstance(事件,dict) or 事件.get('type')!='tool/call':
        raise 聊天错误('tool-call start requires tool/call')
    数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}
    参数类=取部分参数()
    if 先前 is None:
        参数=参数类.fromText(数据.get('arguments'))
    else:
        参数=先前.get('args').settle(数据.get('arguments'))
    return {
        'phase':'start',
        'callId':str(数据.get('callId')),
        'name':数据.get('name'),
        'argsRaw':数据.get('arguments'),
        'args':参数,
        'turn':数据.get('turn'),
        'step':数据.get('step'),
        'time':事件.get('time'),
        'subCalls':[],
    }


def 应用增量(状态,匹配项):
    '把参数碎片留在具名调用上。无名增量先跳过'
    事件=匹配项.get('event') if isinstance(匹配项,dict) else None
    if not isinstance(事件,dict) or 事件.get('type')!='assistant/live-chunk':
        return 状态
    数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}
    块=数据.get('chunk') if isinstance(数据.get('chunk'),dict) else {}
    根=状态.get('root')
    if 块.get('type')=='block-end' and isinstance(块.get('block'),dict) and 块['block'].get('type')=='tool-call':
        if not isinstance(根,dict) or 'kind' in 根 or 根.get('phase')!='preparing':
            return 状态
        下一=dict(状态)
        下一根=dict(根)
        下一根['name']=块['block'].get('name')
        下一根['args']=根.get('args').settle(块['block'].get('arguments'))
        下一['root']=下一根
        return 下一
    if 块.get('type')!='tool-call-delta':
        return 状态
    if 根 is None:
        if not 块.get('name'):
            return 状态
        参数类=取部分参数()
        参数=参数类()
        参数.append(块.get('argumentsDelta'))
        下一=dict(状态)
        下一['root']={
            'phase':'preparing',
            'callId':str(块.get('id')),
            'name':块.get('name'),
            'turn':数据.get('turn'),
            'step':数据.get('step'),
            'time':事件.get('time'),
            'subCalls':[],
            'args':参数,
        }
        return 下一
    if not isinstance(根,dict) or 'kind' in 根 or 根.get('phase')!='preparing' or getattr(根.get('args'),'isSealed',False):
        return 状态
    根['args'].append(块.get('argumentsDelta'))
    return 状态


def 准备块(根,当前):
    '刷新参数视图。没变就留原对象'
    变了=根.get('args').refresh() if hasattr(根.get('args'),'refresh') else False
    if not 变了 and isinstance(当前,dict) and 'kind' not in 当前 and 当前.get('phase')=='preparing' and 当前.get('name')==根.get('name') and 当前.get('args') is 根.get('args'):
        return 当前
    if 变了:
        return dict(根)
    return 根


def 根结果(匹配项,先前=None):
    'tool/result 收成结果节点'
    事件=匹配项.get('event') if isinstance(匹配项,dict) else None
    if not isinstance(事件,dict) or 事件.get('type')!='tool/result':
        return None
    数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}
    消息=数据.get('message') if isinstance(数据.get('message'),dict) else {}
    来源=消息.get('source') if isinstance(消息.get('source'),dict) else {}
    参数类=取部分参数()
    结果={
        'kind':'tool-result',
        'seq':事件.get('seq'),
        'time':事件.get('time'),
        'callId':str(来源.get('callId')),
        'name':先前.get('name') if isinstance(先前,dict) and 先前.get('name') else '',
        'args':先前.get('args') if isinstance(先前,dict) and 先前.get('args') is not None else 参数类.EMPTY,
        'call':None if not isinstance(先前,dict) else {'name':先前.get('name'),'argsRaw':先前.get('argsRaw')},
        'callTime':None if not isinstance(先前,dict) else 先前.get('time'),
        'content':消息.get('content'),
        'isError':消息.get('isError') is True,
        'meta':数据.get('meta'),
        'subCalls':[],
    }
    if 数据.get('error') is not None:
        结果['error']=数据['error']
    return 结果


def 位置回合(匹配项):
    '匹配所在回合。没有就 0'
    位置=匹配项.get('location') if isinstance(匹配项,dict) else None
    if isinstance(位置,dict) and 位置.get('kind') in ('step','turn') and isinstance(位置.get('turn'),dict):
        return 位置['turn'].get('turn') or 0
    return 0


def 位置步(匹配项):
    '匹配所在步骤。没有就 0'
    位置=匹配项.get('location') if isinstance(匹配项,dict) else None
    if isinstance(位置,dict) and 位置.get('kind')=='step' and isinstance(位置.get('step'),dict):
        return 位置['step'].get('step') or 0
    return 0


def 子调用(匹配项,数据):
    'PTC 派发开始'
    参数类=取部分参数()
    return {
        'phase':'start',
        'callId':数据.get('subCallId'),
        'parentCallId':数据.get('parentCallId'),
        'name':数据.get('name'),
        'argsRaw':json.dumps(数据.get('arguments'),ensure_ascii=False),
        'args':参数类.fromObject(数据.get('arguments')),
        'turn':位置回合(匹配项),
        'step':位置步(匹配项),
        'time':匹配项.get('event',{}).get('time') if isinstance(匹配项.get('event'),dict) else None,
        'subCalls':[],
    }


def 子结果(匹配项,数据,先前=None):
    'PTC 派发结算'
    参数类=取部分参数()
    事件=匹配项.get('event') if isinstance(匹配项,dict) else {}
    结果={
        'kind':'tool-result',
        'seq':事件.get('seq'),
        'time':事件.get('time'),
        'callId':数据.get('subCallId'),
        'parentCallId':数据.get('parentCallId'),
        'name':数据.get('name'),
        'args':先前.get('args') if isinstance(先前,dict) and 'kind' not in 先前 else 参数类.fromObject(数据.get('arguments')),
        'call':{'name':数据.get('name'),'argsRaw':json.dumps(数据.get('arguments'),ensure_ascii=False)},
        'callTime':None if not isinstance(先前,dict) else 先前.get('time'),
        'content':数据.get('content') if 数据.get('content') is not None else [],
        'meta':数据.get('meta'),
        'isError':数据.get('isError') is True,
        'subCalls':[],
    }
    if 数据.get('error') is not None:
        结果['error']=数据['error']
    return 结果


def 接受边(状态,父标识,子标识):
    '成环或深度超过上限的边丢掉'
    父母=状态.get('parents') if isinstance(状态.get('parents'),dict) else {}
    子女=状态.get('children') if isinstance(状态.get('children'),dict) else {}
    if 父标识==子标识 or 子标识 in 父母:
        return False
    游标=父标识
    父深=0
    祖先=set()
    while 游标 is not None:
        if 游标==子标识 or 游标 in 祖先:
            return False
        祖先.add(游标)
        父深+=1
        游标=父母.get(游标)
    待定=[{'callId':子标识,'depth':1}]
    后代=set()
    子树深=0
    for 候选 in list(待定):
        if 候选['callId'] in 后代:
            return False
        后代.add(候选['callId'])
        if 候选['depth']>子树深:
            子树深=候选['depth']
        for 嵌套 in 子女.get(候选['callId']) or []:
            if isinstance(嵌套,dict):
                待定.append({'callId':嵌套.get('callId'),'depth':候选['depth']+1})
    return 父深+子树深<=最大工具深度


def 更新派发(状态,匹配项):
    '挂上或结算一条 PTC 子调用'
    事件=匹配项.get('event') if isinstance(匹配项,dict) else None
    if not isinstance(事件,dict) or 事件.get('type') not in ('tool/ptc-dispatch-start','tool/ptc-dispatch'):
        return 状态
    数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}
    父标识=str(数据.get('parentCallId'))
    子标识=str(数据.get('subCallId'))
    数据=dict(数据)
    数据['parentCallId']=父标识
    数据['subCallId']=子标识
    子女=dict(状态.get('children') or {})
    父母=dict(状态.get('parents') or {})
    兄弟=list(子女.get(父标识) or [])
    处=-1
    下标=0
    for 子 in 兄弟:
        if isinstance(子,dict) and 子.get('callId')==子标识:
            处=下标
            break
        下标+=1
    if 事件.get('type')=='tool/ptc-dispatch-start':
        if 处>=0 or not 接受边(状态,父标识,子标识):
            return 状态
        兄弟.append(子调用(匹配项,数据))
        子女[父标识]=兄弟
        父母[子标识]=父标识
        下一=dict(状态)
        下一['children']=子女
        下一['parents']=父母
        return 下一
    if 处<0 and not 接受边(状态,父标识,子标识):
        return 状态
    先前=None if 处<0 else 兄弟[处]
    结算=子结果(匹配项,数据,先前)
    if 处<0:
        兄弟.append(结算)
        父母[子标识]=父标识
    else:
        兄弟[处]=结算
    子女[父标识]=兄弟
    下一=dict(状态)
    下一['children']=子女
    下一['parents']=父母
    return 下一


def 投影块(块,状态,中断于,已访=None,深度=1):
    '递归挂子调用。超过深度上限就不再往下'
    if not isinstance(块,dict):
        return 块
    if 'kind' not in 块 and 块.get('phase')=='preparing':
        return 块
    if 已访 is None:
        已访=set()
    if 块.get('callId') in 已访 or 深度>最大工具深度:
        截=dict(块)
        截['subCalls']=[]
        return 截
    下一访=set(已访)
    下一访.add(块.get('callId'))
    子女表=状态.get('children') if isinstance(状态.get('children'),dict) else {}
    子源=子女表.get(块.get('callId'),块.get('subCalls') or [])
    子=[投影块(子项,状态,中断于,下一访,深度+1) for 子项 in 子源]
    中断序=None if 'kind' in 块 else (None if 中断于 is None else 中断于.get('seq'))
    中断时=None if 'kind' in 块 else (None if 中断于 is None else 中断于.get('time'))
    缓存=投影缓存.get(id(块))
    if isinstance(缓存,dict) and 缓存.get('source') is 块 and 缓存.get('interruptionSeq')==中断序 and 缓存.get('interruptionTime')==中断时 and 引用相同(缓存.get('children') or [],子):
        return 缓存['value']
    if 'kind' in 块 or 中断于 is None:
        if 引用相同(块.get('subCalls') or [],子):
            值=块
        else:
            值=dict(块)
            值['subCalls']=子
    else:
        值={
            'kind':'tool-result',
            'seq':中断于.get('seq',0)+聊天合成序号偏移['interruptedFollowup'],
            'time':中断于.get('time'),
            'callId':块.get('callId'),
            'name':块.get('name'),
            'args':块.get('args'),
            'call':{'name':块.get('name'),'argsRaw':块.get('argsRaw')},
            'callTime':块.get('time'),
            'content':[],
            'isError':True,
            'error':{'name':'Interrupted','code':'interrupted'},
            'subCalls':子,
        }
        if 块.get('parentCallId') is not None:
            值['parentCallId']=块['parentCallId']
    投影缓存[id(块)]={'source':块,'children':子,'interruptionSeq':中断序,'interruptionTime':中断时,'value':值}
    return 值


def 中断点(上下文):
    '步骤或回合已经结束时的终节点'
    起点=上下文.get('start') if isinstance(上下文.get('start'),dict) else None
    位置=起点.get('location') if isinstance(起点,dict) else None
    if isinstance(位置,dict) and 位置.get('kind')=='step' and isinstance(位置.get('step'),dict) and 位置['step'].get('status')=='closed':
        return 位置['step'].get('end')
    if isinstance(位置,dict) and 位置.get('kind') in ('step','turn') and isinstance(位置.get('turn'),dict) and 位置['turn'].get('status')=='closed':
        return 位置['turn'].get('end')
    return None


def 回退状态(上下文):
    '没有状态时，用结果匹配和派发重建'
    匹配=上下文.get('matches') if isinstance(上下文.get('matches'),list) else []
    根=None
    for 候选 in 匹配:
        if isinstance(候选,dict) and isinstance(候选.get('event'),dict) and 候选['event'].get('type')=='tool/result':
            根=根结果(候选)
            break
    if 根 is None:
        return None
    状态={'root':根,'children':{},'parents':{}}
    for 候选 in 匹配:
        状态=更新派发(状态,候选)
    return 状态


def 工具匹配(事件):
    '实时块、工具调用、追加结果，以及挂在根调用上的 PTC 派发'
    if not isinstance(事件,dict):
        return None
    if 事件.get('type')=='assistant/live-chunk':
        数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}
        块=数据.get('chunk') if isinstance(数据.get('chunk'),dict) else {}
        if 块.get('type')=='block-end' and isinstance(块.get('block'),dict) and 块['block'].get('type')=='tool-call':
            return {'id':str(块['block'].get('id')),'role':'start'}
        if 块.get('type')=='tool-call-delta':
            return {'id':str(块.get('id')),'role':'start'}
        return None
    if 事件.get('type')=='tool/call':
        数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}
        return {'id':str(数据.get('callId')),'role':'start'}
    if 事件.get('type')=='tool/result' and 是否追加表面事件(事件):
        数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}
        消息=数据.get('message') if isinstance(数据.get('message'),dict) else {}
        来源=消息.get('source') if isinstance(消息.get('source'),dict) else {}
        return {'id':str(来源.get('callId')),'role':'update'}
    if 事件.get('type') in ('tool/ptc-dispatch-start','tool/ptc-dispatch'):
        数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}
        根=数据.get('rootCallId')
        if isinstance(根,str) and 根!='':
            return {'id':根,'role':'update'}
        return None
    return None


def 工具开始(上下文,匹配项):
    'tool/call 直接成为根。实时块先进入准备或吃增量'
    状态={'root':None,'children':{},'parents':{}}
    事件=匹配项.get('event') if isinstance(匹配项,dict) else None
    if isinstance(事件,dict) and 事件.get('type')=='tool/call':
        状态['root']=根调用(匹配项)
        return 状态
    return 应用增量(状态,匹配项)


def 工具更新(上下文,匹配项):
    '增量、正式调用、结果和 PTC 子调用'
    状态=上下文.get('state') if isinstance(上下文.get('state'),dict) else {'root':None,'children':{},'parents':{}}
    事件=匹配项.get('event') if isinstance(匹配项,dict) else None
    if not isinstance(事件,dict):
        return 状态
    if 事件.get('type')=='assistant/live-chunk':
        return 应用增量(状态,匹配项)
    if 事件.get('type')=='tool/call':
        下一=dict(状态)
        下一['root']=根调用(匹配项,状态.get('root') if isinstance(状态.get('root'),dict) else None)
        return 下一
    if 事件.get('type')=='tool/result':
        根=状态.get('root')
        进行=根 if isinstance(根,dict) and 'kind' not in 根 and 根.get('phase')=='start' else None
        结果=根结果(匹配项,进行)
        if 结果 is None:
            return 状态
        下一=dict(状态)
        下一['root']=结果
        return 下一
    return 更新派发(状态,匹配项)


def 工具公布(匹配项):
    '实时块跟动画帧，其余立刻公布'
    事件=匹配项.get('event') if isinstance(匹配项,dict) else {}
    if 事件.get('type')=='assistant/live-chunk':
        return 'animation-frame'
    return 'immediate'


def 工具建视图(上下文):
    '准备中的根在中断后隐藏。其余投影子调用'
    当前表=上下文.get('current')
    当前=当前表.get('chat') if hasattr(当前表,'get') else None
    状态=上下文.get('state')
    if not isinstance(状态,dict):
        状态=回退状态(上下文)
    if not isinstance(状态,dict) or 状态.get('root') is None:
        if not isinstance(当前,dict):
            return None
        if 当前.get('visibility')=='hidden':
            return 当前
        隐藏=dict(当前)
        隐藏['visibility']='hidden'
        return 隐藏
    中断于=中断点(上下文)
    根=状态['root']
    if isinstance(根,dict) and 'kind' not in 根 and 根.get('phase')=='preparing':
        当前根=当前.get('data',{}).get('root') if isinstance(当前,dict) and isinstance(当前.get('data'),dict) else None
        根=准备块(根,当前根)
    投影=投影块(根,状态,中断于)
    起点=上下文.get('start') if isinstance(上下文.get('start'),dict) else None
    起点事件=起点.get('event') if isinstance(起点,dict) else None
    锚=起点事件.get('seq') if isinstance(起点事件,dict) else None
    if 锚 is None and isinstance(状态.get('root'),dict) and 'kind' in 状态['root']:
        锚=状态['root'].get('seq')
    if 锚 is None:
        匹配=上下文.get('matches') if isinstance(上下文.get('matches'),list) else []
        if len(匹配)>0 and isinstance(匹配[0],dict) and isinstance(匹配[0].get('event'),dict):
            锚=匹配[0]['event'].get('seq')
    if 锚 is None:
        锚=0
    准备中=isinstance(投影,dict) and 'kind' not in 投影 and 投影.get('phase')=='preparing'
    可见='hidden' if 准备中 and 中断于 is not None else 'visible'
    位置=上下文位置(上下文)
    数据={'root':投影}
    if isinstance(当前,dict) and isinstance(当前.get('data'),dict) and 当前['data'].get('root') is 投影:
        数据=当前['data']
    if isinstance(当前,dict) and 当前.get('data') is 数据 and 当前.get('anchorSeq')==锚 and 当前.get('visibility')==可见 and 当前.get('location') is 位置:
        return 当前
    return 聊天节点(上下文,'tool-call',锚,数据,{'visibility':可见,'location':位置})


工具定义={
    'kind':'tool-call',
    'target':'chat',
    'match':工具匹配,
    'start':工具开始,
    'update':工具更新,
    'publication':工具公布,
    'buildViewNode':工具建视图,
}


def 登记工具会话节点(上下文):
    '按事件类型分发匹配'
    def 匹配(事件):
        '转给定义上的匹配'
        return 工具匹配(事件)
    登记=dict(工具定义)
    登记['match']={
        'assistant/live-chunk':匹配,
        'tool/call':匹配,
        'tool/result':匹配,
        'tool/ptc-dispatch-start':匹配,
        'tool/ptc-dispatch':匹配,
    }
    上下文.uiConversation.events.register(登记)
