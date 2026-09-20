import math
from ...模型后端.llm.调用配置 import 深冻结,冻结映射,冻结列表

__all__=['冻结记录','冻结树','快照json值','是否json值']

class 冻结记录(冻结映射):
    """冻结映射并允许点号读取字段。"""
    def __getattr__(自身,名):
        """按字段名读取，缺席则属性错误。"""
        if 名 in 自身:
            return 自身[名]
        raise AttributeError(名)

def 是否负零(值):
    """值为 IEEE 负零时为真。"""
    return isinstance(值,float) and 值==0.0 and math.copysign(1.0,值)<0

def 冻结树(值):
    """深冻结后把冻结映射升级为可点号读取的冻结记录。"""
    深冻结(值)
    待处理=[值]
    while len(待处理)>0:
        当前=待处理.pop()
        if isinstance(当前,dict):
            if type(当前) is 冻结映射:
                当前.__class__=冻结记录
            for 子 in list(当前.values()):
                if isinstance(子,(dict,list)):
                    待处理.append(子)
        elif isinstance(当前,list):
            for 子 in 当前:
                if isinstance(子,(dict,list)):
                    待处理.append(子)
    return 值

def 是否普通数组(值):
    """数组是否为普通列表或其冻结形态，拒绝子类。"""
    return type(值) is list or type(值) is 冻结列表

def 是否普通对象(值):
    """对象是否为普通字典或其冻结形态，拒绝子类。"""
    return type(值) is dict or type(值) is 冻结映射 or type(值) is 冻结记录

def 可枚举字符串键(值):
    """返回每个 JSON 可见的对象键，或拒绝 JSON 会丢掉的自有数据。"""
    键列表=list(值.keys())
    for 键 in 键列表:
        if not isinstance(键,str):
            return None
    return 键列表

def 写入快照槽(目标,项,根盒):
    """把一项写入快照槽或根。"""
    if 目标 is None:
        return
    种类=目标['kind']
    if 种类=='root':
        根盒[0]=项
    elif 种类=='array':
        目标['target'][目标['index']]=项
    else:
        目标['target'][目标['key']]=项

def 遍历json值(值,脱离):
    """迭代校验无损 JSON，可选物化一份脱离快照。"""
    祖先=set()
    根盒=[None]
    任务列表=[{'kind':'visit','value':值}]
    if 脱离:
        任务列表[0]['destination']={'kind':'root'}
    任务=任务列表.pop() if 任务列表 else None
    while 任务 is not None:
        if 任务['kind']=='leave':
            祖先.discard(id(任务['source']))
            任务=任务列表.pop() if 任务列表 else None
            continue
        if 任务['kind']=='array-item':
            源=任务['source']
            下标=任务['index']
            if 下标>=len(源):
                return None#稀疏下标
            下一={'kind':'visit','value':源[下标]}
            if 任务.get('target') is not None:
                下一['destination']={'kind':'array','target':任务['target'],'index':下标}
            任务列表.append(下一)
            任务=任务列表.pop() if 任务列表 else None
            continue
        if 任务['kind']=='object-property':
            源=任务['source']
            键=任务['key']
            下一={'kind':'visit','value':源[键]}
            if 任务.get('target') is not None:
                下一['destination']={'kind':'object','target':任务['target'],'key':键}
            任务列表.append(下一)
            任务=任务列表.pop() if 任务列表 else None
            continue
        当前=任务['value']
        去向=任务.get('destination')
        if 当前 is None:
            写入快照槽(去向,None,根盒)
            任务=任务列表.pop() if 任务列表 else None
            continue
        if isinstance(当前,bool) or isinstance(当前,str):
            写入快照槽(去向,当前,根盒)
            任务=任务列表.pop() if 任务列表 else None
            continue
        if isinstance(当前,(int,float)) and not isinstance(当前,bool):
            if isinstance(当前,float) and (not math.isfinite(当前) or 是否负零(当前)):
                return None#非有限或负零
            写入快照槽(去向,当前,根盒)
            任务=任务列表.pop() if 任务列表 else None
            continue
        if not isinstance(当前,(dict,list)):
            return None
        身份=id(当前)
        if 身份 in 祖先:
            return None#环
        if 是否普通数组(当前):
            额外=getattr(当前,'__dict__',None)
            if 额外 is not None and len(额外)>0:
                return None#JSON 会丢掉的额外键
            长度=len(当前)
            目标=None
            if 脱离:
                目标=[]
                写入快照槽(去向,目标,根盒)
            祖先.add(身份)
            任务列表.append({'kind':'leave','source':当前})
            下标=长度-1#倒序压元素以保持正序访问
            while 下标>=0:
                项={'kind':'array-item','source':当前,'index':下标}
                if 目标 is not None:
                    项['target']=目标
                任务列表.append(项)
                下标-=1
            任务=任务列表.pop() if 任务列表 else None
            continue
        if not 是否普通对象(当前):
            return None
        键列表=可枚举字符串键(当前)
        if 键列表 is None:
            return None
        目标=None
        if 脱离:
            目标={}
            写入快照槽(去向,目标,根盒)
        祖先.add(身份)
        任务列表.append({'kind':'leave','source':当前})
        下标=len(键列表)-1#倒序压属性以保持正序访问
        while 下标>=0:
            键=键列表[下标]
            if 键 is None:
                return None
            项={'kind':'object-property','source':当前,'key':键}
            if 目标 is not None:
                项['target']=目标
            任务列表.append(项)
            下标-=1
        任务=任务列表.pop() if 任务列表 else None
    if 脱离:
        return 根盒[0]
    return True

def 快照json值(值):
    """校验并脱离无损 JSON，每个属性只读一次。"""
    return 遍历json值(值,True)

def 是否json值(值):
    """测试与快照json值相同的无损 JSON 边界，但不脱离。"""
    return 遍历json值(值,False) is True
