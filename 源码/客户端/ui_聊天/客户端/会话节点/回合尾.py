from .....模型后端.token计数器.客户端 import 派生回合令牌用量
from ...异常 import 聊天错误
from .节点工厂 import 聊天合成序号偏移,聊天节点

__all__=['回合尾定义','登记回合尾会话节点']


def 是会话事件(事件):
    '实时块不是持久会话事件，不送进用量折叠'
    return isinstance(事件,dict) and 事件.get('type')!='assistant/live-chunk'


def 回合坐标(事件):
    '能落到某个回合的事件'
    数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}
    if 事件.get('type') in ('assistant/message','assistant/attempt','assistant/live-chunk','step/start','step/end','llm/retry','llm/retry-started'):
        return {'turn':数据.get('turn'),'step':数据.get('step')}
    return None


def 回合位置(上下文):
    '这份上下文所属的回合'
    起点=上下文.get('start') if isinstance(上下文.get('start'),dict) else None
    匹配=上下文.get('matches') if isinstance(上下文.get('matches'),list) else []
    位置=起点.get('location') if isinstance(起点,dict) else None
    if not isinstance(位置,dict) and len(匹配)>0 and isinstance(匹配[0],dict):
        位置=匹配[0].get('location')
    if isinstance(位置,dict) and 位置.get('kind') in ('turn','step'):
        return 位置.get('turn') if isinstance(位置.get('turn'),dict) else None
    return None


def 有文本(数据):
    '定稿助手里有非空文本'
    if not isinstance(数据,dict) or 数据.get('finalNode') is None:
        return False
    块表=数据.get('blocks') if isinstance(数据.get('blocks'),list) else []
    for 块 in 块表:
        if isinstance(块,dict) and 块.get('kind')=='text':
            文=块.get('text')
            if isinstance(文,str) and 文.strip()!='':
                return True
    return False


def 尾数据(上下文):
    '完成回合的页脚：收束助手、能否分支、以及从回合起点算出的用量'
    状态=上下文.get('state') if isinstance(上下文.get('state'),dict) else None
    匹配=上下文.get('matches') if isinstance(上下文.get('matches'),list) else []
    if 状态 is None or 状态.get('end') is None:
        结束=None
        for 项 in 匹配:
            事件=项.get('event') if isinstance(项,dict) else None
            if isinstance(事件,dict) and 事件.get('type')=='turn/end':
                结束=项
    else:
        结束=状态.get('end')
    if not isinstance(结束,dict) or not isinstance(结束.get('event'),dict) or 结束['event'].get('type')!='turn/end':
        return None
    回合=回合位置(上下文)
    if not isinstance(回合,dict):
        return None
    助手表=[]
    步表=回合.get('steps') if isinstance(回合.get('steps'),list) else []
    for 步 in 步表:
        if not isinstance(步,dict):
            continue
        数据=步.get('data')
        材料=数据.get('assistant-step') if hasattr(数据,'get') else None
        if isinstance(材料,dict):
            助手表.append(材料)
    定稿=[]
    for 材料 in 助手表:
        if isinstance(材料.get('finalNode'),dict):
            定稿.append(材料)
    def 定稿序号(项):
        '按定稿消息序号排序'
        终=项.get('finalNode') if isinstance(项.get('finalNode'),dict) else {}
        return 终.get('seq') or 0
    定稿.sort(key=定稿序号)
    收束=None
    for 材料 in reversed(定稿):
        if 有文本(材料):
            收束=材料
            break
    最新序号=None
    if len(定稿)>0 and isinstance(定稿[-1].get('finalNode'),dict):
        最新序号=定稿[-1]['finalNode'].get('seq')
    for 项 in 匹配:
        事件=项.get('event') if isinstance(项,dict) else None
        if not isinstance(事件,dict):
            continue
        候选=None
        if 事件.get('type')=='tool/call':
            候选=事件.get('seq')
        elif 事件.get('type')=='tool/result' and 事件.get('surfaceOp')=='append':
            候选=事件.get('seq')
        elif 事件.get('type')=='turn/end':
            数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}
            原因=数据.get('reason') if isinstance(数据.get('reason'),dict) else {}
            if 原因.get('kind')=='error':
                候选=事件.get('seq')
        elif 事件.get('type')=='llm/retry':
            候选=事件.get('seq')
        if 候选 is not None and (最新序号 is None or 候选>最新序号):
            最新序号=候选
    起点=上下文.get('start') if isinstance(上下文.get('start'),dict) else None
    起点事件=起点.get('event') if isinstance(起点,dict) else None
    用量=None
    if isinstance(起点事件,dict) and 起点事件.get('type')=='turn/start':
        事件表=[]
        for 项 in 匹配:
            事件=项.get('event') if isinstance(项,dict) else None
            if 是会话事件(事件):
                事件表.append(事件)
        用量=派生回合令牌用量(事件表)
    结束事件=结束['event']
    结束数据=结束事件.get('data') if isinstance(结束事件.get('data'),dict) else {}
    收束序号=收束['finalNode'].get('seq') if isinstance(收束,dict) and isinstance(收束.get('finalNode'),dict) else None
    结果={
        'turn':结束数据.get('turn'),
        'seq':结束事件.get('seq'),
        'time':结束事件.get('time'),
        'closing':收束,
        'branchUnavailable':收束 is None or 最新序号!=收束序号,
    }
    if 用量 is not None:
        结果['tokenUsage']=用量
    return 结果


def 回合尾匹配(事件):
    '回合起止、工具，以及能落到回合上的助手和步骤事件'
    数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}
    if 事件.get('type')=='turn/start':
        return {'id':str(数据.get('turn')),'role':'start'}
    if 事件.get('type')=='turn/end':
        return {'id':str(数据.get('turn')),'role':'update'}
    if 事件.get('type') in ('tool/call','tool/result'):
        return {'id':str(数据.get('turn')),'role':'update'}
    坐标=回合坐标(事件)
    if 坐标 is not None:
        return {'id':str(坐标['turn']),'role':'update'}
    return None


def 回合尾开始(上下文,匹配项):
    '必须从 turn/start 开始'
    事件=匹配项.get('event') if isinstance(匹配项,dict) else None
    if not isinstance(事件,dict) or 事件.get('type')!='turn/start':
        raise 聊天错误('turn-tail start requires turn/start')
    数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}
    return {'turn':数据.get('turn')}


def 回合尾更新(上下文,匹配项):
    '只有回合结束改状态'
    状态=上下文.get('state') if isinstance(上下文.get('state'),dict) else {}
    事件=匹配项.get('event') if isinstance(匹配项,dict) else None
    if isinstance(事件,dict) and 事件.get('type')=='turn/end':
        下一=dict(状态)
        下一['end']=匹配项
        return 下一
    return 状态


def 回合尾公布(匹配项):
    '只有回合结束立刻公布'
    事件=匹配项.get('event') if isinstance(匹配项,dict) else {}
    if 事件.get('type')=='turn/end':
        return 'immediate'
    return 'none'


def 回合尾建位置数据(上下文,范围):
    '页脚事实写在回合数据上'
    if 范围!='turn':
        return None
    值=尾数据(上下文)
    if 值 is None:
        return None
    return {'kind':'turn','turn':值['turn'],'key':'turn-tail','value':值}


def 回合尾建视图(上下文):
    '页脚跟在定稿内容后面'
    回合=回合位置(上下文)
    数据=None
    if isinstance(回合,dict) and hasattr(回合.get('data'),'get'):
        数据=回合['data'].get('turn-tail')
    if not isinstance(数据,dict):
        return None
    return 聊天节点(
        上下文,
        'turn-tail',
        数据.get('seq')+聊天合成序号偏移['finalizedFollowup'],
        数据,
        {'groupTree':'turn'},
    )


回合尾定义={
    'kind':'turn-tail',
    'target':'chat',
    'match':回合尾匹配,
    'start':回合尾开始,
    'update':回合尾更新,
    'publication':回合尾公布,
    'buildLocationData':回合尾建位置数据,
    'buildViewNode':回合尾建视图,
}


def 登记回合尾会话节点(上下文):
    '按事件类型分发匹配'
    def 匹配(事件):
        '转给定义上的匹配'
        return 回合尾匹配(事件)
    登记=dict(回合尾定义)
    登记['match']={
        'turn/start':匹配,
        'turn/end':匹配,
        'tool/call':匹配,
        'tool/result':匹配,
        'assistant/message':匹配,
        'assistant/attempt':匹配,
        'assistant/live-chunk':匹配,
        'step/start':匹配,
        'step/end':匹配,
        'llm/retry':匹配,
        'llm/retry-started':匹配,
    }
    上下文.uiConversation.events.register(登记)
