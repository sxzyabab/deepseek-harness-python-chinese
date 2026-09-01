"""一次性的会话谱系与事件关系追踪辅助。对齐上游 `session-query/src/tracing.ts`。"""
from ....内核.会话 import 折叠表面,是否表面事件,快照会话事件#面折叠与快照
from .配置 import 会话查询错误#检索错误

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 事件记录(会话号,事件们):#构建事件记录
    """用一次规范面折叠给原始事件日志分类。"""
    return 分析事件日志(会话号,事件们)['records']#只要记录

def 当前面事件(会话号,事件们):#读取当前面事件
    """在校验整份日志后折叠并返回当前模型面。"""
    分析=分析事件日志(会话号,事件们)#先分析整份日志
    结果=[]#当前面事件
    for 序号 in 分析['currentSeqs']:#按折叠顺序
        事件=事件们[序号] if 序号<len(事件们) else None#按序号取
        if 事件 is None or 取字段(事件,'seq')!=序号 or not 是否表面事件(事件):#不是面事件
            raise 会话查询错误(f'invalid session surface: current node {序号} is not a surface event','SESSION_QUERY_INVALID_SURFACE')#非法面
        结果.append(快照会话事件(事件))#拍面事件快照
    return 结果#当前面事件

def 追踪事件(会话号,事件们,序号):#追踪单事件关系
    """在一次规范面折叠与整份日志校验之后追踪一个目标。"""
    目标=事件们[序号] if 序号<len(事件们) else None#按序号取
    if 目标 is None or 取字段(目标,'seq')!=序号:#缺席或序号对不上
        raise 会话查询错误(f'session "{会话号}" has no event at seq {序号}','SESSION_QUERY_EVENT_NOT_FOUND')#未找到
    分析=分析事件日志(会话号,事件们)#分析整份日志
    替换链=[]#位置替换链
    替换=分析['replacedBy'].get(序号)#直接替换者
    while 替换 is not None:#沿链走到底
        替换链.append(替换)#收下
        替换=分析['replacedBy'].get(替换)#下一跳
    派生序号们=[]#引用本目标的更晚事件
    for 事件 in 事件们:#扫完整日志
        if 取字段(事件,'seq')<=序号:#只要更晚的
            continue#跳过
        if 序号 in 事件来源(事件):#直接引用目标
            派生序号们.append(取字段(事件,'seq'))#记下
    目标记录=分析['records'][序号]#目标轻量记录
    被替换者=分析['replacedBy'].get(序号)#直接替换者
    追踪={#组装追踪
        'target':目标记录,#目标记录
        'replacementChain':替换链,#替换链
        'replacedEventSeqs':分析['replacedEventSeqs'].get(序号,[]),#目标替换掉的
        'sourceEventSeqs':list(事件来源(目标)),#目标引用的源
        'derivedEventSeqs':派生序号们,#引用目标的派生
    }#追踪骨架
    if 被替换者 is not None:#有替换者
        追踪['replacedBy']=被替换者#直接替换者
    return 追踪#返回追踪

def 追踪会话(记录们,会话号):#追踪会话谱系
    """追踪一个目标的已知祖先与递归已知后代。"""
    索引={取字段(取字段(记录,'header'),'id'):记录 for 记录 in 记录们}#按id索引
    目标=索引.get(会话号)#取出目标
    if 目标 is None:#语料里没有
        raise 会话查询错误(f'session "{会话号}" not found','SESSION_QUERY_SESSION_NOT_FOUND')#未找到
    祖先们=[]#祖先链
    已见={会话号}#环检测
    未解析父=None#走出语料的父id
    父号=取字段(取字段(目标,'header'),'parentSession')#当前父
    while 父号 is not None:#沿父链向外
        if 父号 in 已见:#成环
            raise 会话查询错误(f'session lineage contains a cycle at "{父号}"','SESSION_QUERY_INVALID_LINEAGE')#成环
        已见.add(父号)#记下
        父记录=索引.get(父号)#查父
        if 父记录 is None:#语料缺席
            未解析父=父号#记下
            break#停止
        祖先们.append(父记录)#收下祖先
        父号=取字段(取字段(父记录,'header'),'parentSession')#继续向外
    子索引={}#父到直接子
    for 记录 in 记录们:#建子索引
        父=取字段(取字段(记录,'header'),'parentSession')#父会话
        if 父 is None:#无父
            continue#跳过
        子索引.setdefault(父,[]).append(记录)#收下子
    for 子们 in 子索引.values():#每组排序
        子们.sort(key=lambda 行:(取字段(取字段(行,'header'),'createdAt'),取字段(取字段(行,'header'),'id')))#时间升序再id
    后代们=构建后代(子索引,会话号)#递归后代树
    公共={#共用字段
        'target':克隆记录(目标),#克隆目标
        'ancestors':[克隆记录(记录) for 记录 in 祖先们],#克隆祖先
        'descendants':后代们,#后代树
    }#公共结束
    if 未解析父 is not None:#父链不完整
        return {**公共,'complete':False,'unresolvedParentId':未解析父}#显式不完整
    根=克隆记录(祖先们[-1] if len(祖先们)>0 else 目标)#最外层祖先或自身
    return {**公共,'complete':True,'root':根}#完整谱系

def 分析事件日志(会话号,事件们):#分析一份原始日志
    """一次日志分析：记录、替换映射与当前面序号。"""
    try:#折叠当前面
        折叠=折叠表面(事件们)#可能抛出
    except Exception as 错误:#折叠失败
        消息=取字段(错误,'message',str(错误)) if isinstance(错误,BaseException) else 'unknown error'#消息
        raise 会话查询错误(f'invalid session surface: {消息}','SESSION_QUERY_INVALID_SURFACE',{'cause':错误})#非法面
    当前=set(取字段(折叠,'nodes',[]))#当前面序号
    被谁替换={}#被谁替换
    替换移除={}#替换者移除了哪些
    for 替换 in 取字段(折叠,'replacements',[]):#逐条替换
        移除们=取字段(替换,'shadowedSeqs',[])#被遮蔽序号
        替换移除[取字段(替换,'seq')]=移除们#记下移除列表
        for 被遮蔽 in 移除们:#每个被遮蔽
            被谁替换[被遮蔽]=取字段(替换,'seq')#指向替换者
    记录们=[]#轻量记录
    for 事件 in 事件们:#逐事件
        序号=取字段(事件,'seq')#序号
        面='current' if 序号 in 当前 else ('shadowed' if 序号 in 被谁替换 else 'log-only')#面位置
        记录们.append({'sessionId':会话号,'seq':序号,'type':取字段(事件,'type'),'time':取字段(事件,'time'),'surface':面})#记录
    return {'records':记录们,'replacedBy':被谁替换,'replacedEventSeqs':替换移除,'currentSeqs':list(取字段(折叠,'nodes',[]))}#分析结果

def 事件来源(事件):#取出被引用源序号
    """取出被引用源序号；非面事件则空。"""
    return 取字段(事件,'sourceEventSeqs',[]) or []#来源序号

def 构建后代(子索引,会话号):#迭代构建后代树
    """迭代构建后代树，保持时间顺序。"""
    后代们=[]#根层后代
    栈=[{'sessionId':会话号,'descendants':后代们,'nodes':子索引.get(会话号,[])}]#待展开
    while len(栈)>0:#还有帧
        帧=栈.pop()#弹出
        节点们=[]#本帧新建
        for 子 in 帧['nodes']:#直接子
            节点={'session':克隆记录(子),'descendants':[]}#新节点
            节点们.append(节点)#记下
            帧['descendants'].append(节点)#挂到父
        for 节点 in reversed(节点们):#倒序压栈
            栈.append({'sessionId':取字段(取字段(节点['session'],'header'),'id'),'descendants':节点['descendants'],'nodes':子索引.get(取字段(取字段(节点['session'],'header'),'id'),[])})#子帧
    return 后代们#根后代

def 克隆记录(记录):#克隆会话记录
    """克隆会话记录的头。"""
    from ....模型后端.llm import 结构化克隆#拆离克隆
    return {'header':结构化克隆(取字段(记录,'header')),'live':取字段(记录,'live'),'persisted':取字段(记录,'persisted')}#克隆头
