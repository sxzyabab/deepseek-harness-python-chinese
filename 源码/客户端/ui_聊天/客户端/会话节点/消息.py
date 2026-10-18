from .....内核.会话.表面 import 是否追加表面事件,是否替换表面事件
from ...异常 import 聊天错误
from .事件投影 import 上下文形态,上下文生产者
from .节点工厂 import 上下文位置,聊天节点

__all__=['消息定义','开发者消息定义']


def 是压缩检查点(事件):
    '替换面上的 compact 检查点不属于普通输入消息'
    if 事件.get('type')!='user/message' or not 是否替换表面事件(事件):
        return False
    数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}
    来源=数据.get('source') if isinstance(数据.get('source'),dict) else {}
    return 来源.get('kind')=='compact-checkpoint'


def 上下文消息(事件,消息):
    '用户角色注入和开发者消息共用的上下文呈现'
    来源=消息.get('source')
    return {
        'kind':'context',
        'seq':事件.get('seq'),
        'time':事件.get('time'),
        'content':消息.get('content'),
        'source':来源,
        'producer':上下文生产者(来源),
        'form':上下文形态(来源),
    }


def 消息匹配(事件):
    '追加面的用户消息，排除压缩检查点'
    if 事件.get('type')!='user/message':
        return None
    if 是否追加表面事件(事件) and not 是压缩检查点(事件):
        数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}
        return {'id':str(数据.get('id')),'role':'start'}
    return None


def 消息开始(上下文,匹配项,读取器):
    '非用户来源是上下文。已认领的用户消息是插话。其余是用户'
    事件=匹配项.get('event') if isinstance(匹配项,dict) else None
    if not isinstance(事件,dict) or 事件.get('type')!='user/message':
        raise 聊天错误('input-message start requires user/message')
    数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}
    来源=数据.get('source') if isinstance(数据.get('source'),dict) else {}
    if 来源.get('kind')!='user':
        下一回合=读取器.previous('inbox-next-turn')
        下一步=读取器.previous('inbox-next-step')
        下一回合态=下一回合.get('state') if isinstance(下一回合,dict) else None
        下一步态=下一步.get('state') if isinstance(下一步,dict) else None
        位置=匹配项.get('location') if isinstance(匹配项.get('location'),dict) else {}
        回合=位置.get('turn') if isinstance(位置.get('turn'),dict) else {}
        步=位置.get('step') if isinstance(位置.get('step'),dict) else {}
        回合起点=回合.get('start') if isinstance(回合.get('start'),dict) else None
        回合起序号=回合起点.get('seq') if isinstance(回合起点,dict) else None
        下一步认领=下一步态.get('claimSeq') if isinstance(下一步态,dict) and 下一步态.get('claimSeq') is not None else -1
        下一回合认领=下一回合态.get('claimSeq') if isinstance(下一回合态,dict) and 下一回合态.get('claimSeq') is not None else -1
        已认领集=下一步态.get('currentClaimed') if isinstance(下一步态,dict) and isinstance(下一步态.get('currentClaimed'),set) else set()
        空转插话=(
            位置.get('kind')=='step'
            and 步.get('step')==1
            and 回合起序号 is not None
            and 下一步认领>回合起序号
            and 下一回合认领<回合起序号
            and (下一步态.get('claimedHuman') if isinstance(下一步态,dict) else None) is False
            and str(数据.get('id')) in 已认领集
        )
        下一回合集=下一回合态.get('currentClaimed') if isinstance(下一回合态,dict) and isinstance(下一回合态.get('currentClaimed'),set) else set()
        节点=上下文消息(事件,数据)
        节点['waking']=str(数据.get('id')) in 下一回合集 or 空转插话
        return 节点
    下一步=读取器.previous('inbox-next-step')
    下一步态=下一步.get('state') if isinstance(下一步,dict) else None
    已认领集=下一步态.get('currentClaimed') if isinstance(下一步态,dict) and isinstance(下一步态.get('currentClaimed'),set) else set()
    已认领=str(数据.get('id')) in 已认领集
    if 已认领:
        return {
            'kind':'steering',
            'messageId':数据.get('id'),
            'seq':事件.get('seq'),
            'time':事件.get('time'),
            'content':数据.get('content'),
            'source':数据.get('source'),
        }
    return {
        'kind':'user',
        'seq':事件.get('seq'),
        'time':事件.get('time'),
        'content':数据.get('content'),
        'source':数据.get('source'),
    }


def 消息更新(上下文,匹配项=None):
    '输入消息不再改'
    return 上下文.get('state')


def 消息建视图(上下文):
    '唤醒的上下文是回合触发。人在第一步打开一轮交换'
    状态=上下文.get('state')
    if not isinstance(状态,dict):
        return None
    起点=上下文.get('start') if isinstance(上下文.get('start'),dict) else None
    起点事件=起点.get('event') if isinstance(起点,dict) else None
    唤醒=(
        状态.get('kind')=='context'
        and isinstance(起点事件,dict)
        and 起点事件.get('type')=='user/message'
        and 状态.get('waking') is True
    )
    位置=上下文位置(上下文)
    是人=状态.get('kind') in ('user','steering')
    步=位置.get('step') if isinstance(位置.get('step'),dict) else {}
    打开交换=是人 and 位置.get('kind')=='step' and 步.get('step')==1
    if 打开交换:
        组树='exchange'
    elif 是人 or 唤醒:
        组树='input'
    else:
        组树=None
    选项={'location':位置}
    if 组树 is not None:
        选项['groupTree']=组树
    return 聊天节点(
        上下文,
        'turn-trigger' if 唤醒 else 状态.get('kind'),
        状态.get('seq'),
        状态,
        选项,
    )


消息定义={
    'kind':'input-message',
    'target':'chat',
    'match':消息匹配,
    'start':消息开始,
    'update':消息更新,
    'buildViewNode':消息建视图,
}


def 开发者匹配(事件):
    '开发者消息走输入消息的生命周期'
    if 事件.get('type')=='developer/message':
        数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}
        消息=数据.get('message') if isinstance(数据.get('message'),dict) else {}
        return {'id':str(消息.get('id')),'role':'start'}
    return None


def 开发者开始(上下文,匹配项):
    '开发者消息呈现成上下文'
    事件=匹配项.get('event') if isinstance(匹配项,dict) else None
    if not isinstance(事件,dict) or 事件.get('type')!='developer/message':
        raise 聊天错误('developer-message start requires developer/message')
    数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}
    消息=数据.get('message') if isinstance(数据.get('message'),dict) else {}
    return 上下文消息(事件,消息)


开发者消息定义={
    'kind':'developer-message',
    'target':'chat',
    'match':开发者匹配,
    'start':开发者开始,
    'update':消息更新,
    'buildViewNode':消息建视图,
}
