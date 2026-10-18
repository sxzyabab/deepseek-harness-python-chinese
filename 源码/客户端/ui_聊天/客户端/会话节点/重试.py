from ...异常 import 聊天错误
from .节点工厂 import 聊天节点

__all__=['重试定义']


def 已关闭(位置):
    '所属步骤或回合已经关闭，排队中的重试就取消'
    if not isinstance(位置,dict):
        return False
    if 位置.get('kind')=='step':
        步=位置.get('step') if isinstance(位置.get('step'),dict) else {}
        if 步.get('status')=='closed':
            return True
    if 位置.get('kind') in ('step','turn'):
        回合=位置.get('turn') if isinstance(位置.get('turn'),dict) else {}
        if 回合.get('status')=='closed':
            return True
    return False


def 排队节点(匹配项):
    'llm/retry 折成一次排队中的尝试'
    事件=匹配项.get('event') if isinstance(匹配项,dict) else None
    if not isinstance(事件,dict) or 事件.get('type')!='llm/retry':
        return None
    数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}
    节点={
        'kind':'model-retry',
        'seq':事件.get('seq'),
        'time':事件.get('time'),
        'retryState':'scheduled',
    }
    节点.update(数据)
    return 节点


def 重试匹配(事件):
    '同一次 retryId 的排队和开始'
    if 事件.get('type')=='llm/retry':
        数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}
        标识=数据.get('retryId')
        if not isinstance(标识,str) or 标识=='':
            return None
        return {'id':标识,'role':'start' if 数据.get('retry')==1 else 'update'}
    if 事件.get('type')=='llm/retry-started':
        数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}
        标识=数据.get('retryId')
        if isinstance(标识,str) and 标识!='':
            return {'id':标识,'role':'update'}
        return None
    return None


def 重试开始(上下文,匹配项):
    '第一次排队建立尝试列表'
    节点=排队节点(匹配项)
    if 节点 is None:
        raise 聊天错误('model-retry start requires a valid llm/retry event')
    return {'turn':节点.get('turn'),'step':节点.get('step'),'attempts':[节点]}


def 重试更新(上下文,匹配项):
    '再排队就追加。开始事件把对应次数标成已开始'
    状态=上下文.get('state') if isinstance(上下文.get('state'),dict) else {}
    事件=匹配项.get('event') if isinstance(匹配项,dict) else None
    if isinstance(事件,dict) and 事件.get('type')=='llm/retry':
        节点=排队节点(匹配项)
        if 节点 is None:
            return 状态
        下一=dict(状态)
        尝试=list(状态.get('attempts') if isinstance(状态.get('attempts'),list) else [])
        尝试.append(节点)
        下一['attempts']=尝试
        return 下一
    if not isinstance(事件,dict) or 事件.get('type')!='llm/retry-started':
        return 状态
    次数=事件.get('data',{}).get('retry') if isinstance(事件.get('data'),dict) else None
    下一=dict(状态)
    新尝试=[]
    for 尝试 in 状态.get('attempts') if isinstance(状态.get('attempts'),list) else []:
        if isinstance(尝试,dict) and 尝试.get('retry')==次数:
            副本=dict(尝试)
            副本['retryState']='started'
            新尝试.append(副本)
        else:
            新尝试.append(尝试)
    下一['attempts']=新尝试
    return 下一


def 重试建视图(上下文):
    '最后一次如果还在排队且边界已关，标成已取消'
    状态=上下文.get('state')
    if not isinstance(状态,dict) or not isinstance(状态.get('attempts'),list) or len(状态['attempts'])==0:
        return None
    起点=上下文.get('start') if isinstance(上下文.get('start'),dict) else None
    匹配=上下文.get('matches') if isinstance(上下文.get('matches'),list) else []
    if isinstance(起点,dict) and isinstance(起点.get('location'),dict):
        位置=起点['location']
    elif len(匹配)>0 and isinstance(匹配[0],dict) and isinstance(匹配[0].get('location'),dict):
        位置=匹配[0]['location']
    else:
        位置={'kind':'unresolved'}
    原尝试=状态['attempts']
    尝试=[]
    下标=0
    for 项 in 原尝试:
        if (
            下标==len(原尝试)-1
            and isinstance(项,dict)
            and 项.get('retryState')=='scheduled'
            and 已关闭(位置)
        ):
            副本=dict(项)
            副本['retryState']='cancelled'
            尝试.append(副本)
        else:
            尝试.append(项)
        下标+=1
    当前=尝试[-1]
    if not isinstance(当前,dict):
        return None
    首=尝试[0] if isinstance(尝试[0],dict) else {}
    锚=首.get('seq') if 首.get('seq') is not None else 当前.get('seq')
    return 聊天节点(上下文,'model-retry',锚,{'attempts':尝试,'current':当前},{'groupTree':'process'})


重试定义={
    'kind':'model-retry',
    'target':'chat',
    'match':重试匹配,
    'start':重试开始,
    'update':重试更新,
    'buildViewNode':重试建视图,
}
