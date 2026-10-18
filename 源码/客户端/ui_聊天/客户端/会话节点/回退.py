from .....内核.会话.表面 import 是否追加表面事件
from .节点工厂 import 聊天节点

__all__=['未知回退定义']


def 未知匹配(事件):
    '没人认领的追加面事件。实时块除外'
    if 事件.get('type')!='assistant/live-chunk' and 是否追加表面事件(事件):
        return {'id':str(事件.get('seq')),'role':'start'}
    return None


def 未知开始(上下文,匹配项):
    '原样留下类型和数据'
    事件=匹配项.get('event') if isinstance(匹配项,dict) else {}
    return {
        'kind':'unknown',
        'seq':事件.get('seq'),
        'time':事件.get('time'),
        'type':事件.get('type'),
        'data':事件.get('data'),
    }


def 未知更新(上下文,匹配项=None):
    '未知行不再改'
    return 上下文.get('state')


def 未知建视图(上下文):
    '有状态才成行'
    状态=上下文.get('state')
    if not isinstance(状态,dict):
        return None
    return 聊天节点(上下文,'unknown',状态.get('seq'),状态)


未知回退定义={
    'kind':'unknown-surface',
    'target':'chat',
    'match':未知匹配,
    'start':未知开始,
    'update':未知更新,
    'buildViewNode':未知建视图,
}
