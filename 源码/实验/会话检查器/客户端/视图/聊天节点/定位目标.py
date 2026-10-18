'从已加载的对话节点排出精确目标和附近目标'

import json#坐标去重用稳定文本

def 最近节点(节点列表,序号):
    '锚序号距离最近的节点。距离相同保留先出现的'
    最好=None#当前最近
    for 节点 in 节点列表:#逐个
        if 最好 is None or abs(节点.get('anchorSeq')-序号)<abs(最好.get('anchorSeq')-序号):#更近
            最好=节点#换掉
    return 最好#可能没有

def 节点坐标(节点):
    '只留下节点自己的序号和回合、步骤'
    位置=节点.get('location') if isinstance(节点.get('location'),dict) else {}#位置
    坐标={'nodeKey':节点.get('key'),'anchorSeq':节点.get('anchorSeq')}#节点和序号
    if 位置.get('kind') in ('turn','step') and isinstance(位置.get('turn'),dict):#有回合
        坐标['turn']=位置['turn'].get('turn')#回合号
    if 位置.get('kind')=='step' and isinstance(位置.get('step'),dict):#有步骤
        坐标['step']=位置['step'].get('step')#步骤号
    return 坐标#节点坐标

def 坐标键(目标):
    '用固定字段顺序区分两份坐标'
    return json.dumps([
        目标.get('anchorSeq'),目标.get('callId'),目标.get('rootCallId'),目标.get('nodeKey'),目标.get('nodeKind'),
        目标.get('groupKey'),目标.get('groupPart'),目标.get('turn'),目标.get('step'),
    ],ensure_ascii=False,separators=(',',':'))#稳定文本

def 解析聊天定位目标(目标,节点列表):
    '先保留主身份或就近落点，再按步骤、回合、会话给可见邻居排序'
    节点=list(节点列表)#可多次扫描
    可见=[]#当前可见节点
    for 一项 in 节点:#逐个
        if 一项.get('visibility')=='visible':#可见
            可见.append(一项)#留下
    明确=None#点名的节点，隐藏的也算
    if 目标.get('nodeKey') is not None:#有节点键
        for 一项 in 节点:#找这个键
            if 一项.get('key')==目标.get('nodeKey'):#命中
                明确=一项#记下
                break#停
    位置=None if 明确 is None else 节点坐标(明确)#节点自己的位置
    参考序号=目标.get('anchorSeq') if 目标.get('anchorSeq') is not None else (None if 位置 is None else 位置.get('anchorSeq'))#请求序号优先
    回合=目标.get('turn') if 目标.get('turn') is not None else (None if 位置 is None else 位置.get('turn'))#请求回合优先
    步=目标.get('step') if 目标.get('step') is not None else (None if 位置 is None else 位置.get('step'))#请求步骤优先
    if 位置 is None:#没有点名节点，按工具、精确序号、种类、最近落点补节点
        回合内=可见#先在可见节点里
        if 目标.get('turn') is not None:#限制回合
            回合内=[]#这个回合
            for 一项 in 可见:#逐个
                项位置=一项.get('location') if isinstance(一项.get('location'),dict) else {}#位置
                项回合=项位置.get('turn') if isinstance(项位置.get('turn'),dict) else {}#回合
                if 项位置.get('kind') in ('turn','step') and 项回合.get('turn')==目标.get('turn'):#同一回合
                    回合内.append(一项)#留下
        步骤内=回合内#再限制步骤
        if 目标.get('step') is not None:#有步骤
            步骤内=[]#这一步
            for 一项 in 回合内:#逐个
                项位置=一项.get('location') if isinstance(一项.get('location'),dict) else {}#位置
                项步=项位置.get('step') if isinstance(项位置.get('step'),dict) else {}#步骤
                if 项位置.get('kind')=='step' and 项步.get('step')==目标.get('step'):#同一步
                    步骤内.append(一项)#留下
        根调用=目标.get('rootCallId') if 目标.get('rootCallId') is not None else 目标.get('callId')#根调用
        工具=None#工具节点
        if 根调用 is not None:#有调用
            for 一项 in 可见:#找工具调用
                数据=一项.get('data') if isinstance(一项.get('data'),dict) else {}#节点数据
                根=数据.get('root') if isinstance(数据.get('root'),dict) else {}#根调用对象
                if 一项.get('kind')=='tool-call' and 根.get('callId')==根调用:#同一根调用
                    工具=一项#命中
                    break#停
        精确=None#序号相同
        if 目标.get('anchorSeq') is not None:#有序号
            for 一项 in 步骤内:#在步骤里找
                if 一项.get('anchorSeq')==目标.get('anchorSeq'):#同一序号
                    精确=一项#命中
                    break#停
        种类=None#同种类
        if 目标.get('nodeKind') is not None:#有种类
            for 一项 in 步骤内:#在步骤里找
                if 一项.get('kind')==目标.get('nodeKind'):#同种类
                    种类=一项#命中
                    break#停
        落点=工具 or 精确 or 种类#优先工具和精确
        if 落点 is None and 目标.get('anchorSeq') is not None:#再找最近
            落点=最近节点(步骤内,目标.get('anchorSeq'))#步骤内最近
        if 落点 is None and 目标.get('anchorSeq') is not None:#步骤里没有
            落点=最近节点(回合内,目标.get('anchorSeq'))#回合内最近
        if 落点 is None:#仍然没有
            主=dict(目标)#保持原坐标
        else:#补上节点键
            主=dict(目标)#原坐标优先
            主['nodeKey']=落点.get('key')#落到这个节点
            落位置=落点.get('location') if isinstance(落点.get('location'),dict) else {}#位置
            落回合=落位置.get('turn') if isinstance(落位置.get('turn'),dict) else {}#回合
            if 目标.get('turn') is None and 落位置.get('kind') in ('turn','step'):#请求没写回合
                主['turn']=落回合.get('turn')#用节点回合
    else:#点名节点保留请求坐标，缺的用节点位置补
        主=dict(目标)#请求优先
        if 主.get('anchorSeq') is None and 位置.get('anchorSeq') is not None:#请求没写序号
            主['anchorSeq']=位置.get('anchorSeq')#用节点序号
        if 回合 is not None:#有回合
            主['turn']=回合#写上
        if 步 is not None:#有步骤
            主['step']=步#写上
    if 参考序号 is None:#不知道序号
        return [主]#只有主目标
    def 等级(坐标):
        '同一步骤优先，其次同一回合，再是会话里的其他节点'
        同回合=回合 is None or 坐标.get('turn')==回合#回合相同或没有回合限制
        if 同回合 and 步 is not None and 坐标.get('step')==步:#同一步
            return 0#最近
        if 同回合 and 回合 is not None:#同一回合
            return 1#次近
        return 2#其他
    邻居=[节点坐标(一项) for 一项 in 可见]#可见节点坐标
    def 排序键(坐标):
        '先按步骤、回合、会话分级，再按序号距离'
        return (等级(坐标),abs((坐标.get('anchorSeq') or 0)-参考序号))#等级和距离
    邻居.sort(key=排序键)#等级再按距离
    候选=[主]#主目标在前
    见过=set([坐标键(主)])#已放入的坐标
    for 坐标 in 邻居:#按排好的邻居
        键=坐标键(坐标)#这份坐标
        if 键 in 见过:#重复
            continue#跳过
        见过.add(键)#记下
        候选.append(坐标)#邻居只带节点坐标
    return 候选#主目标加邻居
