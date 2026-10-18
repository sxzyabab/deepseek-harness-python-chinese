'从工作区和会话顺序推出浏览树。未入账的会话落在未分组，空白会话只留当前选中的那一条'
from datetime import datetime
from ....工具.值 import 断言永不
from ....工具.工作区路径 import 工作区标题自

__all__=[
    '未分组键','拥有分组键','工作区标签','按近因排序','调和手动顺序','钉住当前空白',
    '派生分组','会话成员标识','可见会话标识','派生扁平','派生检索结果','拥有父文件夹',
]

未分组键=''#不在任何工作区里的会话用空键

def 拥有分组键(工作区列,会话号):
    '会话属于哪个浏览组。没有工作区记账时是未分组'
    for 工作区 in 工作区列:#宿主顺序
        if 会话号 in 工作区['sessionIds']:#成员
            return 工作区['workspaceId']#工作区
    return 未分组键#未分组

def 主会话号(列表):
    '当前主视图留着的会话'
    for 会话 in 列表['byId'].values():#逐条
        保留=会话.get('retainedBy') or {}#保留计数
        if (保留.get('mainView') or 0)>0:#主视图还留着
            return 会话['id']#这条
    return None#没有

def 工作区标签(目录):
    '目录的展示名是路径末段。未分组是空串'
    if 目录 is None or 目录=='':#没有目录
        return ''#空
    末段=工作区标题自(目录)#末段
    if 末段!='':#有末段
        return 末段#用末段
    return 目录#没有末段就用原路径

def 按近因排序(会话号列,摘要表):
    '已知成员按更新时间从新到旧。没有摘要的先不出现。时间相同按会话号'
    行=[]#带名次的成员
    for 标识 in 会话号列:#成员
        摘要=摘要表.get(标识)#摘要
        if 摘要 is None:#还没到
            continue#跳过
        行.append({'id':标识,'rank':摘要['updatedAt']})#名次
    def 近因键(项):
        '新的在前，会话号小的在前'
        return (-项['rank'],项['id'])#排序键
    行.sort(key=近因键)#排序
    return [项['id'] for 项 in 行]#只要号

def 调和手动顺序(成员号列,已存顺序,摘要表,行态=None):
    '已存的相对顺序保留。新的普通分叉插到源前面。置顶在前，归档在后'
    成员={}#字符串键到原号
    for 标识 in 成员号列:#成员
        成员[标识]=标识#原样
    已含=set()#已经放进结果的
    有序=[]#结果前段
    for 键 in (已存顺序 or []):#已存顺序
        标识=成员.get(键)#还是成员吗
        if 标识 is None or 键 in 已含:#不是或重复
            continue#跳过
        有序.append(标识)#按旧顺序
        已含.add(键)#记下
    归档集=set((行态 or {}).get('archivedSessionIds') or [])#归档
    置顶=[]#新出现的置顶
    for 会话号 in ((行态 or {}).get('pinnedSessionIds') or []):#置顶名单
        标识=成员.get(会话号)#是成员吗
        if 标识 is None or 标识 in 已含 or 标识 in 归档集 or 摘要表.get(标识) is None:#不能补
            continue#跳过
        置顶.append(标识)#补到前面
        已含.add(标识)#记下
    缺的=[标识 for 标识 in 成员.values() if 标识 not in 已含]#还没排的
    普通=[]#未归档的新成员
    归档=[]#新出现的归档
    for 标识 in 按近因排序(缺的,摘要表):#按近因
        if 标识 in 归档集:#归档
            归档.append(标识)#放后面
        else:#普通
            普通.append(标识)#放中间
    结果=置顶+有序+普通+归档#四段
    待放=set(普通)#还要按父会话挪位的
    def 安放分叉(标识):
        '新分叉插到父会话前面，不打乱已经排好的相对顺序'
        if 标识 not in 待放:#不是待放的新成员
            return#不动
        待放.remove(标识)#这一条处理过
        父号=(摘要表.get(标识) or {}).get('parentId')#父会话
        if 父号 is None or 父号==标识 or 父号 not in 结果:#没有可跟随的父
            return#留在原处
        安放分叉(父号)#先安放父
        结果.pop(结果.index(标识))#抽出自己
        结果.insert(结果.index(父号),标识)#插到父前面
    for 标识 in list(reversed(普通)):#从旧的新成员开始
        安放分叉(标识)#按父会话挪
    return 结果#调和后的顺序

def 钉住当前空白(顺序,当前空白):
    '选中的空白新会话始终排在这一本的最前'
    if 当前空白 is None:#没有
        return list(顺序)#拷贝
    return [当前空白]+[标识 for 标识 in 顺序 if 标识!=当前空白]#去重后提前

def 会话可见(会话,当前,归档集,归档筛选):
    '子智能体不进树。空白会话只留当前那条。归档按筛选'
    if 会话.get('origin')=='subagent':#子智能体
        return False#不进树
    if 会话.get('blank') and 会话['id']!=当前:#不是当前空白
        return False#藏起
    if 归档筛选=='default':#默认藏归档
        return 会话['id'] not in 归档集#未归档
    if 归档筛选=='show':#全部显示
        return True#都可见
    if 归档筛选=='only':#只看归档
        return 会话['id'] in 归档集#已归档
    return 断言永不(归档筛选)#封闭筛选

def 分段成员(成员列,置顶集,归档集):
    '空白占位在最前，然后是未归档的置顶，其余保持原顺序'
    占位=[]#空白
    领先=[]#置顶
    其余=[]#其它
    for 成员 in 成员列:#原顺序
        if 成员.get('blank'):#空白
            占位.append(成员)#最前
        elif 成员['id'] not in 归档集 and 成员['id'] in 置顶集:#置顶且未归档
            领先.append(成员)#置顶段
        else:#其余
            其余.append(成员)#后面
    return 占位+领先+其余#三段

def 会话标题(会话):
    '空白会话不带标题。没命名的历史也是空串，交给界面写未命名'
    if 会话.get('blank'):#空白
        return ''#不带标题
    标题=会话.get('title')#存储标题
    if isinstance(标题,str):#有字
        return 标题.strip()#去掉空白
    return ''#没有

def 建组(键,工作区号,目录,创建于,标签,成员列):
    '一组的记账，还没变成界面行'
    return {
        'key':键,#组键
        'workspaceId':工作区号,#工作区
        'cwd':目录,#目录
        'createdAt':创建于,#创建时间
        'label':标签,#标签
        'sessions':list(成员列),#成员
    }

def 可见待处理(种类):
    '只有审批、计划待审、提问这三种上到行上'
    if 种类 in ('approval','plan-review','question'):#已知
        return 种类#留下
    return None#其它不显示

def 运行子数(列表,父号,状态表):
    '已载入的子智能体名录里，正在跑的直接子代个数'
    投影=列表.get('projectionsBySession') or {}#按会话的投影
    值=(投影.get(父号) or {}).get('values') or {}#投影值
    名录=值.get('subagentCatalog')#名录
    if not isinstance(名录,list):#没有
        return 0#零
    个数=0#计数
    for 子 in 名录:#逐个
        子号=子.get('id')#子会话
        态=状态表.get(子号) if hasattr(状态表,'get') else None#统一状态
        在跑=None#是否在跑
        if isinstance(态,dict) and 'running' in 态:#状态里有
            在跑=态['running']#用状态
        else:#退回列表
            摘要=列表['byId'].get(子号) or {}#摘要
            在跑=摘要.get('running')#列表上的
        if 在跑 is True:#在跑
            个数=个数+1#加一
    return 个数#合计

def 会话节点(会话,列表,状态表,置顶集,归档集):
    '一条会话行要用的字段'
    态=状态表.get(会话['id']) if hasattr(状态表,'get') else None#统一状态
    待处理=None#待处理种类
    if isinstance(态,dict):#有状态
        交互=态.get('pendingInteraction') or {}#待处理
        待处理=可见待处理(交互.get('kind') if isinstance(交互,dict) else None)#种类
    在跑=会话.get('running')#列表上的
    完成未读=False#完成提醒
    if isinstance(态,dict):#有状态
        if 'running' in 态:#状态优先
            在跑=态['running']#覆盖
        完成未读=态.get('completionUnread') is True#未读完成
    节点={
        'id':会话['id'],#号
        'title':会话标题(会话),#标题
        'blank':会话.get('blank') is True,#空白
        'running':在跑 is True,#在跑
        'runningSubagentCount':运行子数(列表,会话['id'],状态表),#子代
        'completed':完成未读,#完成点
        'pinned':会话['id'] not in 归档集 and 会话['id'] in 置顶集,#置顶
        'archived':会话['id'] in 归档集,#归档
        'updatedAt':会话['updatedAt'],#更新时间
    }
    if 待处理 is not None:#有待处理
        节点['pendingInteraction']=待处理#种类
    return 节点#行

def 派生分组(列表,工作区列,行态,状态表,视图):
    '展开的组才填会话行。只看归档时，没有可见成员的组不出现'
    归档集=set(行态['archivedSessionIds'])#归档
    置顶集=set(行态['pinnedSessionIds'])#置顶
    展开集=set(视图['expandedGroups'])#展开
    当前=主会话号(列表)#当前会话
    当前组=None if 当前 is None else 拥有分组键(工作区列,当前)#当前组
    归档筛选=行态['archivedFilter']#筛选
    未分组顺序=视图.get('ungroupedOrder')#未分组已存顺序
    已入账=set()#已经算进工作区的
    组列=[]#记账组
    for 工作区 in 工作区列:#宿主组顺序
        成员=[]#可见成员
        for 标识 in 工作区['sessionIds']:#成员号
            摘要=列表['byId'].get(标识)#摘要
            if 摘要 is None:#列表还没到
                continue#稍后再出现
            已入账.add(标识)#入账
            if not 会话可见(摘要,当前,归档集,归档筛选):#不可见
                continue#跳过
            成员.append(摘要)#留下
        if 归档筛选=='only' and len(成员)==0:#只看归档且没有
            continue#不贡献组
        创建于=None#创建时间
        原文=工作区.get('createdAt')#宿主时间串
        if isinstance(原文,str) and 原文!='':#有串
            try:#Date.parse 对非法串给 NaN，这里给 None
                创建于=datetime.fromisoformat(原文.replace('Z','+00:00')).timestamp()*1000#毫秒
            except ValueError:#非法
                创建于=None#没有
        组列.append(建组(
            工作区['workspaceId'],工作区['workspaceId'],工作区['path'],
            创建于,工作区['title'],成员,
        ))#一组
    散落=[]#没进任何工作区的
    for 标识 in 列表['ids']:#列表顺序
        摘要=列表['byId'].get(标识)#摘要
        if 摘要 is None or 标识 in 已入账:#没有或已入账
            continue#跳过
        if not 会话可见(摘要,当前,归档集,归档筛选):#不可见
            continue#跳过
        散落.append(摘要)#散落
    if len(散落)>0:#有散落
        按号={会话['id']:会话 for 会话 in 散落}#号到摘要
        if 未分组顺序 is None:#还没初始化
            号列=按近因排序([会话['id'] for 会话 in 散落],列表['byId'])#近因
        else:#已有手动顺序
            号列=调和手动顺序([会话['id'] for 会话 in 散落],未分组顺序,列表['byId'])#调和
        有序散落=[]#按顺序的摘要
        for 标识 in 号列:#顺序
            会话=按号.get(标识)#摘要
            if 会话 is not None:#找得到
                有序散落.append(会话)#留下
        组列.append(建组(未分组键,None,None,None,'',有序散落))#未分组
    结果=[]#界面组
    for 组 in 组列:#逐组
        展开=组['key'] in 展开集#是否展开
        会话行=[]#展开才填
        if 展开:#展开
            for 会话 in 分段成员(组['sessions'],置顶集,归档集):#分段
                会话行.append(会话节点(会话,列表,状态表,置顶集,归档集))#行
        结果.append({
            'key':组['key'],#键
            'workspaceId':组['workspaceId'],#工作区
            'cwd':组['cwd'],#目录
            'createdAt':组['createdAt'],#创建
            'label':组['label'],#标签
            'sessionCount':len(组['sessions']),#可见条数
            'expanded':展开,#展开
            'containsCurrent':组['key']==当前组,#含当前
            'sessions':会话行,#行
        })#一组
    return 结果#组

def 可见会话标识(列表,归档号列,归档筛选):
    '扁平列表里可见的会话号，顺序跟列表走'
    归档集=set(归档号列)#归档
    当前=主会话号(列表)#当前
    结果=[]#可见
    for 标识 in 列表['ids']:#列表顺序
        摘要=列表['byId'].get(标识)#摘要
        if 摘要 is not None and 会话可见(摘要,当前,归档集,归档筛选):#可见
            结果.append(标识)#留下
    return 结果#号

def 会话成员标识(列表):
    '扁平列表的完整成员，含归档，只留当前空白'
    return 可见会话标识(列表,[],'show')#显示含归档

def 派生扁平(列表,会话号列,行态,状态表):
    '按给定顺序出扁平行，置顶段提前'
    归档集=set(行态['archivedSessionIds'])#归档
    置顶集=set(行态['pinnedSessionIds'])#置顶
    当前=主会话号(列表)#当前
    成员=[]#可见摘要
    for 标识 in 会话号列:#给定顺序
        会话=列表['byId'].get(标识)#摘要
        if 会话 is not None and 会话可见(会话,当前,归档集,行态['archivedFilter']):#可见
            成员.append(会话)#留下
    return [会话节点(会话,列表,状态表,置顶集,归档集) for 会话 in 分段成员(成员,置顶集,归档集)]#行

def 派生检索结果(列表,工作区列,查询,归档号列,归档筛选,状态表,内容,上限):
    '标题和目录的本地命中在前，宿主内容命中按原顺序补上。重复的会话带上摘录'
    词=查询.strip().lower()#查询
    if 词=='':#空
        return {'items':[],'hasMore':False}#没有
    归档集=set(归档号列)#归档
    当前=主会话号(列表)#当前
    工作区名={}#会话到工作区标题
    for 工作区 in 工作区列:#逐个
        for 会话号 in 工作区['sessionIds']:#成员
            if 会话号 not in 工作区名:#先到的标题
                工作区名[会话号]=工作区['title']#标题
    def 标签(摘要):
        '工作区标题，没有就用目录末段'
        已有=工作区名.get(摘要['id'])#工作区
        if 已有 is not None:#有
            return 已有#标题
        return 工作区标签(摘要.get('cwd'))#目录
    内容表={}#会话到内容命中
    for 项 in 内容.get('items') or []:#宿主页
        if 项['sessionId'] not in 内容表:#先到的
            内容表[项['sessionId']]=项#留下
    本地=[]#标题或目录命中
    for 标识 in 列表['ids']:#列表顺序
        摘要=列表['byId'].get(标识)#摘要
        if 摘要 is None or 摘要.get('blank') or not 会话可见(摘要,当前,归档集,归档筛选):#不参与
            continue#跳过
        标题=会话标题(摘要)#标题
        if 词 in 标题.lower() or 词 in 标签(摘要).lower():#命中
            本地.append(摘要)#留下
    本地表={摘要['id']:摘要 for 摘要 in 本地}#号到摘要
    有序本地=[]#按近因
    for 标识 in 按近因排序([摘要['id'] for 摘要 in 本地],列表['byId']):#近因
        有序本地.append(本地表[标识])#摘要
    有序=[]#合并后
    已含=set()#已放入
    def 放入(摘要):
        '同一会话只放一次'
        if 摘要['id'] in 已含:#已有
            return#跳过
        已含.add(摘要['id'])#记下
        有序.append(摘要)#放入
    for 摘要 in 有序本地:#本地优先
        放入(摘要)#放
    for 项 in 内容.get('items') or []:#内容页
        摘要=列表['byId'].get(项['sessionId'])#摘要
        if 摘要 is not None and not 摘要.get('blank') and 会话可见(摘要,当前,归档集,归档筛选):#可见
            放入(摘要)#补上
    条目=[]#界面行
    for 摘要 in 有序[:上限]:#上限内
        命中=内容表.get(摘要['id'])#摘录
        态=状态表.get(摘要['id']) if hasattr(状态表,'get') else None#状态
        待处理=None#待处理
        在跑=摘要.get('running')#列表
        完成未读=False#完成
        if isinstance(态,dict):#有状态
            交互=态.get('pendingInteraction') or {}#交互
            待处理=可见待处理(交互.get('kind') if isinstance(交互,dict) else None)#种类
            if 'running' in 态:#优先
                在跑=态['running']#覆盖
            完成未读=态.get('completionUnread') is True#未读
        行={
            'id':摘要['id'],#号
            'title':会话标题(摘要),#标题
            'workspace':标签(摘要),#工作区
            'running':在跑 is True,#在跑
            'runningSubagentCount':运行子数(列表,摘要['id'],状态表),#子代
            'completed':完成未读,#完成
            'archived':摘要['id'] in 归档集,#归档
        }
        if 待处理 is not None:#有
            行['pendingInteraction']=待处理#种类
        if 命中 is not None:#有摘录
            行['snippet']=命中.get('snippet')#摘录
        条目.append(行)#一行
    还有=内容.get('hasMore') is True or len(有序)>上限#要收窄
    return {'items':条目,'hasMore':还有}#结果

def 拥有父文件夹(路径,父列):
    '最近的已登记祖先目录。工作区自己的目录不算。大小写敏感'
    def 文件夹(值):
        '比较用的路径。Windows 才把反斜杠换成斜杠'
        是窗=False#是否 Windows
        if len(值)>=3 and 值[0].isalpha() and 值[1]==':' and 值[2] in '/\\':#盘符
            是窗=True#是
        if 值.startswith('\\\\'):#UNC
            是窗=True#是
        文=值.replace('\\','/') if 是窗 else 值#分隔符
        while 文.endswith('/'):#去掉尾部
            文=文[:-1]#削
        return 文#比较用
    子=文件夹(路径)#子路径
    主人=None#最近祖先原文
    长度=-1#已选长度
    for 父 in 父列:#已登记目录
        根=文件夹(父)#比较形
        if len(根)>长度 and 子!=根 and 子.startswith(根+'/'):#更近的祖先
            主人=父#原文
            长度=len(根)#更长
    return 主人#没有就是 None
