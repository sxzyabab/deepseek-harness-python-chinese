from datetime import datetime#解析工作区创建时间
from zoneinfo import ZoneInfo#UTC

__all__=[#仅中文公开名
    '未分组键',
    '未分组标签',
    '工作区标签',
    '索引子智能体后代',
    '拥有分组键',
    '按近因排序',
    '调和手动顺序',
    '钉住当前空白',
    '可见会话标识',
    '派生分组',
    '派生扁平',
    '派生检索结果',
    '相对时间',
]#公开面结束

未分组键=''#未分组桶的空字符串键
未分组标签='Ungrouped'#未分组桶的展示标签（运行时英文字面量）
创建时刻格式='%Y-%m-%dT%H:%M:%S.%fZ'#工作区记录 createdAt：toISOString

def 工作区标签(工作目录):#工作区/目录展示标签
    """目录 basename；没有 basename 时返回原始路径；空路径返回空标记。"""
    if 工作目录 is None or 工作目录=='':#空路径
        return ''#空标记
    基名=工作目录.rstrip('/\\').replace('\\','/').split('/')[-1]#最后一段
    return 基名 if 基名!='' else 工作目录#有 basename 用它

def 拥有分组键(工作区列表,会话标识):#解析拥有一场会话的浏览器分组
    """无人认领时为未分组键。"""
    for 工作区 in 工作区列表:#真实工作区
        账本=工作区['sessionIds'] if 'sessionIds' in 工作区 and 工作区['sessionIds'] is not None else []#账本
        if 会话标识 in 账本:#命中
            return 工作区['workspaceId']#工作区 id
    return 未分组键#未分组

def 解析创建毫秒(创建原文):#创建时间 → 毫秒
    """工作区记录为 toISOString；已是纪元毫秒则原样。"""
    if 创建原文 is None:#缺席
        return None#无
    if isinstance(创建原文,bool):#bool 是 int 子类
        return None#无
    if isinstance(创建原文,(int,float)):#已是数值
        return int(创建原文)#毫秒
    if not isinstance(创建原文,str):#非串
        return None#无
    时刻=datetime.strptime(创建原文,创建时刻格式).replace(tzinfo=ZoneInfo('UTC'))#写死 ISO 毫秒零区
    return int(时刻.timestamp()*1000)#纪元毫秒

def 会话可见(会话,当前,已归档):#会话是否出现在浏览器树
    """普通会话可见；空白只留当前选中；子智能体与已归档不出现。"""
    return (会话['origin']!='subagent'#非子智能体
        and 会话['id'] not in 已归档#未归档
        and ((not 会话['blank']) or 会话['id']==当前))#空白只留当前

def 会话标题(会话):#会话行标题
    """空白用空串，否则用已存展示标题。"""
    return '' if 会话['blank'] else 会话['displayTitle']#标题

def 有活动日程(会话):#是否有活动日程
    """列表投影的日程非空。"""
    投影=会话['projectionValues'] if 'projectionValues' in 会话 else None#投影
    if not isinstance(投影,dict):#无
        return False#否
    日程=投影['schedule'] if 'schedule' in 投影 else None#日程
    return isinstance(日程,list) and len(日程)>0#非空

def 可见待处理种类(种类):#收窄可见待处理
    """审批、计划待审、提问；其余 None。"""
    if 种类=='approval' or 种类=='plan-review' or 种类=='question':#可见
        return 种类#保留
    return None#不可见

def 按近因排序(会话标识列表,按标识):#账本成员 → 近因序
    """已知成员最新在前，id 决胜；尚无摘要的省略。"""
    带时=[]#带更新时间
    for 标识 in 会话标识列表:#账本成员
        if 标识 not in 按标识:#尚无摘要
            continue#省略
        带时.append((-按标识[标识]['updatedAt'],标识))#近因键
    带时.sort()#最新在前
    return [项[1] for 项 in 带时]#只要 id

def 调和手动顺序(成员标识列表,已存,按标识):#调和已存本地序与当前账本
    """保留的已存槽后接新认识成员。"""
    成员集=set(成员标识列表)#成员
    已纳入=set()#已纳入
    有序=[]#结果
    已存列=[] if 已存 is None else 已存#已存
    for 键 in 已存列:#先走已存
        if 键 not in 成员集 or 键 in 已纳入:#未知或重复
            continue#跳过
        有序.append(键)#追加
        已纳入.add(键)#记下
    for 标识 in 按近因排序(成员标识列表,按标识):#再收新成员
        if 标识 in 已纳入:#已有
            continue#跳过
        有序.append(标识)#追加
        已纳入.add(标识)#记下
    return 有序#已存槽 + 新成员

def 钉住当前空白(顺序,当前空白):#选中空白置顶
    """无空白则拷贝；空白在前且无重复槽。"""
    if 当前空白 is None:#无
        return list(顺序)#拷贝
    return [当前空白]+[标识 for 标识 in 顺序 if 标识!=当前空白]#置顶去重

def 有序未分组(成员列表,已存,按标识):#套已存序或近因
    """新散落的会话按近因追加。"""
    索引={会话['id']:会话 for 会话 in 成员列表}#id → 摘要
    标识列表=[会话['id'] for 会话 in 成员列表]#成员 id
    序=按近因排序(标识列表,按标识) if 已存 is None else 调和手动顺序(标识列表,已存,按标识)#序
    return [索引[标识] for 标识 in 序 if 标识 in 索引]#按序取摘要

def 按工作区分组(列表,工作区列表,已归档,未分组序):#按工作区账本分组
    """按宿主工作区给会话分组；散落会话进未分组桶。"""
    分组列表=[]#结果
    已认领=set()#已被账本认领
    按标识=列表['byId'] if 'byId' in 列表 and 列表['byId'] is not None else {}#摘要表
    当前=列表['current'] if 'current' in 列表 else None#当前会话
    for 工作区 in 工作区列表:#按宿主顺序
        成员=[]#本组可见成员
        账本=工作区['sessionIds'] if 'sessionIds' in 工作区 and 工作区['sessionIds'] is not None else []#账本序
        for 标识 in 账本:#账本序
            if 标识 not in 按标识:#账本早于列表
                continue#跳过
            摘要=按标识[标识]#摘要
            已认领.add(标识)#记认领
            if not 会话可见(摘要,当前,已归档):#不可见
                continue#跳过
            成员.append(摘要)#可见
        创建毫秒=解析创建毫秒(工作区['createdAt'] if 'createdAt' in 工作区 else None)#毫秒或 None
        分组列表.append({'key':工作区['workspaceId'],'workspaceId':工作区['workspaceId'],'cwd':工作区['path'],'createdAt':创建毫秒,'label':工作区['title'],'sessions':list(成员)})#账本序
    散落=[]#未被认领且可见
    标识列表=列表['ids'] if 'ids' in 列表 and 列表['ids'] is not None else []#列表序
    for 标识 in 标识列表:#列表序
        if 标识 not in 按标识:#缺席
            continue#跳过
        摘要=按标识[标识]#摘要
        if 摘要['id'] in 已认领:#已认领
            continue#跳过
        if not 会话可见(摘要,当前,已归档):#不可见
            continue#跳过
        散落.append(摘要)#收下
    if len(散落)>0:#有散落
        成员=有序未分组(散落,未分组序,按标识)#套序
        分组列表.append({'key':未分组键,'workspaceId':None,'cwd':None,'createdAt':None,'label':'','sessions':成员})#未分组桶
    return 分组列表#宿主顺序 + 可选未分组

def 索引子智能体后代(按标识):#按谱系索引运行中的后代
    """在每个祖先下索引经不间断子智能体来源链到达的后代。

    对齐上游 runtime `subagent-lineage.ts` 的 indexSubagentDescendants。
    """
    索引={}#父 id → {count, runningCount}
    for 后代 in 按标识.values():#每个可能的后代
        if 后代['origin']!='subagent':#只沿子智能体来源走
            continue#跳过
        已见=set()#防环
        当前=后代#沿父链上走
        while (当前['origin']=='subagent'#仍是子智能体
            and 当前['parentId'] is not None#且有父
            and 当前['id'] not in 已见):#且未见过
            已见.add(当前['id'])#记下本节点
            父标识=当前['parentId']#父 id
            if 父标识 not in 索引:#第一次见到该父
                索引[父标识]={'count':1,'runningCount':1 if 后代['running'] else 0}#新建
            else:#已有聚合
                聚合=索引[父标识]#聚合
                聚合['count']=聚合['count']+1#后代加一
                if 后代['running']:#叶子在跑
                    聚合['runningCount']=聚合['runningCount']+1#运行加一
            if 父标识 not in 按标识:#孤儿
                break#停
            当前=按标识[父标识]#走到父
    return 索引#父 id → 计数

def 会话行(摘要,后代,待处理):#摘要 → 展示行
    """把摘要投影成顶层会话行。"""
    标识=摘要['id']#会话 id
    后代摘要=后代[标识] if 标识 in 后代 else None#该会话后代
    待=待处理[标识] if 待处理 is not None and 标识 in 待处理 else None#待处理
    种类=None#可见种类
    if isinstance(待,dict) and 'kind' in 待:#有 kind
        种类=可见待处理种类(待['kind'])#收窄
    行={#会话行字段
        'id':标识,#id
        'title':会话标题(摘要),#标题
        'blank':摘要['blank'],#是否空白
        'running':摘要['running'],#自身是否在跑
        'runningSubagentCount':后代摘要['runningCount'] if 后代摘要 is not None else 0,#后代数
        'completed':摘要['completed'] is True if 'completed' in 摘要 else False,#未读完成
        'hasActiveSchedule':有活动日程(摘要),#活动日程
        'updatedAt':摘要['updatedAt'],#最近活动
    }#字段结束
    if 种类 is not None:#有则带上
        行['pendingInteraction']=种类#待处理
    return 行#展示行

def 派生分组(列表,工作区列表,已归档会话标识,待处理,视图):#派生分组树
    """派生工作区浏览器分组，每个会话都是顶层行。"""
    已归档=set(已归档会话标识)#归档集
    展开列=视图['expandedGroups'] if 'expandedGroups' in 视图 and 视图['expandedGroups'] is not None else []#已展开
    已展开=set(展开列)#已展开
    按标识=列表['byId'] if 'byId' in 列表 and 列表['byId'] is not None else {}#摘要表
    后代=索引子智能体后代(按标识)#后代索引
    交互=待处理 if 待处理 is not None else {}#待处理表
    当前=列表['current'] if 'current' in 列表 else None#当前会话
    当前组=None if 当前 is None else 拥有分组键(工作区列表,当前)#当前组键
    未分组序=视图['ungroupedOrder'] if 'ungroupedOrder' in 视图 else None#未分组序
    结果=[]#展示分组
    for 组 in 按工作区分组(列表,工作区列表,已归档,未分组序):#内部组
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
            'sessions':[会话行(会话,后代,交互) for 会话 in 组['sessions']] if 展开 else [],#展开才投影
        })#展示段结束
    return 结果#渲染顺序

def 可见会话标识(列表,已归档会话标识):#选出扁平列表成员
    """列表顺序上的已知可见会话 id。"""
    已归档=set(已归档会话标识)#归档集
    按标识=列表['byId'] if 'byId' in 列表 and 列表['byId'] is not None else {}#摘要表
    当前=列表['current'] if 'current' in 列表 else None#当前
    结果=[]#可见 id
    标识列表=列表['ids'] if 'ids' in 列表 and 列表['ids'] is not None else []#列表序
    for 标识 in 标识列表:#列表序
        if 标识 not in 按标识:#缺
            continue#跳过
        if 会话可见(按标识[标识],当前,已归档):#可见
            结果.append(标识)#收下
    return 结果#可见 id

def 派生扁平(列表,会话标识列表,待处理=None):#由已排序可见 id 派生扁平行
    """按所给顺序投影，带当前状态指示。"""
    按标识=列表['byId'] if 'byId' in 列表 and 列表['byId'] is not None else {}#摘要表
    后代=索引子智能体后代(按标识)#后代
    交互=待处理 if 待处理 is not None else {}#待处理
    return [会话行(按标识[标识],后代,交互) for 标识 in 会话标识列表 if 标识 in 按标识]#按序投影

def 派生检索结果(列表,工作区列表,查询,已归档会话标识,待处理,正文,上限):#合并标题/工作区匹配与正文检索
    """本地行最新在前领头，仅正文命中的行保留后端顺序。"""
    问=查询.strip().lower()#去空白小写
    if 问=='':#空查询
        return {'items':[],'hasMore':False}#无命中
    已归档=set(已归档会话标识)#归档集
    按标识=列表['byId'] if 'byId' in 列表 and 列表['byId'] is not None else {}#摘要表
    后代=索引子智能体后代(按标识)#后代
    交互=待处理 if 待处理 is not None else {}#待处理
    当前=列表['current'] if 'current' in 列表 else None#当前
    会话工作区={}#会话 → 工作区标题
    for 工作区 in 工作区列表:#每个工作区
        账本=工作区['sessionIds'] if 'sessionIds' in 工作区 and 工作区['sessionIds'] is not None else []#账本成员
        for 会话标识 in 账本:#账本成员
            if 会话标识 not in 会话工作区:#先到先得
                会话工作区[会话标识]=工作区['title']#标题
    def 标签于(摘要):#会话的工作区展示标签
        """账本标题优先，否则从 cwd 派生。"""
        标识=摘要['id']#id
        if 标识 in 会话工作区:#账本
            return 会话工作区[标识]#标题
        return 工作区标签(摘要['cwd'] if 'cwd' in 摘要 else None)#从 cwd 派生
    正文按会话={}#会话 → 正文命中
    正文项=正文['items'] if 正文 is not None and 'items' in 正文 and 正文['items'] is not None else []#宿主正文页
    for 项 in 正文项:#宿主正文页
        标识=项['sessionId']#会话 id
        if 标识 not in 正文按会话:#先到先得
            正文按会话[标识]=项#记下
    本地=[]#标题/工作区子串命中
    标识列表=列表['ids'] if 'ids' in 列表 and 列表['ids'] is not None else []#列表序
    for 标识 in 标识列表:#列表序
        if 标识 not in 按标识:#缺
            continue#下一条
        摘要=按标识[标识]#摘要
        if 摘要['blank'] or not 会话可见(摘要,当前,已归档):#跳过
            continue#下一条
        if 问 in 会话标题(摘要).lower() or 问 in 标签于(摘要).lower():#子串命中
            本地.append(摘要)#收入
    本地标识=按近因排序([摘要['id'] for 摘要 in 本地],按标识)#最新在前
    本地索引={摘要['id']:摘要 for 摘要 in 本地}#索引
    有序=[]#合并去重
    已纳入=set()#已纳入
    def 纳入(摘要):#去重追加
        """已在结果里则忽略。"""
        标识=摘要['id']#id
        if 标识 in 已纳入:#已在
            return#忽略
        已纳入.add(标识)#记下
        有序.append(摘要)#追加
    for 标识 in 本地标识:#先本地
        纳入(本地索引[标识])#纳入
    for 项 in 正文项:#再正文
        标识=项['sessionId']#会话 id
        if 标识 not in 按标识:#无摘要
            continue#跳
        摘要=按标识[标识]#摘要
        if not 摘要['blank'] and 会话可见(摘要,当前,已归档):#可见非空白
            纳入(摘要)#纳入
    投影=[]#有界投影
    for 摘要 in 有序[:上限]:#截到上限
        标识=摘要['id']#id
        命中=正文按会话[标识] if 标识 in 正文按会话 else None#正文项
        后代摘要=后代[标识] if 标识 in 后代 else None#后代
        待=交互[标识] if 标识 in 交互 else None#待处理
        种类=可见待处理种类(待['kind']) if isinstance(待,dict) and 'kind' in 待 else None#收窄
        行={#检索行
            'id':标识,#id
            'title':会话标题(摘要),#标题
            'workspace':标签于(摘要),#工作区
            'running':摘要['running'],#运行
            'runningSubagentCount':后代摘要['runningCount'] if 后代摘要 is not None else 0,#后代数
            'completed':摘要['completed'] is True if 'completed' in 摘要 else False,#完成
            'hasActiveSchedule':有活动日程(摘要),#活动日程
        }#行结束
        if 种类 is not None:#有则带上
            行['pendingInteraction']=种类#待处理
        if 命中 is not None and 'snippet' in 命中:#有正文片段
            行['snippet']=命中['snippet']#片段
        投影.append(行)#收下
    正文更多=正文['hasMore'] if 正文 is not None and 'hasMore' in 正文 else False#后端还有
    return {'items':投影,'hasMore':bool(正文更多) or len(有序)>上限}#结果集

def 相对时间(更新于,现在):#相对时间桶
    """会话行的紧凑相对时间结构化桶。更新于与现在都是纪元毫秒 int。"""
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
