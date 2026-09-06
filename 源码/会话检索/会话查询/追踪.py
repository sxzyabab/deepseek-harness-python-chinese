"""一次性的会话谱系与事件关系追踪辅助。对齐上游 `session-query/src/tracing.ts`。"""
from ....内核.会话 import 折叠表面,是否表面事件,快照会话事件#面折叠与快照
from ....内核.会话.表面 import 表面错误#面折叠失败
from ....模型后端.llm import 结构化克隆#拆离克隆
from .配置 import 会话查询错误#检索错误

def 事件记录(会话号,事件列表):
    """用一次规范面折叠给原始事件日志分类。"""
    return 分析事件日志(会话号,事件列表)['records']#只要记录

def 当前面事件(会话号,事件列表):
    """在校验整份日志后折叠并返回当前模型面。"""
    分析=分析事件日志(会话号,事件列表)#先分析整份日志
    结果=[]#当前面事件
    for 序号 in 分析['currentSeqs']:#按折叠顺序
        事件=事件列表[序号] if 序号<len(事件列表) else None#按序号取
        if 事件 is None or 事件['seq']!=序号 or not 是否表面事件(事件):#不是面事件
            raise 会话查询错误('invalid session surface: current node '+str(序号)+' is not a surface event','SESSION_QUERY_INVALID_SURFACE')#非法面
        结果.append(快照会话事件(事件))#拍面事件快照
    return 结果#当前面事件

def 追踪事件(会话号,事件列表,序号):
    """在一次规范面折叠与整份日志校验之后追踪一个目标。"""
    目标=事件列表[序号] if 序号<len(事件列表) else None#按序号取
    if 目标 is None or 目标['seq']!=序号:#缺席或序号对不上
        raise 会话查询错误('session "'+str(会话号)+'" has no event at seq '+str(序号),'SESSION_QUERY_EVENT_NOT_FOUND')#未找到
    分析=分析事件日志(会话号,事件列表)#分析整份日志
    替换链=[]#位置替换链
    替换=分析['replacedBy'][序号] if 序号 in 分析['replacedBy'] else None#直接替换者
    while 替换 is not None:#沿链走到底
        替换链.append(替换)#收下
        替换=分析['replacedBy'][替换] if 替换 in 分析['replacedBy'] else None#下一跳
    派生序号列表=[]#引用本目标的更晚事件
    for 事件 in 事件列表:#扫完整日志
        if 事件['seq']<=序号:#只要更晚的
            continue#跳过
        if 序号 in 事件来源(事件):#直接引用目标
            派生序号列表.append(事件['seq'])#记下
    目标记录=分析['records'][序号]#目标轻量记录
    被替换者=分析['replacedBy'][序号] if 序号 in 分析['replacedBy'] else None#直接替换者
    追踪={
        'target':目标记录,#目标记录
        'replacementChain':替换链,#替换链
        'replacedEventSeqs':分析['replacedEventSeqs'][序号] if 序号 in 分析['replacedEventSeqs'] else [],#目标替换掉的
        'sourceEventSeqs':list(事件来源(目标)),#目标引用的源
        'derivedEventSeqs':派生序号列表,#引用目标的派生
    }#追踪骨架
    if 被替换者 is not None:#有替换者
        追踪['replacedBy']=被替换者#直接替换者
    return 追踪#返回追踪

def 会话排序键(行):
    """后代排序：创建时刻再 id。"""
    头=行['header']#头
    return (头['createdAt'],头['id'])#键

def 追踪会话(记录列表,会话号):
    """追踪一个目标的已知祖先与递归已知后代。"""
    索引={记录['header']['id']:记录 for 记录 in 记录列表}#按id索引
    if 会话号 not in 索引:#语料里没有
        raise 会话查询错误('session "'+str(会话号)+'" not found','SESSION_QUERY_SESSION_NOT_FOUND')#未找到
    目标=索引[会话号]#取出目标
    祖先列表=[]#祖先链
    已见={会话号}#环检测
    未解析父=None#走出语料的父id
    父号=目标['header']['parentSession'] if 'parentSession' in 目标['header'] else None#当前父
    while 父号 is not None:#沿父链向外
        if 父号 in 已见:#成环
            raise 会话查询错误('session lineage contains a cycle at "'+str(父号)+'"','SESSION_QUERY_INVALID_LINEAGE')#成环
        已见.add(父号)#记下
        if 父号 not in 索引:#语料缺席
            未解析父=父号#记下
            break#停止
        父记录=索引[父号]#查父
        祖先列表.append(父记录)#收下祖先
        父号=父记录['header']['parentSession'] if 'parentSession' in 父记录['header'] else None#继续向外
    子索引={}#父到直接子
    for 记录 in 记录列表:#建子索引
        父=记录['header']['parentSession'] if 'parentSession' in 记录['header'] else None#父会话
        if 父 is None:#无父
            continue#跳过
        if 父 not in 子索引:#首次
            子索引[父]=[]#新表
        子索引[父].append(记录)#收下子
    for 子列表 in 子索引.values():#每组排序
        子列表.sort(key=会话排序键)#时间升序再id
    后代列表=构建后代(子索引,会话号)#递归后代树
    公共={
        'target':克隆记录(目标),#克隆目标
        'ancestors':[克隆记录(记录) for 记录 in 祖先列表],#克隆祖先
        'descendants':后代列表,#后代树
    }#公共结束
    if 未解析父 is not None:#父链不完整
        return {**公共,'complete':False,'unresolvedParentId':未解析父}#显式不完整
    根=克隆记录(祖先列表[-1] if len(祖先列表)>0 else 目标)#最外层祖先或自身
    return {**公共,'complete':True,'root':根}#完整谱系

def 分析事件日志(会话号,事件列表):
    """一次日志分析：记录、替换映射与当前面序号。"""
    try:#折叠当前面
        折叠=折叠表面(事件列表)#可能抛出
    except 表面错误 as 错误:#折叠失败
        raise 会话查询错误('invalid session surface: '+str(错误),'SESSION_QUERY_INVALID_SURFACE',{'cause':错误})#非法面
    当前=set(折叠['nodes'])#当前面序号
    被谁替换={}#被谁替换
    替换移除={}#替换者移除了哪些
    for 替换 in 折叠['replacements']:#逐条替换
        移除列表=替换['shadowedSeqs'] if 'shadowedSeqs' in 替换 else []#被遮蔽序号
        替换移除[替换['seq']]=移除列表#记下移除列表
        for 被遮蔽 in 移除列表:#每个被遮蔽
            被谁替换[被遮蔽]=替换['seq']#指向替换者
    记录列表=[]#轻量记录
    for 事件 in 事件列表:#逐事件
        序号=事件['seq']#序号
        面='current' if 序号 in 当前 else ('shadowed' if 序号 in 被谁替换 else 'log-only')#面位置
        记录列表.append({'sessionId':会话号,'seq':序号,'type':事件['type'],'time':事件['time'],'surface':面})#记录
    return {'records':记录列表,'replacedBy':被谁替换,'replacedEventSeqs':替换移除,'currentSeqs':list(折叠['nodes'])}#分析结果

def 事件来源(事件):
    """取出被引用源序号；非面事件则空。"""
    源列表=事件['sourceEventSeqs'] if 'sourceEventSeqs' in 事件 else []#来源序号
    return 源列表 if isinstance(源列表,list) else []#来源序号

def 构建后代(子索引,会话号):
    """迭代构建后代树，保持时间顺序。"""
    后代列表=[]#根层后代
    栈=[{'sessionId':会话号,'descendants':后代列表,'nodes':子索引[会话号] if 会话号 in 子索引 else []}]#待展开
    while len(栈)>0:#还有帧
        帧=栈.pop()#弹出
        节点列表=[]#本帧新建
        for 子 in 帧['nodes']:#直接子
            节点={'session':克隆记录(子),'descendants':[]}#新节点
            节点列表.append(节点)#记下
            帧['descendants'].append(节点)#挂到父
        for 节点 in reversed(节点列表):#倒序压栈
            标识=节点['session']['header']['id']#子 id
            栈.append({'sessionId':标识,'descendants':节点['descendants'],'nodes':子索引[标识] if 标识 in 子索引 else []})#子帧
    return 后代列表#根后代

def 克隆记录(记录):
    """克隆会话记录的头。"""
    return {'header':结构化克隆(记录['header']),'live':记录['live'],'persisted':记录['persisted']}#克隆头
