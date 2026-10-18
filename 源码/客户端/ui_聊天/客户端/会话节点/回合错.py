from ...异常 import 聊天错误
from .事件投影 import 展示失败
from .节点工厂 import 聊天节点

__all__=['回合错定义']


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
    '所属回合最后一步'
    处=位置(上下文)
    if not isinstance(处,dict) or 处.get('kind') not in ('turn','step'):
        return 0
    回合=处.get('turn') if isinstance(处.get('turn'),dict) else {}
    步表=回合.get('steps') if isinstance(回合.get('steps'),list) else []
    if len(步表)==0 or not isinstance(步表[-1],dict):
        return 0
    return 步表[-1].get('step') if 步表[-1].get('step') is not None else 0


def 结束失败(原因):
    '错误、退出登录、进程中断才有失败行。完成和截断没有'
    if not isinstance(原因,dict):
        return None
    种类=原因.get('kind')
    if 种类=='error':
        return 原因.get('error')
    if 种类=='aborted':
        内因=原因.get('reason') if isinstance(原因.get('reason'),dict) else {}
        if 内因.get('kind')=='hook' and 内因.get('reason')=='deepseek-account/signed-out':
            return {'message':'Stopped because you signed out of DeepSeek.','code':'ACCOUNT_SIGNED_OUT'}
        return None
    if 种类=='interrupted':
        return {'message':'The DSH process exited before this turn finished.','code':'INTERRUPTED'}
    return None


def 自失败(匹配项):
    'turn/end 上的可展示失败'
    事件=匹配项.get('event') if isinstance(匹配项,dict) else None
    if not isinstance(事件,dict) or 事件.get('type')!='turn/end':
        return None
    数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}
    失败=结束失败(数据.get('reason'))
    if 失败 is None:
        return None
    展示=展示失败(失败)
    结果={
        'seq':事件.get('seq'),
        'time':事件.get('time'),
        'message':展示.get('message'),
    }
    if 展示.get('code') is not None:
        结果['code']=展示['code']
    return 结果


def 回合错匹配(事件):
    '回合开始认领。结束时只有真有失败才更新'
    if 事件.get('type')=='turn/start':
        数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}
        return {'id':str(数据.get('turn')),'role':'start'}
    if 事件.get('type')=='turn/end':
        数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}
        if 结束失败(数据.get('reason')) is not None:
            return {'id':str(数据.get('turn')),'role':'update'}
    return None


def 回合错开始(上下文,匹配项):
    '必须从 turn/start 开始'
    事件=匹配项.get('event') if isinstance(匹配项,dict) else None
    if not isinstance(事件,dict) or 事件.get('type')!='turn/start':
        raise 聊天错误('turn-error start requires turn/start')
    数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}
    return {'turn':数据.get('turn')}


def 回合错更新(上下文,匹配项):
    '把失败写进状态'
    状态=上下文.get('state') if isinstance(上下文.get('state'),dict) else {}
    失败=自失败(匹配项)
    if 失败 is None:
        return 状态
    下一=dict(状态)
    下一['failure']=失败
    return 下一


def 回合错回退(上下文):
    '没有状态时从已加载的失败结束补'
    匹配=上下文.get('matches') if isinstance(上下文.get('matches'),list) else []
    结束=None
    for 项 in 匹配:
        if 自失败(项) is not None:
            结束=项
            break
    if not isinstance(结束,dict) or not isinstance(结束.get('event'),dict) or 结束['event'].get('type')!='turn/end':
        return None
    失败=自失败(结束)
    if 失败 is None:
        return None
    数据=结束['event'].get('data') if isinstance(结束['event'].get('data'),dict) else {}
    return {'turn':数据.get('turn'),'failure':失败}


def 回合错建视图(上下文):
    '终局失败单独成行。重试历史不压掉这一行'
    状态=上下文.get('state')
    if not isinstance(状态,dict):
        状态=回合错回退(上下文)
    if not isinstance(状态,dict) or not isinstance(状态.get('failure'),dict):
        return None
    失败=状态['failure']
    节点={
        'kind':'turn-error',
        'seq':失败.get('seq'),
        'time':失败.get('time'),
        'turn':状态.get('turn'),
        'step':末步(上下文),
        'message':失败.get('message'),
    }
    if 失败.get('code') is not None:
        节点['code']=失败['code']
    return 聊天节点(上下文,'turn-error',节点.get('seq'),节点,{'groupTree':'turn'})


回合错定义={
    'kind':'turn-error',
    'target':'chat',
    'match':回合错匹配,
    'start':回合错开始,
    'update':回合错更新,
    'buildViewNode':回合错建视图,
}
