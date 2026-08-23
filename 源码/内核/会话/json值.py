"""可持久化会话数据的无损 JSON 校验与脱离快照。对齐上游 `session/src/json.ts`。公开面仅中文名。"""
import math#数学
from ..llm.调用配置 import 深冻结,冻结映射,冻结列表#导入深冻结与冻结形态

__all__=['冻结记录','冻结树','快照json值','是否json值']#仅中文公开名

class 冻结记录(冻结映射):#可点号读取的冻结映射
    """冻结映射并允许点号读取字段。"""
    def __getattr__(自身,名):#按字段名读取
        """按字段名读取，缺席则属性错误。"""
        if 名 in 自身:#有该键
            return 自身[名]#有该键
        raise AttributeError(名)#没有该键

def 是否负零(值):#IEEE 负零
    """值为 IEEE 负零时为真。"""
    return isinstance(值,float) and 值==0.0 and math.copysign(1.0,值)<0#符号为负的零

def 冻结树(值):#迭代深冻结并升级记录
    """深冻结后把冻结映射升级为可点号读取的冻结记录。"""
    深冻结(值)#就地深冻结
    待处理=[值]#待访问栈
    while len(待处理)>0:#还有对象
        当前=待处理.pop()#弹出一个
        if isinstance(当前,dict):#映射
            if type(当前) is 冻结映射:#尚未升级
                当前.__class__=冻结记录#升级为可点号记录
            for 子 in list(当前.values()):#逐个自有值
                if isinstance(子,(dict,list)):#对象则入栈
                    待处理.append(子)#对象则入栈
        elif isinstance(当前,list):#列表
            for 子 in 当前:#逐个元素
                if isinstance(子,(dict,list)):#对象则入栈
                    待处理.append(子)#对象则入栈
    return 值#已冻结根

def 是否普通数组(值):#普通列表或其冻结形态
    """数组是否为普通列表或其冻结形态，拒绝子类。"""
    return type(值) is list or type(值) is 冻结列表#恰好列表或冻结列表

def 是否普通对象(值):#普通字典或其冻结形态
    """对象是否为普通字典或其冻结形态，拒绝子类。"""
    return type(值) is dict or type(值) is 冻结映射 or type(值) is 冻结记录#恰好字典或冻结记录

def 可枚举字符串键(值):#JSON 可见键
    """返回每个 JSON 可见的对象键，或拒绝 JSON 会丢掉的自有数据。"""
    键列表=list(值.keys())#全部自有键
    for 键 in 键列表:#逐个键
        if not isinstance(键,str):#非字符串键
            return None#有非字符串键则拒
    return 键列表#全是可枚举字符串键

def 写入快照槽(目标,项,根盒):#写入快照槽
    """把一项写入快照槽或根。"""
    if 目标 is None:#不物化
        return#不物化则跳过
    种类=目标['kind']#槽种类
    if 种类=='root':#写根
        根盒[0]=项#记下根
    elif 种类=='array':#写数组槽
        目标['target'][目标['index']]=项#放入下标
    else:#写对象槽
        目标['target'][目标['key']]=项#按键写入

def 遍历json值(值,脱离):#迭代校验无损 JSON
    """迭代校验无损 JSON，可选物化一份脱离快照。"""
    祖先=set()#当前祖先栈
    根盒=[None]#脱离根
    任务列表=[{'kind':'visit','value':值}]#待办栈，先访问根
    if 脱离:#物化
        任务列表[0]['destination']={'kind':'root'}#物化则写根
    任务=任务列表.pop() if 任务列表 else None#弹出任务
    while 任务 is not None:#弹出任务直到空
        if 任务['kind']=='leave':#离开祖先
            祖先.discard(id(任务['source']))#弹出祖先
            任务=任务列表.pop() if 任务列表 else None#下一任务
            continue#下一任务
        if 任务['kind']=='array-item':#安排数组元素
            源=任务['source']#数组
            下标=任务['index']#下标
            if 下标>=len(源):#稀疏下标
                return None#稀疏下标拒
            下一={'kind':'visit','value':源[下标]}#改为访问该元素
            if 任务.get('target') is not None:#物化
                下一['destination']={'kind':'array','target':任务['target'],'index':下标}#物化则写该槽
            任务列表.append(下一)#压栈
            任务=任务列表.pop() if 任务列表 else None#下一任务
            continue#下一任务
        if 任务['kind']=='object-property':#安排对象属性
            源=任务['source']#对象
            键=任务['key']#键
            下一={'kind':'visit','value':源[键]}#改为访问该属性
            if 任务.get('target') is not None:#物化
                下一['destination']={'kind':'object','target':任务['target'],'key':键}#物化则写该槽
            任务列表.append(下一)#压栈
            任务=任务列表.pop() if 任务列表 else None#下一任务
            continue#下一任务
        当前=任务['value']#当前候选
        去向=任务.get('destination')#快照槽
        if 当前 is None:#null
            写入快照槽(去向,None,根盒)#写入 null
            任务=任务列表.pop() if 任务列表 else None#下一任务
            continue#下一任务
        if isinstance(当前,bool) or isinstance(当前,str):#布尔或字符串
            写入快照槽(去向,当前,根盒)#原样写入
            任务=任务列表.pop() if 任务列表 else None#下一任务
            continue#下一任务
        if isinstance(当前,(int,float)) and not isinstance(当前,bool):#数字
            if isinstance(当前,float) and (not math.isfinite(当前) or 是否负零(当前)):#非有限或负零
                return None#非有限或负零拒
            写入快照槽(去向,当前,根盒)#写入数字
            任务=任务列表.pop() if 任务列表 else None#下一任务
            continue#下一任务
        if not isinstance(当前,(dict,list)):#其余原始类型
            return None#其余原始类型拒
        身份=id(当前)#对象身份
        if 身份 in 祖先:#环
            return None#环拒
        if 是否普通数组(当前):#数组
            额外=getattr(当前,'__dict__',None)#列表额外自有属性
            if 额外 is not None and len(额外)>0:#JSON 会丢掉的额外键
                return None#额外自有键拒
            长度=len(当前)#长度
            目标=None#物化数组
            if 脱离:#物化
                目标=[]#物化则建空数组
                写入快照槽(去向,目标,根盒)#先挂上数组
            祖先.add(身份)#压入祖先
            任务列表.append({'kind':'leave','source':当前})#稍后离开
            下标=长度-1#倒序压元素以保持正序访问
            while 下标>=0:#倒序压元素
                项={'kind':'array-item','source':当前,'index':下标}#安排元素
                if 目标 is not None:#物化
                    项['target']=目标#物化槽
                任务列表.append(项)#压栈
                下标-=1#前一元素
            任务=任务列表.pop() if 任务列表 else None#下一任务
            continue#下一任务
        if not 是否普通对象(当前):#非普通对象
            return None#非普通对象拒
        键列表=可枚举字符串键(当前)#取出可见键
        if 键列表 is None:#有 JSON 会丢掉的键
            return None#有 JSON 会丢掉的键则拒
        目标=None#物化对象
        if 脱离:#物化
            目标={}#物化则建空对象
            写入快照槽(去向,目标,根盒)#先挂上对象
        祖先.add(身份)#压入祖先
        任务列表.append({'kind':'leave','source':当前})#稍后离开
        下标=len(键列表)-1#倒序压属性以保持正序访问
        while 下标>=0:#倒序压属性
            键=键列表[下标]#当前键
            if 键 is None:#下标越界
                return None#下标越界防护
            项={'kind':'object-property','source':当前,'key':键}#安排属性
            if 目标 is not None:#物化
                项['target']=目标#物化槽
            任务列表.append(项)#压栈
            下标-=1#前一键
        任务=任务列表.pop() if 任务列表 else None#下一任务
    if 脱离:#物化
        return 根盒[0]#物化返回根
    return True#校验通过

def 快照json值(值):#脱离快照
    """校验并脱离无损 JSON，每个属性只读一次。"""
    return 遍历json值(值,True)#物化遍历

def 是否json值(值):#是否无损 JSON
    """测试与快照json值相同的无损 JSON 边界，但不脱离。"""
    return 遍历json值(值,False) is True#只校验
