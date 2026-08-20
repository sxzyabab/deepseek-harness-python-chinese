"""会话事件日志之上的表面层：产出 LLM 消息的事件的有序视图。对齐上游 `session/src/surface.ts`。公开面仅中文名。"""
from .类型 import 是否安全整数,表面事件类型 as 表面事件类型元组#导入安全整数与表面类型词表

__all__=[#仅中文公开名
    '是否可进表面类型','是否表面事件','是否追加表面事件','是否替换表面事件',
    '事件派生消息','折叠表面','表面管理器',
]#公开面结束

表面事件类型=frozenset(表面事件类型元组)#产出消息的事件类型集合

def 取字段(对象,键):#读取字段
    """读取映射或对象上的字段。"""
    if isinstance(对象,dict):#映射
        return 对象[键]#映射键
    return getattr(对象,键)#对象属性

def 试取(对象,键):#读取可选字段
    """读取可选字段，缺席为 None。"""
    if 对象 is None:#无对象
        return None#缺席
    if isinstance(对象,dict):#映射
        return 对象.get(键)#映射键
    return getattr(对象,键,None)#对象属性

def 有自有(对象,键):#是否拥有自有键
    """对象是否拥有该自有键。"""
    if isinstance(对象,dict):#字典
        return 键 in 对象#字典键
    字典=getattr(对象,'__dict__',None)#实例字典
    if 字典 is None:#没有字典
        return False#没有字典
    return 键 in 字典#自有

def 是否可进表面类型(类型):#类型是否可进表面
    """某事件类型能否加入模型可见表面（对齐类型.表面事件类型）。"""
    return 类型 in 表面事件类型#查集合

def 是否表面事件(事件):#是否表面事件
    """把事件收窄为带必需标记的可进表面事件。"""
    if 试取(事件,'type') not in 表面事件类型:#类型不对
        return False#类型不对
    return 有自有(事件,'surfaceOp')#必须有表面操作

def 是否追加表面事件(事件):#是否追加表面事件
    """把事件收窄为追加源表面事件。"""
    return 是否表面事件(事件) and 试取(事件,'surfaceOp')=='append'#表面且操作为追加

def 是否替换表面事件(事件):#是否替换表面事件
    """把事件收窄为表面替换。"""
    return 是否表面事件(事件) and 试取(事件,'surfaceOp')!='append'#表面且不是追加

def 事件派生消息(事件):#事件派生消息
    """把单条事件投影成它派生出的 LLM 消息；不产出消息则为 None。"""
    类型=试取(事件,'type')#事件类型
    if 类型=='user/message':#用户消息
        return 取字段(事件,'data')#载荷即消息
    if 类型=='assistant/message':#助手消息
        消息=取字段(取字段(事件,'data'),'message')#取出消息
        if len(取字段(消息,'content'))==0:#空内容
            return None#空内容不进历史
        return 消息#取出消息
    if 类型=='tool/result':#工具结果
        return 取字段(取字段(事件,'data'),'message')#取出消息
    return None#非表面事件无消息

def 创建折叠状态():#空折叠状态
    """创建空的表面折叠状态。"""
    return {'nodes':[],'replaceGeneration':0}#空节点与零代数

def 是否事件序号(值):#是否事件序号
    """运行时值是否为非负安全事件序号。"""
    return 是否安全整数(值) and 值>=0#数字、安全整数、非负

def 是否替换操作(值):#是否替换操作
    """运行时值是否正好是位置替换形态。"""
    if not isinstance(值,dict):#必须是记录
        return False#必须是记录
    if len(值)!=3:#恰好三键
        return False#恰好三键
    if 'op' not in 值 or 'start' not in 值 or 'end' not in 值:#必须有这三键
        return False#必须有这三键
    if 值['op']!='replace':#必须是 replace
        return False#必须是 replace
    return 是否事件序号(值['start']) and 是否事件序号(值['end'])#起止序号合法

def 取出表面操作(事件):#取出表面操作
    """校验事件本地的表面资格并返回其操作。"""
    类型=试取(事件,'type')#事件类型
    if not 是否可进表面类型(类型):#类型不可进表面
        if 有自有(事件,'surfaceOp'):#却带了表面操作
            raise Exception('session event "'+str(类型)+'" is not surface-eligible and cannot carry surfaceOp')#非法携带
        if 有自有(事件,'sourceEventSeqs'):#却带了源序号
            raise Exception('session event "'+str(类型)+'" is not surface-eligible and cannot carry sourceEventSeqs')#非法携带
        return None#非表面事件
    if not 有自有(事件,'surfaceOp'):#可进表面却没有标记
        raise Exception('session event "'+str(类型)+'" is surface-eligible and requires a surfaceOp marker')#缺少标记
    操作=取字段(事件,'surfaceOp')#取出操作
    if 操作=='append':#追加
        return 操作#追加
    if 操作 is None or isinstance(操作,(str,bytes,int,float,bool,list)):#不是对象
        raise Exception('session event "'+str(类型)+'" carries an invalid surfaceOp')#非法操作
    if not isinstance(操作,dict):#不是记录
        raise Exception('session event "'+str(类型)+'" carries an invalid surfaceOp')#非法操作
    if not 是否替换操作(操作):#不是合法替换
        raise Exception('session event "'+str(类型)+'" carries an invalid replace surfaceOp')#非法替换
    return 操作#合法替换

def 断言出处(事件,被遮蔽序号):#校验出处
    """按先前日志条目与替换区间校验引用的源事件序号。"""
    原始=取字段(事件,'sourceEventSeqs') if 有自有(事件,'sourceEventSeqs') else None#原始源序号
    已见=set()#已见源
    if 原始 is not None:#有出处字段
        if not isinstance(原始,list):#不是数组
            raise Exception('sourceEventSeqs on event at seq '+str(试取(事件,'seq'))+' must be an array when present')#必须是数组
        if len(原始)==0 and 试取(事件,'type')!='assistant/message':#空数组且不是助手消息
            raise Exception('sourceEventSeqs must not be empty except on assistant/message')#除助手消息外不得空
        不早源=None#不早于当前的源
        for 源 in 原始:#逐个源
            if not 是否事件序号(源):#不是合法序号
                raise Exception('session event "'+str(试取(事件,'type'))+'" sourceEventSeqs must densely contain non-negative safe integers')#必须是稠密非负安全整数
            已见.add(源)#记下
            if 不早源 is None and 源>=取字段(事件,'seq'):#找到不早于当前的
                不早源=源#找到不早于当前的
        if len(已见)!=len(原始):#有重复
            raise Exception('sourceEventSeqs must not contain duplicates')#不得重复
        if 不早源 is not None:#引用了不更早的事件
            raise Exception('sourceEventSeqs must reference earlier events: '+str(不早源)+' >= current seq '+str(取字段(事件,'seq')))#必须引用更早事件
    缺=[]#被遮蔽却未引用
    for 序号 in 被遮蔽序号:#被遮蔽序号
        if 序号 not in 已见:#未引用
            缺.append(序号)#记下缺失
    if len(缺)>0:#缺引用
        缺文=', '.join(str(项) for 项 in 缺)#拼缺失
        raise Exception('surface replace: sourceEventSeqs must include every shadowed surface node; missing '+缺文)#必须覆盖每个被遮蔽节点

def 替换区间(状态,操作):#定位替换区间
    """定位一段替换区间，不改当前折叠状态。"""
    节点们=状态['nodes']#当前表面节点
    try:#查起点
        起点下标=节点们.index(操作['start'])#起点下标
    except ValueError:#表面里没有起点
        raise Exception('surface replace: start seq '+str(操作['start'])+' not found in surface')#起点不在表面
    try:#查终点
        终点下标=节点们.index(操作['end'])#终点下标
    except ValueError:#表面里没有终点
        raise Exception('surface replace: end seq '+str(操作['end'])+' not found in surface')#终点不在表面
    if 起点下标>终点下标:#起点在终点之后
        raise Exception(
            'surface replace: start seq '+str(操作['start'])+' (index '+str(起点下标)+') is after end seq '+str(操作['end'])+' (index '+str(终点下标)+')'
        )#区间颠倒
    return {#区间
        'startIdx':起点下标,#起点下标
        'endIdx':终点下标,#终点下标
        'shadowedSeqs':节点们[起点下标:终点下标+1],#含端切片
    }#区间

def json深相等(甲,乙):#JSON 深相等
    """会话事件 JSON 值域上的深结构相等。"""
    if 甲 is 乙:#同一引用
        return True#同一引用
    if isinstance(甲,bool) or isinstance(乙,bool):#至少一方是布尔
        return 甲 is 乙#布尔必须同一
    if isinstance(甲,(int,float)) and isinstance(乙,(int,float)) and not isinstance(甲,bool) and not isinstance(乙,bool):#双方数字
        return 甲==乙#JSON 数字相等
    if isinstance(甲,str) and isinstance(乙,str):#双方字符串
        return 甲==乙#字符串相等
    if 甲 is None or 乙 is None:#至少一方 null
        return 甲 is 乙#仅双方都是 null
    if isinstance(甲,list) or isinstance(乙,list):#至少一方是数组
        if not isinstance(甲,list) or not isinstance(乙,list) or len(甲)!=len(乙):#双方都须是等长数组
            return False#双方都须是等长数组
        下标=0#逐项
        while 下标<len(甲):#逐项递归
            if not json深相等(甲[下标],乙[下标]):#项不等
                return False#项不等
            下标+=1#下一项
        return True#逐项都等
    if not isinstance(甲,dict) or not isinstance(乙,dict):#非双方对象
        return False#非双方对象
    甲键=list(甲.keys())#甲方键
    if len(甲键)!=len(乙):#键数不同
        return False#键数不同
    for 键 in 甲键:#逐键
        if 键 not in 乙:#缺键
            return False#缺键
        if not json深相等(甲[键],乙[键]):#值不等
            return False#值不等
    return True#逐键都等

def 断言工具结果改写(事件,被遮蔽序号,事件们,基序号):#校验工具结果改写
    """把工具结果替换限制为只改当前一条结果的内容。"""
    if 试取(事件,'type')!='tool/result':#非工具结果
        return#非工具结果放过
    if len(被遮蔽序号)!=1:#不是恰好一个节点
        raise Exception('tool/result surface replacement must rewrite exactly one current node')#必须只改一个
    for 原序号 in 被遮蔽序号:#被遮蔽的原事件
        窗口下标=原序号-基序号#窗口下标
        原事件=事件们[窗口下标] if 0<=窗口下标<len(事件们) else None#窗口内原事件
        if 原事件 is None or 试取(原事件,'type')!='tool/result':#目标不是当前工具结果
            raise Exception('tool/result surface replacement must target a current tool/result')#必须对准当前 tool/result
        原载荷=dict(取字段(原事件,'data'))#原载荷副本
        新载荷=dict(取字段(事件,'data'))#替换载荷副本
        原结果=取字段(取字段(取字段(原事件,'data'),'message'),'content')[0]#原第一条内容
        新结果=取字段(取字段(取字段(事件,'data'),'message'),'content')[0]#新第一条内容
        原消息=dict(取字段(取字段(原事件,'data'),'message'))#保留消息其余
        原块=dict(原结果)#块副本
        原块['content']=None#内容置空
        原消息['content']=[原块]#抹掉内容
        原载荷['message']=原消息#写回
        新消息=dict(取字段(取字段(事件,'data'),'message'))#保留消息其余
        新块=dict(新结果)#块副本
        新块['content']=None#内容置空
        新消息['content']=[新块]#抹掉内容
        新载荷['message']=新消息#写回
        if not json深相等(原载荷,新载荷):#其余字段不同
            raise Exception('tool/result surface replacement may change only content')#只许改内容

def 计划表面事件(状态,事件,期望序号,事件们,基序号):#计划表面变迁
    """在回放边界校验一条事件，并准备其原子折叠变迁。"""
    if 试取(事件,'seq')!=期望序号:#序号不连续
        raise Exception('session event seq '+str(试取(事件,'seq'))+' is not contiguous; expected '+str(期望序号))#必须连续
    表面操作=取出表面操作(事件)#取出表面操作
    if 表面操作 is None:#非表面
        return None#非表面
    if 表面操作=='append':#追加
        断言出处(事件,[])#追加无遮蔽
        return {'kind':'append','seq':取字段(事件,'seq')}#追加计划
    区间=替换区间(状态,表面操作)#定位区间
    断言出处(事件,区间['shadowedSeqs'])#校验出处覆盖
    断言工具结果改写(事件,区间['shadowedSeqs'],事件们,基序号)#工具结果只许改内容
    return {#替换计划
        'kind':'replace',#替换
        'seq':取字段(事件,'seq'),#替换事件序号
        'start':表面操作['start'],#声明起点
        'end':表面操作['end'],#声明终点
        'startIdx':区间['startIdx'],#起点下标
        'endIdx':区间['endIdx'],#终点下标
        'shadowedSeqs':区间['shadowedSeqs'],#被遮蔽
    }#替换计划

def 应用表面计划(状态,计划):#提交表面变迁
    """提交一条先前已校验的表面变迁。"""
    if 计划 is not None and 试取(计划,'kind')=='append':#追加
        状态['nodes'].append(计划['seq'])#接到尾部
    elif 计划 is not None and 试取(计划,'kind')=='replace':#替换
        起点=计划['startIdx']#起点下标
        终点=计划['endIdx']#终点下标
        状态['nodes'][起点:终点+1]=[计划['seq']]#区间换成新序号
        状态['replaceGeneration']+=1#代数加一
    if 计划 is None or 试取(计划,'kind')!='replace':#非替换
        return None#非替换无元数据
    return {#替换元数据
        'seq':计划['seq'],#替换事件序号
        'start':计划['start'],#起点
        'end':计划['end'],#终点
        'shadowedSeqs':计划['shadowedSeqs'],#被遮蔽
    }#替换元数据

def 应用表面事件(状态,事件,期望序号,事件们,基序号):#应用一条事件
    """应用一条事件，仅在发生替换时返回替换元数据。"""
    计划=计划表面事件(状态,事件,期望序号,事件们,基序号)#先计划
    return 应用表面计划(状态,计划)#再提交

def 折叠表面(事件们):#完整折叠表面
    """经规范表面折叠回放一份完整会话日志。"""
    状态=创建折叠状态()#空状态
    替换们=[]#替换历史
    下标=0#按序号扫描
    for 事件 in 事件们:#按序号扫描
        替换=应用表面事件(状态,事件,下标,事件们,0)#应用事件
        if 替换 is not None:#记下替换
            替换们.append(替换)#记下替换
        下标+=1#下一条
    return {'nodes':list(状态['nodes']),'replacements':替换们}#脱离结果

class 表面管理器:#表面管理器
    """增量有序表面视图与追加边界校验器。"""
    def __init__(自身,日志,基序号=0):#构造
        """连续完整日志或已加载事件窗口。"""
        自身._日志=日志#日志窗口
        自身._基序号=基序号#窗口起点
        自身._状态=创建折叠状态()#折叠状态
        自身._上次处理序号=基序号-1#尚未处理窗口内事件
        自身._待提交=None#待提交计划

    def 校验下一条(自身,事件):#校验下一条
        """校验下一个候选，不改已提交表面。"""
        if 自身._上次处理序号<自身._基序号+len(自身._日志)-1:#尚未追上
            自身._追上增量()#先追上已追加
        期望序号=自身._基序号+len(自身._日志)#下一条期望序号
        自身._待提交={#暂存计划
            'event':事件,#候选
            'expectedSeq':期望序号,#期望序号
            'plan':计划表面事件(自身._状态,事件,期望序号,自身._日志,自身._基序号),#纯计划
        }#暂存计划

    @property#替换代数
    def replaceGeneration(自身):#替换代数
        """已折叠位置替换的单调计数。"""
        if 自身._上次处理序号<自身._基序号+len(自身._日志)-1:#尚未追上
            自身._追上增量()#先追上
        return 自身._状态['replaceGeneration']#返回代数

    @property#表面节点
    def nodes(自身):#表面节点
        """模型可见顺序的表面事件序号。"""
        if 自身._上次处理序号<自身._基序号+len(自身._日志)-1:#尚未追上
            自身._追上增量()#先追上
        return 自身._状态['nodes']#返回节点

    def _追上增量(自身):#追上增量
        """折叠自上次访问以来追加的事件。"""
        末序号=自身._基序号+len(自身._日志)-1#窗口末序号
        序号=自身._上次处理序号+1#从下一条起
        while 序号<=末序号:#逐条追上
            下标=序号-自身._基序号#窗口下标
            事件=自身._日志[下标]#取出事件
            待提交=自身._待提交#待提交计划
            if 待提交 is not None and 待提交['event'] is 事件 and 待提交['expectedSeq']==序号:#正好是已校验候选
                应用表面计划(自身._状态,待提交['plan'])#提交计划
            else:#普通追加
                应用表面事件(自身._状态,事件,序号,自身._日志,自身._基序号)#现场计划并提交
            if 待提交 is not None and 待提交['expectedSeq']<=序号:#过期计划
                自身._待提交=None#过期计划清掉
            自身._上次处理序号=序号#记下已处理
            序号+=1#下一条
