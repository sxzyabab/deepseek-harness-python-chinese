__all__=['当前浏览器目标','浏览器地址检查点']

def 当前浏览器目标(状态):
    """读已选地址。"""
    if 状态 is None or 状态['index']<0:
        return None
    return 状态['entries'][状态['index']]

def 浏览器地址检查点(目标,修订):
    """只记下可序列化地址，不序列化原生历史。"""
    return {
        'entries':[目标],
        'index':0,
        'request':{'target':目标,'revision':修订},
        'navigation':{'status':'known','revision':修订},
        'failure':None,
    }
