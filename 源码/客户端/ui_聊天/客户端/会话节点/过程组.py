from .节点工厂 import 聊天错误
from ..约定.助手内容 import 有助手回复内容
from ..约定.聊天可见性 import 是可见聊天节点
from .过程活动记录 import 过程活动记录
import json

__all__=['过程状态','过程组定义']

独立种类=frozenset(['user','steering','turn-trigger','model-retry','turn-error','turn-max-tokens','turn-tail'])

def 回合于(节点):
    """turn 或 step 位置上的回合号。节点为 dict。"""
    位置=节点['location']
    种=位置['kind'] if 'kind' in 位置 else None
    if 种=='turn' or 种=='step':
        return 位置['turn']['turn']
    return None

def 有推理(节点):
    """助手步骤是否含非空推理块。"""
    if 节点['kind']!='assistant-step':
        return False
    for 块 in 节点['data']['blocks']:
        if 块['kind']=='reasoning' and 块['text'].strip()!='':
            return True
    return False

def 有回复(节点):
    """助手步骤是否含可见回复。"""
    return 节点['kind']=='assistant-step' and 有助手回复内容(节点['data']['blocks'])

def 同摘要(左,右):
    """运行态与计数字段全等。"""
    if 左['running']!=右['running'] or 左['runningDetail']!=右['runningDetail']:
        return False
    左备=左['preparing'] if 'preparing' in 左 else None
    右备=右['preparing'] if 'preparing' in 右 else None
    if 左备!=右备:
        return False
    if len(左['counts'])!=len(右['counts']):
        return False
    下标=0
    while 下标<len(左['counts']):
        甲=左['counts'][下标]
        乙=右['counts'][下标]
        if 甲['kind']!=乙['kind'] or 甲['count']!=乙['count']:
            return False
        下标+=1
    return True

def 同成员(左,右):
    """成员键与组分全等。"""
    if len(左)!=len(右):
        return False
    下标=0
    while 下标<len(左):
        甲=左[下标]
        乙=右[下标]
        甲分=甲['groupPart'] if 'groupPart' in 甲 else None
        乙分=乙['groupPart'] if 'groupPart' in 乙 else None
        if 甲['key']!=乙['key'] or 甲分!=乙分:
            return False
        下标+=1
    return True

def 结构已变(先前,当前):
    """种类、回合、可见性或推理/回复边界变化。"""
    if not 是可见聊天节点(当前) and (先前 is None or not 是可见聊天节点(先前)):
        return False
    if 先前 is None:
        return True
    return (先前['kind']!=当前['kind']
        or 回合于(先前)!=回合于(当前)
        or 是可见聊天节点(先前)!=是可见聊天节点(当前)
        or 有推理(先前)!=有推理(当前) or 有回复(先前)!=有回复(当前))

def 读节点(输入,键):
    """当前目标节点；缺失则失败。输入为 dict。"""
    节点=输入['readNode'](键)
    if 节点 is None:
        raise 聊天错误('Chat grouping input is missing Node '+str(键))
    return 节点

def 读位置(输入,键):
    """可见位置；缺失则失败。"""
    位置=输入['readPosition'](键)
    if 位置 is None:
        raise 聊天错误('Chat grouping order is missing position for Node '+str(键))
    return 位置

def 回合已关(输入,回合):
    """时间线该回合是否 closed。"""
    回合表=输入['timeline']['turns']
    if 回合 not in 回合表:
        return False
    return 回合表[回合]['status']=='closed'

class 过程组:
    """一组的成员与缓存摘要；内容变则一起刷新。"""
    def __init__(自身,键,回合,成员列表):
        """空摘要起步。"""
        自身.键=键
        自身.回合=回合
        自身.成员列表=成员列表
        自身.节点列表=()
        自身.快照={'key':键,'members':成员列表,'data':{'turn':回合,'closed':False,'summary':{'counts':(),'running':None,'runningDetail':''}}}

    def 刷新(自身,输入,已闭合):
        """按当前成员重算摘要。"""
        节点列表=tuple(读节点(输入,成员['key']) for 成员 in 自身.成员列表)
        未变=len(节点列表)==len(自身.节点列表)
        if 未变:
            下标=0
            while 下标<len(节点列表):
                if 节点列表[下标] is not 自身.节点列表[下标]:
                    未变=False
                    break
                下标+=1
        先前=自身.快照['data']
        活动=先前['summary'] if 未变 and 先前['closed']==已闭合 else 过程活动记录(节点列表)
        摘要={'counts':活动['counts'],'running':None,'runningDetail':''} if 已闭合 else 活动
        自身.节点列表=节点列表
        if 先前['closed']!=已闭合 or not 同摘要(先前['summary'],摘要):
            自身.快照={'key':自身.键,'members':自身.成员列表,'data':{'turn':自身.回合,'closed':已闭合,'summary':摘要}}

class 回合分组:
    """一轮的分组结果与成员查找。"""
    def __init__(自身,回合):
        """空表。"""
        自身.回合=回合
        自身.组表={}
        自身.归属={}
        自身.根表={}

    def 引用表(自身,键):
        """该节点根引用。"""
        return 自身.根表[键] if 键 in 自身.根表 else ()

    def 快照表(自身):
        """各组当前快照。"""
        return [组.快照 for 组 in 自身.组表.values()]

    def 刷新(自身,输入,已变):
        """只重算内容变化的组。"""
        脏=set()
        for 节点键 in 已变:
            if 节点键 in 自身.归属:
                脏.add(自身.归属[节点键])
        已结束=回合已关(输入,自身.回合)
        if 已结束:
            for 组 in 自身.组表.values():
                if not 组.快照['data']['closed']:
                    脏.add(组.键)
        写入=[]
        for 键 in 脏:
            组=自身.组表[键]
            先前=组.快照
            组.刷新(输入,先前['data']['closed'] or 已结束)
            if 组.快照 is not 先前:
                写入.append(组.快照)
        return 写入

    def 重建(自身,输入,新增):
        """按当前回合可见序重切分组。"""
        根表={}
        组表={}
        归属={}
        待发=[]
        写入=[]
        def 发出(键,条目):
            """追加该节点的根引用。"""
            已有=list(根表[键]) if 键 in 根表 else []
            已有.append(条目)
            根表[键]=tuple(已有)
        def 冲刷(已闭合):
            """把待发成员收成一组。"""
            nonlocal 待发
            if len(待发)==0:
                return
            首=待发[0]
            留用=自身.延伸组(待发,新增)
            组分=首['groupPart'] if 'groupPart' in 首 else None
            键=留用.键 if 留用 is not None else json.dumps(['process',首['key'],组分],ensure_ascii=False,separators=(',',':'),allow_nan=False)
            先前=自身.组表[键] if 键 in 自身.组表 else None
            之前=先前.快照 if 先前 is not None else None
            if 先前 is not None and 同成员(先前.成员列表,待发):
                组=先前
            else:
                组=过程组(键,自身.回合,tuple(待发))
            组.刷新(输入,已闭合 or 回合已关(输入,自身.回合))
            组表[组.键]=组
            发出(首['key'],{'kind':'group','key':组.键})
            for 成员 in 待发:
                归属[成员['key']]=组.键
            if 组.快照 is not 之前:
                写入.append(组.快照)
            待发=[]
        先前键=None
        后续=False
        for 键 in 输入['readTurn'](自身.回合):
            位置=读位置(输入,键)
            if 先前键 is not None and 位置['previous']!=先前键:
                冲刷(True)
            先前键=键
            后续=位置['next'] is not None
            节点=读节点(输入,键)
            种=节点['kind']
            if 种 in 独立种类:
                冲刷(True)
                发出(键,{'kind':'node','key':键})
            elif 种=='turn-process':
                发出(键,{'kind':'node','key':键})
            elif 种=='assistant-step':
                if 有推理(节点):
                    待发.append({'kind':'node','key':键,'groupPart':'reasoning'})
                if 有回复(节点):
                    冲刷(True)
                    发出(键,{'kind':'node','key':键,'groupPart':'response'})
            else:
                待发.append({'kind':'node','key':键})
        冲刷(后续)
        移除=[键 for 键 in 自身.组表 if 键 not in 组表]
        自身.组表=组表
        自身.归属=归属
        自身.根表=根表
        return {'upserts':写入,'removes':移除}

    def 延伸组(自身,成员列表,新增):
        """仅当完整旧组仍夹在新可见成员之间时复用身份。"""
        偏移=0
        命中=False
        while 偏移<len(成员列表):
            if 成员列表[偏移]['key'] not in 新增:
                命中=True
                break
            偏移+=1
        if not 命中:
            return None
        首=成员列表[偏移]
        键=自身.归属[首['key']] if 首['key'] in 自身.归属 else None
        先前=自身.组表[键] if 键 is not None and 键 in 自身.组表 else None
        if 先前 is None or 偏移+len(先前.成员列表)>len(成员列表):
            return None
        下标=0
        while 下标<len(先前.成员列表):
            前=先前.成员列表[下标]
            后=成员列表[偏移+下标]
            前分=前['groupPart'] if 'groupPart' in 前 else None
            后分=后['groupPart'] if 'groupPart' in 后 else None
            if 前['key']!=后['key'] or 前分!=后分:
                return None
            下标+=1
        下标=偏移+len(先前.成员列表)
        while 下标<len(成员列表):
            if 成员列表[下标]['key'] not in 新增:
                return None
            下标+=1
        return 先前

class 过程状态:
    """会话内各回合结果；普通更新不读其他回合节点内容。"""
    def __init__(自身):
        """空序。"""
        自身.回合表={}
        自身.顺序=()
        自身.待发=None

    def 接受(自身,输入):
        """消费一次同步构建器输入，不保留其读取器。输入为 dict。"""
        if 输入['kind']=='replace':
            旧键=set(自身.顺序)
            新增=set()
            for 键 in 输入['order']:
                if 键 not in 旧键:
                    新增.add(键)
            回合表={}
            for 键 in 输入['order']:
                回合=读位置(输入,键)['turn']
                if 回合 is None or 回合 in 回合表:
                    continue
                分组=自身.回合表[回合] if 回合 in 自身.回合表 else 回合分组(回合)
                分组.重建(输入,新增)
                回合表[回合]=分组
            自身.回合表=回合表
            自身.顺序=输入['order']
            快照=[]
            for 分组 in 回合表.values():
                快照.extend(分组.快照表())
            自身.待发={'entries':自身.根条目(输入),'groups':{'kind':'replace','snapshots':快照}}
            return
        重切=set(输入['changedTurnOrders'])
        新增=set()
        已变={}
        def 触及(回合):
            """取出该回合已变键集。"""
            if 回合 not in 已变:
                已变[回合]=set()
            return 已变[回合]
        for 变更 in 输入['changes']:
            前=变更['previous']
            后=变更['current']
            回合=回合于(后)
            if 前 is None or not 是可见聊天节点(前):
                新增.add(后['key'])
            if 结构已变(前,后):
                先前回合=None if 前 is None else 回合于(前)
                if 先前回合 is not None:
                    重切.add(先前回合)
                if 回合 is not None:
                    重切.add(回合)
            if 回合 is not None:
                触及(回合).add(后['key'])
        for 回合 in 输入['changedTurns']:
            触及(回合)
        写入=[]
        移除=[]
        for 回合 in 重切:
            分组=自身.回合表[回合] if 回合 in 自身.回合表 else 回合分组(回合)
            更新=分组.重建(输入,新增)
            写入.extend(更新['upserts'])
            移除.extend(更新['removes'])
            if len(输入['readTurn'](回合))==0:
                自身.回合表.pop(回合,None)
            else:
                自身.回合表[回合]=分组
        for 回合 in 已变:
            if 回合 not in 重切 and 回合 in 自身.回合表:
                写入.extend(自身.回合表[回合].刷新(输入,已变[回合]))
        重排=输入['order'] is not 自身.顺序 or len(重切)>0
        自身.顺序=输入['order']
        已装=set(组['key'] for 组 in 写入)
        if 重排 or len(写入)>0 or len(移除)>0:
            更新={'groups':{'kind':'apply','upserts':写入,'removes':[键 for 键 in 移除 if 键 not in 已装]}}
            if 重排:
                更新['entries']=自身.根条目(输入)
            自身.待发=更新
        else:
            自身.待发=None

    def 根条目(自身,输入):
        """按目标序展开各组根引用。"""
        结果=[]
        for 键 in 输入['order']:
            回合=读位置(输入,键)['turn']
            if 回合 is None:
                结果.append({'kind':'node','key':键})
                continue
            if 回合 not in 自身.回合表:
                raise 聊天错误('Chat grouping order is missing Turn '+str(回合))
            结果.extend(自身.回合表[回合].引用表(键))
        return 结果

    def 输出(自身):
        """读待发输出，不推进状态。"""
        return 自身.待发

def 创建过程状态():
    """会话局部过程状态。"""
    return 过程状态()

def 更新过程组(上下文,输入):
    """消费输入并交回同一状态。上下文为 dict。"""
    上下文['state'].接受(输入)
    return 上下文['state']

def 构建过程组(上下文):
    """物化待发分组。"""
    return 上下文['state'].输出()

过程组定义={
    'kind':'process-groups','target':'chat',
    'create':创建过程状态,
    'update':更新过程组,
    'buildGroups':构建过程组,
}
