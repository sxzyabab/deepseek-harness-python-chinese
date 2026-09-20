import json,math,weakref
__all__=['断言永不','快照json值','是否json值','深相等json','深冻结','带值弱映射','值错误']

class 值错误(Exception):
    """值辅助失败。"""
    def __init__(自身,消息):
        super().__init__(消息)

def 断言永不(值,上下文=None):
    """标记封闭联合的不可达分支；运行时逃出的值一律抛错。"""
    try:
        渲染=json.dumps(值,ensure_ascii=False,separators=(',',':'),allow_nan=False)
    except (TypeError,ValueError):
        渲染=str(值)
    标签=' in '+上下文 if 上下文 is not None else ''
    raise 值错误('不可达变体'+标签+': '+渲染)

def _有朴素数组原型(值):
    """是否朴素 list，而不是子类。"""
    return type(值) is list#只要内建 list

def _有朴素对象原型(值):
    """是否朴素 dict。"""
    return type(值) is dict#只要内建 dict

def _可枚举字符串键(值):
    """返回每个 JSON 可见对象键，否则拒绝自有但 JSON 会丢的数据。"""
    键列表=list(值.keys())
    for 键 in 键列表:
        if not isinstance(键,str):
            return None
    return 键列表

def _写入目的(目的,项,状态):
    """把项写入分离目标槽。"""
    if 目的 is None:
        return
    if 目的=='root':
        状态['root']=项
    elif 目的[0]=='array':
        目的[1][目的[2]]=项
    elif 目的[0]=='object':
        目的[1][目的[2]]=项

def _遍历json值(值,分离):
    """迭代校验无损 JSON，可选物化分离快照。"""
    祖先=set()
    状态={'root':None}
    任务=[('visit',值,'root' if 分离 else None)]
    while len(任务)>0:
        种类,*其余=任务.pop()
        if 种类=='leave':
            祖先.discard(其余[0])
            continue
        if 种类=='array-item':
            源,下标,目标=其余
            if 下标 not in range(len(源)):
                return None#稀疏数组
            目的=None if 目标 is None else ('array',目标,下标)
            任务.append(('visit',源[下标],目的))
            continue
        if 种类=='object-property':
            源,键,目标=其余
            目的=None if 目标 is None else ('object',目标,键)
            任务.append(('visit',源[键],目的))
            continue
        当前,目的=其余
        if 当前 is None:
            _写入目的(目的,None,状态)
            continue
        if isinstance(当前,bool):
            _写入目的(目的,当前,状态)
            continue
        if isinstance(当前,str):
            _写入目的(目的,当前,状态)
            continue
        if isinstance(当前,(int,float)) and not isinstance(当前,bool):
            if not math.isfinite(当前):
                return None#非有限
            if 当前==0.0 and math.copysign(1.0,当前)<0:
                return None#负零
            _写入目的(目的,当前,状态)
            continue
        if not isinstance(当前,(list,dict)):
            return None
        if id(当前) in 祖先:
            return None#环
        if isinstance(当前,list):
            if not _有朴素数组原型(当前):
                return None
            目标数组=[] if 分离 else None
            _写入目的(目的,目标数组,状态)
            祖先.add(id(当前))
            任务.append(('leave',id(当前)))
            for 下标 in range(len(当前)-1,-1,-1):
                任务.append(('array-item',当前,下标,目标数组))
            continue
        if not _有朴素对象原型(当前):
            return None
        键列表=_可枚举字符串键(当前)
        if 键列表 is None:
            return None
        目标对象={} if 分离 else None
        _写入目的(目的,目标对象,状态)
        祖先.add(id(当前))
        任务.append(('leave',id(当前)))
        for 键 in reversed(键列表):
            任务.append(('object-property',当前,键,目标对象))
    if 分离:
        return 状态['root']
    return True

def 快照json值(值):
    """一次读取每个属性，校验并分离无损 JSON。"""
    return _遍历json值(值,True)

def 是否json值(值):
    """测试与快照json值相同的无损 JSON 规则，但不分离值。"""
    return _遍历json值(值,False) is True

def 深相等json(左,右):
    """结构比较 JSON 兼容值。"""
    if 左 is 右:
        return True
    if type(左) is not type(右):
        return False
    if 左 is None:
        return 右 is None
    if isinstance(左,list):
        if len(左)!=len(右):
            return False
        return all(深相等json(左[索引],右[索引]) for 索引 in range(len(左)))
    if isinstance(左,dict):
        if set(左.keys())!=set(右.keys()):
            return False
        return all(深相等json(左[键],右[键]) for 键 in 左)
    return 左==右

def 深冻结(值):
    """原地深冻结对象图，同时保留 live AbortSignal 对象可变。"""
    已见=set()
    待办=[值]
    while len(待办)>0:
        节点=待办.pop()
        if 节点 is None or not isinstance(节点,(list,dict)):
            continue
        if getattr(节点,'__class__',None).__name__=='中止信号':
            continue#保留本包中止信号可变
        标识=id(节点)
        if 标识 in 已见:
            continue
        已见.add(标识)
        if isinstance(节点,dict):
            for 键 in list(节点.keys()):
                待办.append(节点[键])
        if isinstance(节点,list):
            for 项 in 节点:
                待办.append(项)
    return 值

class 带值弱映射:
    """弱键查找，并强保留关联值的可迭代集合。每个值只能属于一个键；不做自动清理。"""
    def __init__(自身):
        """构造空弱映射。"""
        自身._键表=weakref.WeakKeyDictionary()
        自身._值集=[]

    @property
    def values(自身):
        """按插入顺序的活强保留值。"""
        return tuple(自身._值集)

    def get(自身,键):
        """读键关联的值；缺席为 None。"""
        return 自身._键表.get(键)

    def has(自身,键):
        """键是否有关联。"""
        return 键 in 自身._键表

    def set(自身,键,值):
        """把一个键与一个调用方唯一值关联。"""
        if 键 in 自身._键表:
            旧值=自身._键表[键]
            if 旧值 is 值:
                return 自身
            if 旧值 in 自身._值集:
                自身._值集.remove(旧值)
        自身._键表[键]=值
        自身._值集.append(值)
        return 自身

    def delete(自身,键):
        """移除一个关联及其强保留值。"""
        if 键 not in 自身._键表:
            return False
        值=自身._键表.pop(键)
        if 值 in 自身._值集:
            自身._值集.remove(值)
        return True

    def clear(自身):
        """移除每个关联与强保留值。"""
        自身._键表=weakref.WeakKeyDictionary()
        自身._值集.clear()
