'从检查器已加载的 Chat 快照得到精确和附近的定位候选'

import json

__all__=['解析聊天定位目标']

def 读(值,键,缺省=None):
    '快照字段'
    if 值 is None:
        return 缺省
    if isinstance(值,dict):
        return 值[键] if 键 in 值 else 缺省
    return getattr(值,键,缺省)

def 最近(节点表,序号):
    '锚点距离最近的节点；距离相同保留输入顺序'
    最佳=None
    for 节点 in 节点表:
        if 最佳 is None or abs(读(节点,'anchorSeq')-序号)<abs(读(最佳,'anchorSeq')-序号):
            最佳=节点
    return 最佳

def 节点目标(节点):
    '节点自己的坐标'
    位置=读(节点,'location') or {}
    种类=读(位置,'kind')
    结果={'nodeKey':读(节点,'key'),'anchorSeq':读(节点,'anchorSeq')}
    if 种类 in ('turn','step'):
        结果['turn']=读(读(位置,'turn'),'turn')
    if 种类=='step':
        结果['step']=读(读(位置,'step'),'step')
    return 结果

def 目标键(目标):
    '候选去重键'
    return json.dumps([
        目标.get('anchorSeq'),目标.get('callId'),目标.get('rootCallId'),目标.get('nodeKey'),目标.get('nodeKind'),
        目标.get('groupKey'),目标.get('groupPart'),目标.get('turn'),目标.get('step'),
    ],ensure_ascii=False)

def 主目标(目标,可见):
    '没有显式节点时，按工具、精确锚点、种类、最近距离放置'
    if 目标.get('nodeKey') is not None or 目标.get('anchorSeq') is None:
        return 目标
    if 目标.get('turn') is None:
        回合内=可见
    else:
        回合内=[]
        for 节点 in 可见:
            位置=读(节点,'location') or {}
            种类=读(位置,'kind')
            if 种类 in ('turn','step') and 读(读(位置,'turn'),'turn')==目标['turn']:
                回合内.append(节点)
    if 目标.get('step') is None:
        步内=回合内
    else:
        步内=[]
        for 节点 in 回合内:
            位置=读(节点,'location') or {}
            if 读(位置,'kind')=='step' and 读(读(位置,'step'),'step')==目标['step']:
                步内.append(节点)
    根调用=目标['rootCallId'] if 目标.get('rootCallId') is not None else 目标.get('callId')
    工具=None
    if 根调用 is not None:
        for 节点 in 可见:
            if 读(节点,'kind')=='tool-call' and 读(读(读(节点,'data'),'root'),'callId')==根调用:
                工具=节点
                break
    精确=None
    for 节点 in 步内:
        if 读(节点,'anchorSeq')==目标['anchorSeq']:
            精确=节点
            break
    种类命中=None
    if 目标.get('nodeKind') is not None:
        for 节点 in 步内:
            if 读(节点,'kind')==目标['nodeKind']:
                种类命中=节点
                break
    节点=工具 or 精确 or 种类命中 or 最近(步内,目标['anchorSeq']) or 最近(回合内,目标['anchorSeq'])
    if 节点 is None:
        return 目标
    位置=读(节点,'location') or {}
    回合=目标.get('turn')
    if 回合 is None and 读(位置,'kind') in ('turn','step'):
        回合=读(读(位置,'turn'),'turn')
    结果={**目标,'nodeKey':读(节点,'key')}
    if 回合 is not None:
        结果['turn']=回合
    return 结果

def 解析聊天定位目标(目标,节点表):
    '保留主身份，再按步、回合、会话给可见邻居排序'
    可见=[节点 for 节点 in 节点表 if 读(节点,'visibility')=='visible']
    显式=None
    if 目标.get('nodeKey') is not None:
        for 节点 in 节点表:
            if 读(节点,'key')==目标['nodeKey']:
                显式=节点
                break
    位置=None if 显式 is None else 节点目标(显式)
    参考序号=目标.get('anchorSeq') if 目标.get('anchorSeq') is not None else (None if 位置 is None else 位置.get('anchorSeq'))
    回合=目标.get('turn') if 目标.get('turn') is not None else (None if 位置 is None else 位置.get('turn'))
    步=目标.get('step') if 目标.get('step') is not None else (None if 位置 is None else 位置.get('step'))
    if 位置 is None:
        主=主目标(目标,可见)
    else:
        主={**目标}
        if 目标.get('anchorSeq') is None:
            主['anchorSeq']=位置.get('anchorSeq')
        if 回合 is not None:
            主['turn']=回合
        if 步 is not None:
            主['step']=步
    if 参考序号 is None:
        return [主]
    def 等级(候选):
        '同一步 0，同一回合 1，其余 2'
        同回合=回合 is None or 候选.get('turn')==回合
        if 同回合 and 步 is not None and 候选.get('step')==步:
            return 0
        if 同回合 and 回合 is not None:
            return 1
        return 2
    邻居=sorted((节点目标(节点) for 节点 in 可见),key=lambda 候选:(等级(候选),abs(候选['anchorSeq']-参考序号)))
    候选表=[主]
    见过={目标键(主)}
    for 候选 in 邻居:
        键=目标键(候选)
        if 键 in 见过:
            continue
        见过.add(键)
        候选表.append(候选)
    return 候选表
