'已物化 Node、Group、Turn/Step 位置及其 Data 读取器的弱身份索引'

import weakref

__all__=['聊天对象索引']

def 取(值,键,缺省=None):
    '快照或节点字段'
    if 值 is None:
        return 缺省
    if isinstance(值,dict):
        return 值[键] if 键 in 值 else 缺省
    return getattr(值,键,缺省)

class 标识表:
    '能弱引用则不留住对象；其余按身份编号'
    def __init__(自身):
        '弱表和不可弱引用对象的编号表'
        自身._弱=weakref.WeakKeyDictionary()
        自身._号={}

    def 获取(自身,键):
        '按对象身份取值'
        try:
            return 自身._弱[键] if 键 in 自身._弱 else None
        except TypeError:
            return 自身._号.get(id(键))

    def 含有(自身,键):
        '是否已经登记这个身份'
        try:
            return 键 in 自身._弱
        except TypeError:
            return id(键) in 自身._号

    def 设置(自身,键,值):
        '已有身份不覆盖'
        try:
            if 键 not in 自身._弱:
                自身._弱[键]=值
        except TypeError:
            编号=id(键)
            if 编号 not in 自身._号:
                自身._号[编号]=值

class 已索引集:
    '每个不可变发布只索引一次'
    def __init__(自身):
        '弱集合和编号集合'
        自身._弱=weakref.WeakSet()
        自身._号=set()

    def 首次(自身,对象):
        '第一次见到返回真并记下'
        try:
            if 对象 in 自身._弱:
                return False
            自身._弱.add(对象)
            return True
        except TypeError:
            编号=id(对象)
            if 编号 in 自身._号:
                return False
            自身._号.add(编号)
            return True

class 聊天对象索引:
    '每次只索引一份不可变发布，不留住它的对象或节点数组'
    def __init__(自身,绑定):
        '绑定是会话拥有的 Conversation 读取器'
        自身._绑定=绑定
        自身._身份=标识表()
        自身._已索引=已索引集()

    def 引用(自身,值):
        '解析原对象身份，不留住已被替换的发布'
        自身._刷新()
        return 自身._身份.获取(值)

    def _聊天(自身):
        '当前 chat 视图快照'
        快照=自身._绑定.snapshot.getSnapshot()
        视图=取(快照,'views')
        if 视图 is None:
            return None
        return 视图.get('chat')

    def _登记(自身,值,引用):
        '非空对象且尚未登记时写入'
        if 值 is not None and not isinstance(值,(str,int,float,bool)) and not 自身._身份.含有(值):
            自身._身份.设置(值,引用)

    def _位置(自身,值,步=None):
        '登记 Turn 或 Step 及其 data'
        回合=取(取(值,'turn'),'turn')
        身份=str(回合) if 步 is None else f'{回合}/{步}'
        种类='turn' if 步 is None else 'step'
        def 读取():
            '当前已加载的位置'
            聊天=自身._聊天()
            时间线=取(聊天,'timeline')
            回合表=取(时间线,'turns')
            当前=None if 回合表 is None else 回合表.get(回合)
            if 步 is None:
                return 当前
            if 当前 is None:
                return None
            for 项 in 取(当前,'steps') or []:
                if 取(项,'step')==步:
                    return 项
            return None
        聊天=自身._聊天()
        位置索引=取(聊天,'locations')
        if 步 is None:
            列表=位置索引.getTurn(回合) if 位置索引 is not None else []
        else:
            列表=位置索引.getStep(回合,步) if 位置索引 is not None else []
        首个=列表[0] if 列表 is not None and len(列表)>0 else None
        目标={'turn':回合}
        if 首个 is not None:
            目标['nodeKey']=首个
        自身._登记(值,{'id':f'{种类}:{身份}','kind':种类,'identity':身份,'target':目标,'read':读取})
        数据种类='turnData' if 步 is None else 'stepData'
        自身._登记(取(值,'data'),{'id':f'{种类}-data:{身份}','kind':数据种类,'identity':身份,'target':目标,'read':lambda:取(读取(),'data')})

    def _刷新(自身):
        '把当前节点、时间线和分组补进身份表'
        聊天=自身._聊天()
        if 聊天 is None:
            return
        节点存储=取(聊天,'nodes')
        节点表=节点存储.values() if 节点存储 is not None else []
        if 自身._已索引.首次(节点表):
            for 节点 in 节点表:
                键=取(节点,'key')
                位置=取(节点,'location') or {}
                种类=取(位置,'kind')
                回合=取(取(位置,'turn'),'turn') if 种类 in ('turn','step') else None
                目标={'nodeKey':键}
                if 回合 is not None:
                    目标['turn']=回合
                def 读节点(键=键):
                    '当前节点'
                    当前=自身._聊天()
                    存储=取(当前,'nodes')
                    return None if 存储 is None else 存储.get(键)
                自身._登记(节点,{'id':f'node:{键}','kind':'node','identity':键,'target':目标,'read':读节点})
                自身._登记(取(节点,'data'),{'id':f'node-data:{键}','kind':'nodeData','identity':键,'target':目标,'read':lambda 键=键:取(读节点(键),'data')})
        时间线=取(聊天,'timeline')
        if 时间线 is not None and 自身._已索引.首次(时间线):
            回合表=取(时间线,'turns')
            for 回合 in (回合表.values() if 回合表 is not None else []):
                自身._位置(回合)
                for 步 in 取(回合,'steps') or []:
                    自身._位置(步,取(步,'step'))
        快照=自身._绑定.snapshot.getSnapshot()
        视图=取(快照,'views')
        分组=None if 视图 is None else 视图.grouped('chat')
        for 条目 in (取(分组,'entries') or []):
            if 取(条目,'kind')!='group':
                continue
            键=取(条目,'key')
            组=分组.groupSource(键).getSnapshot()
            if 组 is None or not 自身._已索引.首次(组):
                continue
            目标={'groupKey':键}
            def 读组(键=键):
                '当前分组快照'
                当前快照=自身._绑定.snapshot.getSnapshot()
                当前视图=取(当前快照,'views')
                当前分组=None if 当前视图 is None else 当前视图.grouped('chat')
                if 当前分组 is None:
                    return None
                return 当前分组.groupSource(键).getSnapshot()
            自身._登记(组,{'id':f'group:{键}','kind':'group','identity':键,'target':目标,'read':读组})
            自身._登记(取(组,'data'),{'id':f'group-data:{键}','kind':'groupData','identity':键,'target':目标,'read':lambda 键=键:取(读组(键),'data')})
            for 成员 in 取(组,'members') or []:
                节点键=取(成员,'key')
                成员目标={'nodeKey':节点键}
                if 取(成员,'groupPart') is not None:
                    成员目标['groupPart']=取(成员,'groupPart')
                def 读成员(节点键=节点键):
                    '成员对应的当前节点'
                    当前=自身._聊天()
                    存储=取(当前,'nodes')
                    return None if 存储 is None else 存储.get(节点键)
                自身._登记(成员,{'id':f'node:{节点键}','kind':'node','identity':节点键,'target':成员目标,'read':读成员})
