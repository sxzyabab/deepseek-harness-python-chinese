import json
from ...异常 import 聊天错误
from ..约定.助手内容 import 有助手回复内容
from ..约定.聊天可见性 import 是可见聊天节点
from ..约定.组树 import 在该层或更外
from .过程活动记录 import 过程活动

__all__=['过程组定义','过程状态']


def 节点回合(节点):
    '节点落到的回合'
    if not isinstance(节点,dict):
        return None
    位置=节点.get('location')
    if isinstance(位置,dict) and 位置.get('kind') in ('turn','step'):
        回合=位置.get('turn') if isinstance(位置.get('turn'),dict) else {}
        return 回合.get('turn')
    return None


def 是推理(节点):
    '助手步骤里有非空推理'
    if not isinstance(节点,dict) or 节点.get('kind')!='assistant-step':
        return False
    数据=节点.get('data') if isinstance(节点.get('data'),dict) else {}
    块表=数据.get('blocks') if isinstance(数据.get('blocks'),list) else []
    for 块 in 块表:
        if isinstance(块,dict) and 块.get('kind')=='reasoning':
            文=块.get('text')
            if isinstance(文,str) and 文.strip()!='':
                return True
    return False


def 是回复(节点):
    '助手步骤里有面对用户的回复'
    if not isinstance(节点,dict) or 节点.get('kind')!='assistant-step':
        return False
    数据=节点.get('data') if isinstance(节点.get('data'),dict) else {}
    块表=数据.get('blocks') if isinstance(数据.get('blocks'),list) else []
    return 有助手回复内容(块表)


def 摘要相同(左,右):
    '两组活动摘要的计数和正在跑的细节一样'
    if not isinstance(左,dict) or not isinstance(右,dict):
        return False
    if 左.get('running')!=右.get('running') or 左.get('runningDetail')!=右.get('runningDetail') or 左.get('preparing')!=右.get('preparing'):
        return False
    左计数=左.get('counts') if isinstance(左.get('counts'),list) else []
    右计数=右.get('counts') if isinstance(右.get('counts'),list) else []
    if len(左计数)!=len(右计数):
        return False
    下标=0
    for 项 in 左计数:
        对=右计数[下标] if 下标<len(右计数) else None
        if not isinstance(项,dict) or not isinstance(对,dict) or 项.get('kind')!=对.get('kind') or 项.get('count')!=对.get('count'):
            return False
        下标+=1
    return True


def 成员相同(左,右):
    '两组成员的键和分段一样'
    if len(左)!=len(右):
        return False
    下标=0
    for 项 in 左:
        对=右[下标]
        if 项.get('key')!=对.get('key') or 项.get('groupPart')!=对.get('groupPart'):
            return False
        下标+=1
    return True


def 结构变了(先前,当前):
    '可见性、种类、回合、组树或推理回复变了就要重组'
    if not 是可见聊天节点(当前) and (先前 is None or not 是可见聊天节点(先前)):
        return False
    if 先前 is None:
        return True
    return (
        先前.get('kind')!=当前.get('kind')
        or 节点回合(先前)!=节点回合(当前)
        or 是可见聊天节点(先前)!=是可见聊天节点(当前)
        or 先前.get('groupTree')!=当前.get('groupTree')
        or 是推理(先前)!=是推理(当前)
        or 是回复(先前)!=是回复(当前)
    )


def 读节点(输入,键):
    '分组输入里必须能读到这个节点'
    节点=输入['readNode'](键)
    if 节点 is None:
        raise 聊天错误('Chat grouping input is missing Node '+str(键))
    return 节点


def 读位置(输入,键):
    '分组顺序里必须有这个节点的位置'
    位置=输入['readPosition'](键)
    if 位置 is None:
        raise 聊天错误('Chat grouping order is missing position for Node '+str(键))
    return 位置


class 过程组:
    '一组的成员和缓存摘要。内容变了一起刷新'
    def __init__(自身,键,回合,成员):
        '先给一份空摘要'
        自身.key=键
        自身.turn=回合
        自身.members=成员
        自身.节点=[]
        自身.snapshot={
            'key':键,
            'members':成员,
            'data':{'turn':回合,'closed':False,'summary':{'counts':[],'running':None,'runningDetail':''}},
        }

    def 刷新(自身,输入,已关):
        '成员没变且开关没变就留着旧摘要'
        节点表=[读节点(输入,成员['key']) for 成员 in 自身.members]
        未变=len(节点表)==len(自身.节点)
        if 未变:
            下标=0
            for 节点 in 节点表:
                if 节点 is not 自身.节点[下标]:
                    未变=False
                    break
                下标+=1
        先前=自身.snapshot['data']
        if 未变 and 先前.get('closed')==已关:
            活动=先前.get('summary')
        else:
            活动=过程活动(节点表)
        if 已关:
            摘要={'counts':活动.get('counts'),'running':None,'runningDetail':''}
        else:
            摘要=活动
        自身.节点=节点表
        if 先前.get('closed')!=已关 or not 摘要相同(先前.get('summary'),摘要):
            自身.snapshot={
                'key':自身.key,
                'members':自身.members,
                'data':{'turn':自身.turn,'closed':已关,'summary':摘要},
            }


class 回合组:
    '一个回合的分组结果'
    def __init__(自身,回合):
        '这个回合还没有组'
        自身.turn=回合
        自身.组={}
        自身.归属={}
        自身.根={}

    def 引用(自身,键):
        '这个根节点在渲染顺序里占的条目'
        return 自身.根.get(键,[])

    def 快照表(自身):
        '各组当前快照'
        return [组.snapshot for 组 in 自身.组.values()]

    def 刷新(自身,输入,变化键):
        '只刷新变化成员所属的组。回合结束后未关闭的组也刷新'
        脏=set()
        for 节点键 in 变化键:
            组键=自身.归属.get(节点键)
            if 组键 is not None:
                脏.add(组键)
        时间线=输入.get('timeline') if isinstance(输入.get('timeline'),dict) else {}
        回合表=时间线.get('turns') if isinstance(时间线.get('turns'),dict) else {}
        回合体=回合表.get(自身.turn)
        已结束=isinstance(回合体,dict) and 回合体.get('status')=='closed'
        if 已结束:
            for 组 in 自身.组.values():
                if not 组.snapshot['data'].get('closed'):
                    脏.add(组.key)
        更新=[]
        for 键 in 脏:
            组=自身.组[键]
            先前=组.snapshot
            组.刷新(输入,先前['data'].get('closed') or 已结束)
            if 组.snapshot is not 先前:
                更新.append(组.snapshot)
        return 更新

    def 重建(自身,输入,新增):
        '按回合内的节点顺序重切组'
        根={}
        组表={}
        归属={}
        待定=[]
        更新=[]

        def 发出(键,条目):
            '一个根可以占多条渲染条目'
            已有=list(根.get(键,[]))
            已有.append(条目)
            根[键]=已有

        def 吐出(已关):
            '把积下的成员收成一组'
            nonlocal 待定
            if len(待定)==0:
                return
            首=待定[0]
            沿用=自身.延伸组(待定,新增)
            if 沿用 is not None:
                键=沿用.key
            else:
                分段=首.get('groupPart')
                键=json.dumps(['process',首.get('key'),分段],ensure_ascii=False,separators=(',',':'))
            先前组=自身.组.get(键)
            之前=先前组.snapshot if 先前组 is not None else None
            if 先前组 is not None and 成员相同(先前组.members,待定):
                组=先前组
            else:
                组=过程组(键,自身.turn,待定)
            时间线=输入.get('timeline') if isinstance(输入.get('timeline'),dict) else {}
            回合表=时间线.get('turns') if isinstance(时间线.get('turns'),dict) else {}
            回合体=回合表.get(自身.turn)
            回合关=isinstance(回合体,dict) and 回合体.get('status')=='closed'
            组.刷新(输入,已关 or 回合关)
            组表[组.key]=组
            发出(首['key'],{'kind':'group','key':组.key})
            for 成员 in 待定:
                归属[成员['key']]=组.key
            if 组.snapshot is not 之前:
                更新.append(组.snapshot)
            待定=[]

        上一个=None
        有后继=False
        for 键 in 输入['readTurn'](自身.turn):
            位置=读位置(输入,键)
            if 上一个 is not None and 位置.get('previous')!=上一个:
                吐出(True)
            上一个=键
            有后继=位置.get('next') is not None
            节点=读节点(输入,键)
            if 在该层或更外(节点,'process'):
                吐出(True)
                发出(键,{'kind':'node','key':键})
            elif 节点.get('kind')=='assistant-step':
                if 是推理(节点):
                    待定.append({'kind':'node','key':键,'groupPart':'reasoning'})
                if 是回复(节点):
                    吐出(True)
                    发出(键,{'kind':'node','key':键,'groupPart':'response'})
            else:
                待定.append({'kind':'node','key':键})
        吐出(有后继)
        移除=[键 for 键 in 自身.组 if 键 not in 组表]
        自身.组=组表
        自身.归属=归属
        自身.根=根
        return {'upserts':更新,'removes':移除}

    def 延伸组(自身,成员,新增):
        '只有整段旧组还夹在新可见成员之间时才沿用身份'
        偏移=None
        下标=0
        for 成员项 in 成员:
            if 成员项.get('key') not in 新增:
                偏移=下标
                break
            下标+=1
        if 偏移 is None:
            return None
        首=成员[偏移]
        键=自身.归属.get(首.get('key'))
        先前=自身.组.get(键) if 键 is not None else None
        if 先前 is None or 偏移+len(先前.members)>len(成员):
            return None
        下标=0
        for 之前 in 先前.members:
            之后=成员[偏移+下标]
            if 之前.get('key')!=之后.get('key') or 之前.get('groupPart')!=之后.get('groupPart'):
                return None
            下标+=1
        下标=偏移+len(先前.members)
        while 下标<len(成员):
            if 成员[下标].get('key') not in 新增:
                return None
            下标+=1
        return 先前


class 过程状态:
    '会话内各回合的分组。普通更新不读别的回合的节点内容'
    def __init__(自身):
        '还没有回合，也没有待公布的更新'
        自身.回合={}
        自身.顺序=[]
        自身.待定=None

    def 接受(自身,输入):
        '吃掉这一批同步输入，不留读者'
        if 输入.get('kind')=='replace':
            旧键=set(自身.顺序)
            新增=set(键 for 键 in 输入.get('order',[]) if 键 not in 旧键)
            回合表={}
            for 键 in 输入.get('order',[]):
                回合=读位置(输入,键).get('turn')
                if 回合 is None or 回合 in 回合表:
                    continue
                组=自身.回合.get(回合)
                if 组 is None:
                    组=回合组(回合)
                组.重建(输入,新增)
                回合表[回合]=组
            自身.回合=回合表
            自身.顺序=list(输入.get('order',[]))
            快照=[]
            for 组 in 回合表.values():
                快照.extend(组.快照表())
            自身.待定={
                'entries':自身.根条目(输入),
                'groups':{'kind':'replace','snapshots':快照},
            }
            return
        重组=set(输入.get('changedTurnOrders') or [])
        新增=set()
        变化={}
        for 变更 in 输入.get('changes') or []:
            之前=变更.get('previous')
            之后=变更.get('current')
            回合=节点回合(之后)
            if 之前 is None or not 是可见聊天节点(之前):
                新增.add(之后.get('key'))
            if 结构变了(之前,之后):
                先前回合=节点回合(之前) if 之前 is not None else None
                if 先前回合 is not None:
                    重组.add(先前回合)
                if 回合 is not None:
                    重组.add(回合)
            if 回合 is not None:
                if 回合 not in 变化:
                    变化[回合]=set()
                变化[回合].add(之后.get('key'))
        for 回合 in 输入.get('changedTurns') or []:
            if 回合 not in 变化:
                变化[回合]=set()
        更新=[]
        移除=[]
        for 回合 in 重组:
            组=自身.回合.get(回合)
            if 组 is None:
                组=回合组(回合)
            结果=组.重建(输入,新增)
            更新.extend(结果['upserts'])
            移除.extend(结果['removes'])
            if len(输入['readTurn'](回合))==0:
                if 回合 in 自身.回合:
                    del 自身.回合[回合]
            else:
                自身.回合[回合]=组
        for 回合,键集 in 变化.items():
            if 回合 not in 重组 and 回合 in 自身.回合:
                更新.extend(自身.回合[回合].刷新(输入,键集))
        重排=输入.get('order') is not 自身.顺序 or len(重组)>0
        自身.顺序=list(输入.get('order') or [])
        已装=set(组.get('key') for 组 in 更新)
        if 重排 or len(更新)>0 or len(移除)>0:
            待定={'groups':{'kind':'apply','upserts':更新,'removes':[键 for 键 in 移除 if 键 not in 已装]}}
            if 重排:
                待定['entries']=自身.根条目(输入)
            自身.待定=待定
        else:
            自身.待定=None

    def 根条目(自身,输入):
        '按顺序展开各组的渲染条目'
        条目=[]
        for 键 in 输入.get('order') or []:
            回合=读位置(输入,键).get('turn')
            if 回合 is None:
                条目.append({'kind':'node','key':键})
                continue
            组=自身.回合.get(回合)
            if 组 is None:
                raise 聊天错误('Chat grouping order is missing Turn '+str(回合))
            条目.extend(组.引用(键))
        return 条目

    def 输出(自身):
        '上一批输入对应的更新。再读一次还是这一份'
        return 自身.待定


def 创建过程状态():
    '一份会话一份分组状态'
    return 过程状态()


def 更新过程状态(上下文,输入):
    '接受输入后仍返回同一份状态'
    上下文['state'].接受(输入)
    return 上下文['state']


def 构建组(上下文):
    '读出待公布的组更新'
    return 上下文['state'].输出()


过程组定义={
    'kind':'process-groups',
    'target':'chat',
    'create':创建过程状态,
    'update':更新过程状态,
    'buildGroups':构建组,
}
