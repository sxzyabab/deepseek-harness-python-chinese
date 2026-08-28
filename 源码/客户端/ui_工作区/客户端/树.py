"""由宿主工作区的顺序与成员关系派生工作区浏览器树。

对齐上游 `ui-workspace/src/client/tree.ts`。公开面仅中文名。
子智能体后代索引内联对齐 runtime `subagent-lineage.ts`。
"""
from datetime import datetime#解析工作区创建时间

__all__=[#仅中文公开名
    '未分组键',
    '未分组标签',
    '工作区标签',
    '索引子智能体后代',
    '派生分组',
    '派生扁平',
    '派生检索结果',
    '相对时间',
    '取字段',
]#公开面结束

未分组键=''#未分组桶的空字符串键
未分组标签='Ungrouped'#未分组桶的展示标签（运行时英文字面量）

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 工作区标签(工作目录):#工作区/目录展示标签
    """目录 basename；没有 basename 时返回原始路径；再否则未分组标签。"""
    if 工作目录 is None or 工作目录=='':#空路径
        return 未分组标签#未分组
    基名=工作目录.rstrip('/\\').replace('\\','/').split('/')[-1]#最后一段
    return 基名 if 基名!='' else 工作目录#有 basename 用它

def 解析创建毫秒(创建原文):#创建时间 → 毫秒
    """ISO 串或数值转 epoch 毫秒；无法解析为 None。"""
    if 创建原文 is None:#缺席
        return None#无
    if isinstance(创建原文,(int,float)):#已是数值
        return int(创建原文)#毫秒
    if not isinstance(创建原文,str):#非串
        return None#无
    return int(datetime.fromisoformat(创建原文.replace('Z','+00:00')).timestamp()*1000)#解析

def 会话可见(会话,当前,已归档):#会话是否出现在浏览器树
    """普通会话可见；空白只留当前选中；子智能体与已归档不出现。"""
    return (取字段(会话,'origin')!='subagent'#非子智能体
        and 取字段(会话,'id') not in 已归档#未归档
        and ((not 取字段(会话,'blank')) or 取字段(会话,'id')==当前))#空白只留当前

def 会话标题(会话):#会话行标题
    """空白用规范英文标题，否则用已存展示标题。"""
    return 'New Session' if 取字段(会话,'blank') else 取字段(会话,'displayTitle')#标题

def 组装分组(键,工作区标识,工作目录,创建于,标签,成员们,顺序):#组装内部分组
    """组装一个分组，不把会话谱系投影成展示。"""
    会话=list(成员们)#拷贝成员
    if 顺序=='recency':#近因序
        会话.sort(key=lambda 项:( -取字段(项,'updatedAt'),取字段(项,'id')))#最新在前
    return {'key':键,'workspaceId':工作区标识,'cwd':工作目录,'createdAt':创建于,'label':标签,'sessions':会话}#内部分组

def 有序未分组(成员们,已存):#按已存键序排未分组会话
    """套用已存的未分组顺序，新散落的会话按近因追加。"""
    按标识={取字段(会话,'id'):会话 for 会话 in 成员们}#id → 摘要
    已纳入=set()#已纳入
    有序=[]#结果
    for 键 in 已存:#先走已存顺序
        会话=按标识.get(键)#摘要
        if 会话 is None or 键 in 已纳入:#未知或已纳入
            continue#跳过
        有序.append(会话)#追加
        已纳入.add(键)#记下
    剩余=sorted(成员们,key=lambda 项:( -取字段(项,'updatedAt'),取字段(项,'id')))#近因
    for 会话 in 剩余:#收新散落
        if 取字段(会话,'id') in 已纳入:#已在
            continue#跳过
        有序.append(会话)#追加
    return 有序#已存序 + 新散落

def 按工作区分组(列表,工作区们,已归档,未分组序):#按工作区账本分组
    """按宿主工作区给会话分组；散落会话进未分组桶。"""
    分组们=[]#结果
    已认领=set()#已被账本认领
    按标识=取字段(列表,'byId') or {}#摘要表
    当前=取字段(列表,'current')#当前会话
    for 工作区 in 工作区们:#按宿主顺序
        成员=[]#本组可见成员
        for 标识 in 取字段(工作区,'sessionIds') or []:#账本序
            摘要=按标识.get(标识) if isinstance(按标识,dict) else 取字段(按标识,标识)#摘要
            if 摘要 is None:#账本早于列表
                continue#跳过
            已认领.add(标识)#记认领
            if not 会话可见(摘要,当前,已归档):#不可见
                continue#跳过
            成员.append(摘要)#可见
        创建毫秒=解析创建毫秒(取字段(工作区,'createdAt'))#毫秒或 None
        分组们.append(组装分组(取字段(工作区,'workspaceId'),取字段(工作区,'workspaceId'),取字段(工作区,'path'),创建毫秒,取字段(工作区,'title'),成员,'account'))#账本序
    散落=[]#未被认领且可见
    for 标识 in 取字段(列表,'ids') or []:#列表序
        摘要=按标识.get(标识) if isinstance(按标识,dict) else 取字段(按标识,标识)#摘要
        if 摘要 is None:#缺席
            continue#跳过
        if 取字段(摘要,'id') in 已认领:#已认领
            continue#跳过
        if not 会话可见(摘要,当前,已归档):#不可见
            continue#跳过
        散落.append(摘要)#收下
    if len(散落)>0:#有散落
        成员=散落 if 未分组序 is None else 有序未分组(散落,未分组序)#套序
        分组们.append(组装分组(未分组键,None,None,None,未分组标签,成员,'recency' if 未分组序 is None else 'account'))#未分组桶
    return 分组们#宿主顺序 + 可选未分组

def 索引子智能体后代(按标识):#按谱系索引运行中的后代
    """在每个祖先下索引经不间断子智能体来源链到达的后代。

    对齐上游 runtime `subagent-lineage.ts` 的 indexSubagentDescendants。
    """
    索引={}#父 id → {count, runningCount}
    if not isinstance(按标识,dict):#非映射
        return 索引#空
    for 后代 in 按标识.values():#每个可能的后代
        if 取字段(后代,'origin')!='subagent':#只沿子智能体来源走
            continue#跳过
        已见=set()#防环
        当前=后代#沿父链上走
        while (取字段(当前,'origin')=='subagent'#仍是子智能体
            and 取字段(当前,'parentId') is not None#且有父
            and 取字段(当前,'id') not in 已见):#且未见过
            已见.add(取字段(当前,'id'))#记下本节点
            父标识=取字段(当前,'parentId')#父 id
            聚合=索引.get(父标识)#父上的聚合
            if 聚合 is None:#第一次见到该父
                索引[父标识]={'count':1,'runningCount':1 if 取字段(后代,'running') else 0}#新建
            else:#已有聚合
                聚合['count']=取字段(聚合,'count',0)+1#后代加一
                if 取字段(后代,'running'):#叶子在跑
                    聚合['runningCount']=取字段(聚合,'runningCount',0)+1#运行加一
            当前=按标识.get(父标识)#走到父
            if 当前 is None:#孤儿
                break#停
    return 索引#父 id → 计数

def 会话行(摘要,后代):#摘要 → 展示行
    """把摘要投影成顶层会话行。"""
    标识=取字段(摘要,'id')#会话 id
    后代摘要=后代.get(标识) if isinstance(后代,dict) else None#该会话后代
    行={#会话行字段
        'id':标识,#id
        'title':会话标题(摘要),#标题
        'blank':取字段(摘要,'blank'),#是否空白
        'running':取字段(摘要,'running'),#自身是否在跑
        'runningSubagentCount':取字段(后代摘要,'runningCount',0) if 后代摘要 is not None else 0,#后代数
        'completed':取字段(摘要,'completed') is True,#未读完成
        'updatedAt':取字段(摘要,'updatedAt'),#最近活动
    }#字段结束
    待处理=取字段(摘要,'pendingInteraction')#待处理交互
    if 待处理 is not None:#有则带上
        行['pendingInteraction']=待处理#待处理
    return 行#展示行

def 派生分组(列表,工作区们,已归档会话标识,视图):#派生分组树
    """派生工作区浏览器分组，每个会话都是顶层行。"""
    已归档=set(已归档会话标识)#归档集
    已展开=set(取字段(视图,'expandedGroups') or [])#已展开
    后代=索引子智能体后代(取字段(列表,'byId') or {})#后代索引
    当前=取字段(列表,'current')#当前会话
    当前组=None#当前组键
    if 当前 is not None:#有当前会话
        当前组=未分组键#默认未分组
        for 工作区 in 工作区们:#真实工作区
            if 当前 in (取字段(工作区,'sessionIds') or []):#命中账本
                当前组=取字段(工作区,'workspaceId')#工作区 id
                break#找到
    结果=[]#展示分组
    for 组 in 按工作区分组(列表,工作区们,已归档,取字段(视图,'ungroupedOrder')):#内部组
        展开=组['key'] in 已展开#是否展开
        结果.append({#展示段
            'key':组['key'],#分组键
            'workspaceId':组['workspaceId'],#工作区 id
            'cwd':组['cwd'],#工作目录
            'createdAt':组['createdAt'],#创建时间
            'label':组['label'],#展示标签
            'sessionCount':len(组['sessions']),#可见会话总数
            'expanded':展开,#是否展开
            'containsCurrent':组['key']==当前组,#是否含当前
            'sessions':[会话行(会话,后代) for 会话 in 组['sessions']] if 展开 else [],#展开才投影
        })#展示段结束
    return 结果#渲染顺序

def 派生扁平(列表,已归档会话标识):#派生扁平列表
    """每个可见会话一条顶层行，严格最新在前。"""
    已归档=set(已归档会话标识)#归档集
    按标识=取字段(列表,'byId') or {}#摘要表
    后代=索引子智能体后代(按标识)#后代
    行=[]#可见摘要
    当前=取字段(列表,'current')#当前
    for 标识 in 取字段(列表,'ids') or []:#列表序
        摘要=按标识.get(标识) if isinstance(按标识,dict) else 取字段(按标识,标识)#摘要
        if 摘要 is None or not 会话可见(摘要,当前,已归档):#不可见
            continue#跳过
        行.append(摘要)#收下
    行.sort(key=lambda 项:( -取字段(项,'updatedAt'),取字段(项,'id')))#最新在前
    return [会话行(会话,后代) for 会话 in 行]#投影

def 派生检索结果(列表,工作区们,查询,已归档会话标识,正文,上限):#合并标题/工作区匹配与正文检索
    """本地行最新在前领头，仅正文命中的行保留后端顺序。"""
    问=查询.strip().lower()#去空白小写
    if 问=='':#空查询
        return {'items':[],'hasMore':False}#无命中
    已归档=set(已归档会话标识)#归档集
    按标识=取字段(列表,'byId') or {}#摘要表
    后代=索引子智能体后代(按标识)#后代
    当前=取字段(列表,'current')#当前
    会话工作区={}#会话 → 工作区标题
    for 工作区 in 工作区们:#每个工作区
        for 会话标识 in 取字段(工作区,'sessionIds') or []:#账本成员
            if 会话标识 not in 会话工作区:#先到先得
                会话工作区[会话标识]=取字段(工作区,'title')#标题
    def 标签于(摘要):#会话的工作区展示标签
        """账本标题优先，否则从 cwd 派生。"""
        return 会话工作区.get(取字段(摘要,'id')) or 工作区标签(取字段(摘要,'cwd'))#标签
    正文按会话={}#会话 → 正文命中
    for 项 in 取字段(正文,'items') or []:#宿主正文页
        标识=取字段(项,'sessionId')#会话 id
        if 标识 not in 正文按会话:#先到先得
            正文按会话[标识]=项#记下
    本地=[]#标题/工作区子串命中
    for 标识 in 取字段(列表,'ids') or []:#列表序
        摘要=按标识.get(标识) if isinstance(按标识,dict) else 取字段(按标识,标识)#摘要
        if 摘要 is None or 取字段(摘要,'blank') or not 会话可见(摘要,当前,已归档):#跳过
            continue#下一条
        if 问 in 会话标题(摘要).lower() or 问 in 标签于(摘要).lower():#子串命中
            本地.append(摘要)#收入
    本地.sort(key=lambda 项:( -取字段(项,'updatedAt'),取字段(项,'id')))#最新在前
    有序=[]#合并去重
    已纳入=set()#已纳入
    def 纳入(摘要):#去重追加
        """已在结果里则忽略。"""
        标识=取字段(摘要,'id')#id
        if 标识 in 已纳入:#已在
            return#忽略
        已纳入.add(标识)#记下
        有序.append(摘要)#追加
    for 摘要 in 本地:#先本地
        纳入(摘要)#纳入
    for 项 in 取字段(正文,'items') or []:#再正文
        摘要=按标识.get(取字段(项,'sessionId')) if isinstance(按标识,dict) else 取字段(按标识,取字段(项,'sessionId'))#摘要
        if 摘要 is not None and not 取字段(摘要,'blank') and 会话可见(摘要,当前,已归档):#可见非空白
            纳入(摘要)#纳入
    投影=[]#有界投影
    for 摘要 in 有序[:上限]:#截到上限
        标识=取字段(摘要,'id')#id
        命中=正文按会话.get(标识)#正文项
        后代摘要=后代.get(标识)#后代
        行={#检索行
            'id':标识,#id
            'title':会话标题(摘要),#标题
            'workspace':标签于(摘要),#工作区
            'running':取字段(摘要,'running'),#运行
            'runningSubagentCount':取字段(后代摘要,'runningCount',0) if 后代摘要 is not None else 0,#后代数
            'completed':取字段(摘要,'completed') is True,#完成
        }#行结束
        待处理=取字段(摘要,'pendingInteraction')#待处理
        if 待处理 is not None:#有则带上
            行['pendingInteraction']=待处理#待处理
        if 命中 is not None:#有正文片段
            行['snippet']=取字段(命中,'snippet')#片段
        投影.append(行)#收下
    return {'items':投影,'hasMore':bool(取字段(正文,'hasMore')) or len(有序)>上限}#结果集

def 相对时间(更新于,现在):#相对时间桶
    """会话行的紧凑相对时间结构化桶。"""
    分=60_000#一分钟毫秒
    时=3_600_000#一小时
    日=86_400_000#一天
    差=max(0,现在-更新于)#非负差
    if 差<分:#不足一分钟
        return {'unit':'now','n':0}#刚刚
    if 差<时:#不足一小时
        return {'unit':'minutes','n':差//分}#分钟
    if 差<日:#不足一天
        return {'unit':'hours','n':差//时}#小时
    if 差<30*日:#不足三十天
        return {'unit':'days','n':差//日}#天
    if 差<365*日:#不足一年
        return {'unit':'months','n':差//(30*日)}#月
    return {'unit':'years','n':差//(365*日)}#年
