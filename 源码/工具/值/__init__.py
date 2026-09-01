"""可重复安装安全的 JSON 与不可变值辅助。"""
import json,math#JSON 与有限数判定
__all__=['断言永不','快照json值','是否json值','深相等json','深冻结']#仅中文公开名

def 断言永不(值,上下文=None):#标记不可达分支
    """标记封闭联合的不可达分支；运行时逃出的值一律抛错。"""
    try:#尽量 JSON 化
        渲染=json.dumps(值,ensure_ascii=False)#JSON 文本
    except Exception:#不可 JSON 化
        渲染=str(值)#退回字符串
    标签=' in '+上下文 if 上下文 is not None else ''#可选上下文
    raise Exception('unreachable variant'+标签+': '+渲染)#与上游文案对齐

def _有朴素数组原型(值):#是否朴素 list
    """是否朴素 list，而不是子类。"""
    return type(值) is list#只要内建 list

def _有朴素对象原型(值):#是否朴素 dict
    """是否朴素 dict。"""
    return type(值) is dict#只要内建 dict

def _可枚举字符串键(值):#收集 JSON 可见键
    """返回每个 JSON 可见对象键，否则拒绝自有但 JSON 会丢的数据。"""
    键们=list(值.keys())#自有键
    for 键 in 键们:#逐键
        if not isinstance(键,str):#非字符串键
            return None#拒绝
    return 键们#可枚举字符串键

def _写入目的(目的,项,状态):#把项写入分离目标
    """把项写入分离目标槽。"""
    if 目的 is None:#无目标
        return#忽略
    if 目的=='root':#根槽
        状态['root']=项#写根
    elif 目的[0]=='array':#数组槽
        目的[1][目的[2]]=项#写下标
    elif 目的[0]=='object':#对象槽
        目的[1][目的[2]]=项#写键

def _遍历json值(值,分离):#迭代校验无损 JSON
    """迭代校验无损 JSON，可选物化分离快照。"""
    祖先=set()#环检测
    状态={'root':None}#分离根容器
    任务=[('visit',值,'root' if 分离 else None)]#任务栈
    while len(任务)>0:#直到栈空
        种类,*其余=任务.pop()#弹出
        if 种类=='leave':#离开对象
            祖先.discard(其余[0])#出祖先集
            continue#下一项
        if 种类=='array-item':#数组项
            源,下标,目标=其余#源数组、下标、目标数组
            if 下标 not in range(len(源)):#稀疏数组
                return None#拒绝
            目的=None if 目标 is None else ('array',目标,下标)#目标槽
            任务.append(('visit',源[下标],目的))#访问元素
            continue#下一项
        if 种类=='object-property':#对象属性
            源,键,目标=其余#源对象、键、目标对象
            目的=None if 目标 is None else ('object',目标,键)#目标槽
            任务.append(('visit',源[键],目的))#访问属性
            continue#下一项
        当前,目的=其余#visit 任务
        if 当前 is None:#null
            _写入目的(目的,None,状态)#写 null
            continue#下一项
        if isinstance(当前,bool):#布尔
            _写入目的(目的,当前,状态)#写布尔
            continue#下一项
        if isinstance(当前,str):#字符串
            _写入目的(目的,当前,状态)#写字符串
            continue#下一项
        if isinstance(当前,(int,float)) and not isinstance(当前,bool):#数字
            if not math.isfinite(当前):#非有限
                return None#拒绝
            if 当前==0.0 and math.copysign(1.0,当前)<0:#负零
                return None#拒绝
            _写入目的(目的,当前,状态)#写数字
            continue#下一项
        if not isinstance(当前,(list,dict)):#其它类型
            return None#拒绝
        if id(当前) in 祖先:#环
            return None#拒绝
        if isinstance(当前,list):#数组
            if not _有朴素数组原型(当前):#非朴素数组
                return None#拒绝
            目标数组=[] if 分离 else None#分离则建新数组
            _写入目的(目的,目标数组,状态)#写数组槽
            祖先.add(id(当前))#入祖先
            任务.append(('leave',id(当前)))#稍后离开
            for 下标 in range(len(当前)-1,-1,-1):#逆序压栈
                任务.append(('array-item',当前,下标,目标数组))#数组项
            continue#下一项
        if not _有朴素对象原型(当前):#非朴素对象
            return None#拒绝
        键们=_可枚举字符串键(当前)#可枚举键
        if 键们 is None:#非法键
            return None#拒绝
        目标对象={} if 分离 else None#分离则建新对象
        _写入目的(目的,目标对象,状态)#写对象槽
        祖先.add(id(当前))#入祖先
        任务.append(('leave',id(当前)))#稍后离开
        for 键 in reversed(键们):#逆序压栈
            任务.append(('object-property',当前,键,目标对象))#对象属性
    if 分离:#要分离
        return 状态['root']#分离根
    return True#仅测试

def 快照json值(值):#校验并分离无损 JSON
    """一次读取每个属性，校验并分离无损 JSON。"""
    return _遍历json值(值,True)#分离快照或 None

def 是否json值(值):#测试是否无损 JSON
    """测试与快照json值相同的无损 JSON 规则，但不分离值。"""
    return _遍历json值(值,False) is True#真为通过

def 深相等json(左,右):#结构比较 JSON 兼容值
    """结构比较 JSON 兼容值。"""
    if 左 is 右:#同一对象
        return True#相等
    if type(左) is not type(右):#类型不同
        return False#不等
    if 左 is None:#null 对 null
        return 右 is None#两边都空
    if isinstance(左,list):#数组
        if len(左)!=len(右):#长度不同
            return False#不等
        return all(深相等json(左[索引],右[索引]) for 索引 in range(len(左)))#逐项
    if isinstance(左,dict):#对象
        if set(左.keys())!=set(右.keys()):#键集不同
            return False#不等
        return all(深相等json(左[键],右[键]) for 键 in 左)#逐键
    return 左==右#原子值

def 深冻结(值):#原地深冻结对象图
    """原地深冻结对象图，同时保留 live AbortSignal 对象可变。"""
    已见=set()#已见对象 id
    待办=[值]#待处理节点
    while len(待办)>0:#直到清空
        节点=待办.pop()#弹出
        if 节点 is None or not isinstance(节点,(list,dict)):#非对象图
            continue#跳过
        if getattr(节点,'__class__',None).__name__=='AbortSignal':#保留 AbortSignal
            continue#不冻结
        标识=id(节点)#对象标识
        if 标识 in 已见:#已处理
            continue#跳过
        已见.add(标识)#记下
        if isinstance(节点,dict):#对象
            for 键 in list(节点.keys()):#自有键
                待办.append(节点[键])#下钻
        if isinstance(节点,list):#数组
            for 项 in 节点:#子项
                待办.append(项)#下钻
    return 值#原值返回
