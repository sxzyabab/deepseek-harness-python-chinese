from ...异常 import 聊天错误
from .节点工厂 import 聊天合成序号偏移,聊天节点

__all__=['回合最大令牌定义']


def 位置(上下文):
    '起点位置，否则第一笔匹配的位置'
    起点=上下文.get('start') if isinstance(上下文.get('start'),dict) else None
    if isinstance(起点,dict) and isinstance(起点.get('location'),dict):
        return 起点['location']
    匹配=上下文.get('matches') if isinstance(上下文.get('matches'),list) else []
    if len(匹配)>0 and isinstance(匹配[0],dict) and isinstance(匹配[0].get('location'),dict):
        return 匹配[0]['location']
    return None


def 末步(上下文):
    '所属回合最后一步。不是回合或步骤就是 0'
    处=位置(上下文)
    if not isinstance(处,dict) or 处.get('kind') not in ('turn','step'):
        return 0
    回合=处.get('turn') if isinstance(处.get('turn'),dict) else {}
    步表=回合.get('steps') if isinstance(回合.get('steps'),list) else []
    if len(步表)==0 or not isinstance(步表[-1],dict):
        return 0
    return 步表[-1].get('step') if 步表[-1].get('step') is not None else 0


def 通知锚(上下文,序号):
    '夹在收束助手和回合尾之间。没有收束助手就停在截断点'
    处=位置(上下文)
    if not isinstance(处,dict) or 处.get('kind') not in ('turn','step'):
        return 序号
    回合=处.get('turn') if isinstance(处.get('turn'),dict) else {}
    数据=回合.get('data')
    尾=None
    if hasattr(数据,'get'):
        尾=数据.get('turn-tail')
    收束=尾.get('closing') if isinstance(尾,dict) else None
    if 收束 is None:
        return 序号
    终节点=收束.get('finalNode') if isinstance(收束,dict) and isinstance(收束.get('finalNode'),dict) else {}
    return 终节点.get('seq',序号)+聊天合成序号偏移['maxTokensNotice']


def 自结束(匹配项):
    '只有 max-tokens 的 turn/end 才建状态'
    事件=匹配项.get('event') if isinstance(匹配项,dict) else None
    if not isinstance(事件,dict) or 事件.get('type')!='turn/end':
        return None
    数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}
    原因=数据.get('reason') if isinstance(数据.get('reason'),dict) else {}
    if 原因.get('kind')!='max-tokens':
        return None
    return {'turn':数据.get('turn'),'seq':事件.get('seq'),'time':事件.get('time')}


def 最大令牌匹配(事件):
    '输出上限结束的回合'
    if 事件.get('type')=='turn/end':
        数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}
        原因=数据.get('reason') if isinstance(数据.get('reason'),dict) else {}
        if 原因.get('kind')=='max-tokens':
            return {'id':str(数据.get('turn')),'role':'start'}
    return None


def 最大令牌开始(上下文,匹配项):
    '必须是 max-tokens 的回合结束'
    状态=自结束(匹配项)
    if 状态 is None:
        raise 聊天错误('turn-max-tokens start requires a max-tokens turn/end')
    return 状态


def 最大令牌更新(上下文,匹配项=None):
    '通知不再改状态'
    return 上下文.get('state')


def 最大令牌建视图(上下文):
    '通知放在组树的回合层'
    状态=上下文.get('state')
    if not isinstance(状态,dict):
        return None
    节点={
        'kind':'turn-max-tokens',
        'seq':状态.get('seq'),
        'time':状态.get('time'),
        'turn':状态.get('turn'),
        'step':末步(上下文),
    }
    return 聊天节点(上下文,'turn-max-tokens',通知锚(上下文,状态.get('seq')),节点,{'groupTree':'turn'})


回合最大令牌定义={
    'kind':'turn-max-tokens',
    'target':'chat',
    'match':最大令牌匹配,
    'start':最大令牌开始,
    'update':最大令牌更新,
    'buildViewNode':最大令牌建视图,
}
