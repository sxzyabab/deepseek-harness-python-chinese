__all__=['节点引用','组引用','组快照','节点变更','组节点位置']

def 节点引用(键,组分=None):
    """整节点或渲染器拥有的节点局部。"""
    项={'kind':'node','key':键}
    if 组分 is not None:
        项['groupPart']=组分
    return 项

def 组引用(键):
    """根列表对独立观察分组的引用。"""
    return {'kind':'group','key':键}

def 组快照(键,数据,成员列表):
    """不可变分组数据及其有序、非嵌套节点引用。"""
    return {'key':键,'data':数据,'members':成员列表}

def 节点变更(当前,先前=None):
    """一次更新前后目标已处理的节点值。"""
    return {'previous':先前,'current':当前}

def 组节点位置(回合,先前,其后):
    """所属回合及目标可见节点序中的紧邻。"""
    return {'turn':回合,'previous':先前,'next':其后}
