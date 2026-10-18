'按连续事件窗增量组装业务上下文，并物化已登记视图快照'
from ..约定.会话 import 会话上下文键
from ...异常 import 对话错误
from .组存储 import 会话组存储
from .位置索引 import 会话位置索引

__all__=['会话节点组装器']

发布秩={'none':0,'animation-frame':1,'immediate':2}
位置范围=('step','turn')
无组={'entries':lambda: [],'forTarget':lambda 目标:None}

def 末项(列):
    '空列没有末项'
    if len(列)==0:
        return None
    return 列[-1]

def 空位置数据():
    '步和回合都还没有位置数据'
    return {'step':None,'turn':None}

def 最大发布(左,右):
    '取更高的发布节奏'
    if 发布秩[左]>=发布秩[右]:
        return 左
    return 右

def 起始序号(上下文):
    '上下文的起始事件序号'
    return 上下文['startSeq']

def 插入下标(上下文列,序号):
    '按起始序号找到插入点'
    低=0
    高=len(上下文列)
    while 低<高:
        中=低+(高-低)//2
        候选=上下文列[中]
        if 候选 is not None and 候选['startSeq']<序号:
            低=中+1
        else:
            高=中
    return 低

def 上下文快照(上下文):
    '交给定义的只读上下文'
    return {
        'key':上下文['key'],
        'kind':上下文['kind'],
        'id':上下文['id'],
        'matches':上下文['matches'],
        'start':上下文['start'],
        'state':上下文['state'],
        'current':上下文['current'],
    }

def 合并匹配(键,新增,已有):
    '按事件序号合并。同一序号出现两次就失败'
    合并=[]
    加=0
    现=0
    while 加<len(新增) or 现<len(已有):
        左=新增[加] if 加<len(新增) else None
        右=已有[现] if 现<len(已有) else None
        if 左 is not None and 右 is not None and 左['event']['seq']==右['event']['seq']:
            raise 对话错误('conversation Context '+键+' received duplicate Match '+str(左['event']['seq']))
        if 右 is None or (左 is not None and 左['event']['seq']<右['event']['seq']):
            合并.append(左)
            加+=1
        else:
            合并.append(右)
            现+=1
    return 合并

def 会话匹配(输入,角色,位置):
    '一条匹配：事件、角色和位置'
    return {'event':输入['event'],'role':角色,'location':位置}

def 是位置边界(类型):
    '回合或步骤的开始和结束'
    return 类型 in ('turn/start','turn/end','step/start','step/end')

def 要求状态(定义,阶段,状态):
    'start 和 update 不能返回 None'
    if 状态 is None:
        raise 对话错误('conversation Definition "'+定义['kind']+'" returned undefined from '+阶段+'()')
    return 状态

class 会话节点组装器:
    '一份会话拥有的增量引擎。视图快照从这里读'
    def __init__(自身,事件定义,视图定义,组定义=None):
        '记下三份注册表，并按当前视图定义重置构建器'
        自身.事件定义=事件定义
        自身.视图定义=视图定义
        自身.组定义=无组 if 组定义 is None else 组定义
        自身.上下文={}
        自身.按种类={}
        自身.按序号={}
        自身.按目标={}
        自身.输入={}
        自身.位置=会话位置索引()
        自身.脏=set()
        自身.按目标脏={}
        自身.已修订=set()
        自身.依赖者={}
        自身.视图={}
        自身.组={}
        自身.待发布组=set()
        自身.活动目标=set()
        自身.命中定义=[]
        自身.命中结果=[]
        自身.还有更多=False
        自身.待替换=True
        自身.时间线脏=True
        自身.重置视图构建器()

    def openTurn(自身):
        '最新回合已加载且仍开着时返回回合号'
        快照=自身.位置.快照()
        顺序=快照['turnOrder']
        最新=None if len(顺序)==0 else 顺序[-1]
        回合=None if 最新 is None else 快照['turns'].get(最新)
        if 回合 is not None and 回合.get('status')=='open' and 回合.get('start') is not None:
            return 回合['turn']
        return None

    def replaceWindow(自身,条目列,还有更多):
        '整窗替换后立即发布'
        自身.上下文.clear()
        自身.按种类.clear()
        自身.按序号.clear()
        自身.按目标.clear()
        自身.输入.clear()
        自身.脏.clear()
        自身.按目标脏.clear()
        自身.已修订.clear()
        自身.依赖者.clear()
        自身.还有更多=还有更多
        排序=sorted(条目列,key=lambda 项:项['event']['seq'])
        for 条目 in 排序:
            自身.输入[条目['event']['seq']]=条目
        自身.位置.重建(排序)
        自身.时间线脏=True
        for 条目 in 排序:
            自身.匹配输入(条目)
        自身.重放依赖()
        自身.已修订.clear()
        for 上下文 in 自身.上下文.values():
            自身.标脏(上下文)
        自身.待替换=True
        return 'immediate'

    def append(自身,记录):
        '追加一条尾事件，不扫描已有上下文'
        事件=记录['event']
        if 事件['seq'] in 自身.输入:
            return 'none'
        if len(自身.已修订)>0:
            自身.已修订.clear()
        自身.输入[事件['seq']]=记录
        发布='none'
        if 事件['type']!='assistant/live-chunk' and 是位置边界(事件['type']):
            先前=自身.位置.快照()
            变更=自身.位置.追加边界(事件)
            if 自身.位置.快照() is not 先前:
                自身.时间线脏=True
                发布='immediate'
            自身.重放上下文(自身.刷新匹配位置(变更))
            if len(变更)>0:
                发布='immediate'
        else:
            自身.位置.追加非边界(事件)
        发布=最大发布(发布,自身.匹配输入(记录))
        if 自身.重放已修订依赖者():
            发布='immediate'
        if len(自身.已修订)>0:
            自身.已修订.clear()
        return 发布

    def settleAssistant(自身,尝试标识,条目=None):
        '退役一次助手尝试的瞬时匹配，再套上可选的耐久结算'
        自身.已修订.clear()
        退役=[]
        for 候选 in 自身.输入.values():
            if 候选.get('type')=='transient' and 候选['event']['data']['attemptId']==尝试标识:
                退役.append(候选)
        退役序号=set(项['event']['seq'] for 项 in 退役)
        受影响=set()
        for 序号 in 退役序号:
            del 自身.输入[序号]
            for 上下文 in 自身.按序号.get(序号,[]):
                受影响.add(上下文)
            if 序号 in 自身.按序号:
                del 自身.按序号[序号]
        for 上下文 in 受影响:
            上下文['matches']=[匹配 for 匹配 in 上下文['matches'] if 匹配['event']['seq'] not in 退役序号]
        自身.位置.移除助手瞬时([项['event'] for 项 in 退役])
        发布='none' if len(退役)==0 else 'immediate'
        if 条目 is not None and 条目['event']['seq'] not in 自身.输入:
            自身.输入[条目['event']['seq']]=条目
            自身.位置.插入助手结算(条目['event'])
            待定={}
            发布=最大发布(发布,自身.收集输入(条目,待定))
            自身.应用待定匹配(待定,受影响)
        自身.重放上下文(受影响)
        if 自身.重放已修订依赖者():
            发布='immediate'
        自身.已修订.clear()
        return 发布

    def prepend(自身,条目列,还有更多):
        '向前补一页，保留已有上下文和视图身份'
        自身.已修订.clear()
        发布='none'
        先前还有=自身.还有更多
        新鲜=sorted([项 for 项 in 条目列 if 项['event']['seq'] not in 自身.输入],key=lambda 项:项['event']['seq'])
        for 条目 in 新鲜:
            自身.输入[条目['event']['seq']]=条目
        自身.还有更多=还有更多
        先前时间线=自身.位置.快照()
        变更位置=自身.位置.重建(自身.排序输入())
        if 自身.位置.快照() is not 先前时间线:
            自身.时间线脏=True
        受影响=自身.刷新匹配位置(变更位置)
        待定={}
        for 条目 in 新鲜:
            发布=最大发布(发布,自身.收集输入(条目,待定))
        自身.应用待定匹配(待定,受影响)
        自身.重放上下文(受影响)
        if (len(自身.已修订)>0 or 先前还有!=还有更多) and 自身.重放依赖():
            发布='immediate'
        if len(变更位置)>0:
            发布='immediate'
        自身.已修订.clear()
        return 发布

    def rebuildRegistry(自身):
        '注册表变了就按当前窗重建'
        自身.重置视图构建器()
        return 自身.replaceWindow(自身.排序输入(),自身.还有更多)

    def flush(自身):
        '物化脏上下文并推进每个活动视图。有变化才返回真'
        if (not 自身.待替换) and len(自身.脏)==0 and (not 自身.时间线脏):
            return False
        if 自身.待替换:
            自身.替换位置数据()
            已更新=[]
            变更回合=自身.位置.取走变更回合()
            for 目标 in 自身.活动目标:
                视图=自身.视图.get(目标)
                if 视图 is None:
                    continue
                自身.更新视图(视图,True,自身.构建目标节点(目标,自身.按目标.get(目标)),变更回合)
                已更新.append(视图)
            自身.待替换=False
            自身.脏.clear()
            自身.按目标脏.clear()
            自身.时间线脏=False
            return 自身.发布视图(已更新)
        已更新=[]
        if 自身.应用脏位置数据():
            自身.时间线脏=True
        变更回合=自身.位置.取走变更回合()
        时间线脏=自身.时间线脏
        for 目标 in 自身.活动目标:
            视图=自身.视图.get(目标)
            if 视图 is None or 视图['builder'] is None:
                continue
            更新项=自身.构建目标更新(目标,自身.按目标脏.get(目标))
            if len(更新项)==0 and not 时间线脏:
                continue
            自身.更新视图(视图,False,更新项,变更回合)
            已更新.append(视图)
        自身.脏.clear()
        自身.按目标脏.clear()
        自身.时间线脏=False
        return 自身.发布视图(已更新)

    def activateTarget(自身,目标):
        '把目标放进单调活动集，并物化当前快照'
        视图=自身.视图.get(目标)
        if 目标 in 自身.活动目标:
            return False
        已发布=自身.flush()
        自身.活动目标.add(目标)
        if 视图 is None:
            return 已发布
        自身.替换视图(视图)
        自身.发布视图([视图])
        return True

    def snapshot(自身,目标):
        '已登记目标的最新快照。还没激活则没有'
        视图=自身.视图.get(目标)
        if 视图 is None:
            return None
        return 视图['snapshot']

    def get(自身,目标):
        '视图快照存储的读取口'
        return 自身.snapshot(目标)

    def grouped(自身,目标):
        '这个目标的分组视图'
        组=自身.组.get(目标)
        if 组 is None:
            return None
        return 组['store']

    def activityTargets(自身):
        '拥有者认为当前快照有可见活动的目标'
        活动=set()
        for 目标 in 自身.活动目标:
            视图=自身.视图.get(目标)
            if 视图 is None or 视图['isActive'] is None:
                continue
            if 视图['isActive'](视图['snapshot']) is True:
                活动.add(视图['target'])
        return 活动

    def 排序输入(自身):
        '按事件序号排好的已加载输入'
        return sorted(自身.输入.values(),key=lambda 项:项['event']['seq'])

    def 匹配输入(自身,输入):
        '分发并接受匹配'
        return 自身.分发输入(输入,自身.接受匹配)

    def 收集输入(自身,输入,待定):
        '先收进待定表，整批再套上'
        def 接受(定义,标识,匹配):
            '按上下文键累积'
            键=会话上下文键(定义['kind'],标识)
            列=待定.get(键)
            if 列 is None:
                列=[]
                待定[键]=列
            列.append({'definition':定义,'id':标识,'match':匹配})
            发布=定义.get('publication')
            if 发布 is None:
                return 'immediate'
            return 发布(匹配)
        return 自身.分发输入(输入,接受)

    def 分发输入(自身,输入,接受):
        '先解决独占声明，再按角色接受。回退只在没有普通命中时'
        事件=输入['event']
        起始匹配=None
        更新匹配=None
        位置=None
        def 取匹配(角色):
            '同一事件的位置只算一次'
            nonlocal 起始匹配,更新匹配,位置
            if 位置 is None:
                位置=自身.位置.位置于(事件)
            if 角色=='start':
                if 起始匹配 is None:
                    起始匹配=会话匹配(输入,角色,位置)
                return 起始匹配
            if 更新匹配 is None:
                更新匹配=会话匹配(输入,角色,位置)
            return 更新匹配
        定义列=自身.命中定义
        结果列=自身.命中结果
        定义列.clear()
        结果列.clear()
        路由=None
        if hasattr(自身.事件定义,'forEvent'):
            路由=自身.事件定义.forEvent(事件['type'])
        if 路由 is None:
            for 定义 in 自身.事件定义.entries():
                结果=定义['match'](事件)
                if 结果 is None:
                    continue
                定义列.append(定义)
                结果列.append(结果)
        else:
            for 路由项 in 路由:
                结果=路由项['match'](事件)
                if 结果 is None:
                    continue
                定义列.append(路由项['definition'])
                结果列.append(结果)
        声明=None
        下标=0
        while 下标<len(结果列):
            if 结果列[下标].get('exclusive') is True:
                定义=定义列[下标]
                目标=定义.get('target')
                if 目标 is None:
                    raise 对话错误('conversation Definition "'+定义['kind']+'" claims '+事件['type']+' at seq '+str(事件['seq'])+' without a target')
                已声明=None if 声明 is None else 声明.get(目标)
                if 已声明 is not None:
                    raise 对话错误('conversation Definitions "'+已声明+'" and "'+定义['kind']+'" both claim '+事件['type']+' at seq '+str(事件['seq'])+' on target "'+目标+'"')
                if 声明 is None:
                    声明={}
                声明[目标]=定义['kind']
            下标+=1
        第一=None
        第二=None
        其余=None
        发布='none'
        下标=0
        while 下标<len(结果列):
            定义=定义列[下标]
            结果=结果列[下标]
            目标=定义.get('target')
            if 目标 is not None and 结果.get('exclusive') is not True and 声明 is not None and 目标 in 声明:
                下标+=1
                continue
            if 目标 is not None and 目标!=第一 and 目标!=第二:
                if 第一 is None:
                    第一=目标
                elif 第二 is None:
                    第二=目标
                else:
                    if 其余 is None:
                        其余=set()
                    其余.add(目标)
            发布=最大发布(发布,接受(定义,结果['id'],取匹配(结果['role'])))
            下标+=1
        回退=自身.事件定义.fallbackEntry()
        目标=None if 回退 is None else 回退.get('target')
        if 回退 is not None and 目标 is not None and 目标!=第一 and 目标!=第二 and (其余 is None or 目标 not in 其余):
            结果=回退['match'](事件)
            if 结果 is not None:
                发布=最大发布(发布,接受(回退,结果['id'],取匹配(结果['role'])))
        return 发布

    def 创建上下文(自身,定义,标识,键):
        '新建一份上下文并挂到目标索引'
        上下文={
            'key':键,
            'kind':定义['kind'],
            'id':标识,
            'definition':定义,
            'startSeq':None,
            'start':None,
            'matches':[],
            'state':None,
            'revision':0,
            'current':{},
            'locationData':空位置数据(),
            'dependencies':{},
        }
        自身.上下文[键]=上下文
        自身.索引目标上下文(上下文)
        return 上下文

    def 接受匹配(自身,定义,标识,匹配):
        '追加一条匹配。起始之后才更新状态'
        种类列=自身.按种类.get(定义['kind'],[])
        最新=末项(种类列)
        if 最新 is not None and 最新['id']==标识:
            键=最新['key']
        else:
            键=会话上下文键(定义['kind'],标识)
        上下文=自身.上下文.get(键)
        if 上下文 is None:
            上下文=自身.创建上下文(定义,标识,键)
        起始=匹配['role']=='start' and 上下文['start'] is None
        先前=末项(上下文['matches'])
        if 先前 is not None and 先前['event']['seq']>=匹配['event']['seq']:
            raise 对话错误('conversation Context '+键+' received non-appended Match '+str(匹配['event']['seq']))
        if 起始 and len(上下文['matches'])>0:
            raise 对话错误('conversation Context '+键+' received an update before its start Match')
        上下文['matches'].append(匹配)
        if 起始:
            上下文['startSeq']=匹配['event']['seq']
            上下文['start']=匹配
            自身.索引已开始(上下文)
        拥有者=自身.按序号.get(匹配['event']['seq'])
        if 拥有者 is None:
            拥有者=[]
            自身.按序号[匹配['event']['seq']]=拥有者
        拥有者.append(上下文)
        if 起始:
            自身.重放一个(上下文)
        elif 上下文['state'] is not None:
            上下文['state']=要求状态(定义,'update',定义['update'](上下文快照(上下文),匹配))
            上下文['revision']+=1
            自身.已修订.add(上下文)
        自身.标脏(上下文)
        发布=定义.get('publication')
        if 发布 is None:
            return 'immediate'
        return 发布(匹配)

    def 应用待定匹配(自身,待定,受影响):
        '把收集到的匹配按序号并进已有上下文'
        for 键,条目列 in 待定.items():
            if len(条目列)==0:
                continue
            第一=条目列[0]
            上下文=自身.上下文.get(键)
            if 上下文 is None:
                上下文=自身.创建上下文(第一['definition'],第一['id'],键)
            新增=[]
            for 条目 in 条目列:
                if 条目['definition'] is not 上下文['definition'] or 条目['id']!=上下文['id']:
                    raise 对话错误('conversation Context '+键+' received inconsistent Definition identity')
                拥有者=自身.按序号.get(条目['match']['event']['seq'])
                if 拥有者 is None:
                    拥有者=[]
                    自身.按序号[条目['match']['event']['seq']]=拥有者
                拥有者.append(上下文)
                新增.append(条目['match'])
            新增.sort(key=lambda 匹配:匹配['event']['seq'])
            上下文['matches']=合并匹配(上下文['key'],新增,上下文['matches'])
            受影响.add(上下文)
            自身.标脏(上下文)

    def 重放上下文(自身,上下文集):
        '先校正起始，再按起始序号重放'
        自身.刷新起始(上下文集)
        有序=sorted(上下文集,key=lambda 项:项['startSeq'] if 项['startSeq'] is not None else float('inf'))
        for 上下文 in 有序:
            if 上下文['start'] is None:
                上下文['state']=None
                自身.替换依赖(上下文,{})
                上下文['revision']+=1
                自身.已修订.add(上下文)
                自身.标脏(上下文)
                continue
            自身.重放一个(上下文)

    def 刷新起始(自身,上下文集):
        '起始匹配变了就从种类索引里重插'
        变更=set()
        按种类起始={}
        for 上下文 in 上下文集:
            起始=None
            for 匹配 in 上下文['matches']:
                if 匹配['role']=='start':
                    起始=匹配
                    break
            if 起始 is 上下文['start']:
                continue
            上下文['start']=起始
            上下文['startSeq']=None if 起始 is None else 起始['event']['seq']
            变更.add(上下文)
            列=按种类起始.get(上下文['kind'])
            if 列 is None:
                列=[]
                按种类起始[上下文['kind']]=列
            if 起始 is not None:
                列.append(上下文)
        for 种类,起始列 in 按种类起始.items():
            已有=自身.按种类.get(种类,[])
            自身.按种类[种类]=[项 for 项 in 已有 if 项 not in 变更]
            自身.索引多个已开始(种类,起始列)

    def 重放一个(自身,上下文):
        '从起始匹配重算状态，再按顺序 update'
        起始=上下文['start']
        if 起始 is None:
            上下文['state']=None
            return
        if 上下文['matches'][0] is not 起始:
            raise 对话错误('conversation Context '+上下文['key']+' received an update before its start Match')
        依赖={}
        读者=自身.读者于(起始['event']['seq'],依赖)
        上下文['state']=None
        上下文['state']=要求状态(上下文['definition'],'start',上下文['definition']['start'](上下文快照(上下文),起始,读者))
        自身.替换依赖(上下文,依赖)
        下标=1
        while 下标<len(上下文['matches']):
            匹配=上下文['matches'][下标]
            上下文['state']=要求状态(上下文['definition'],'update',上下文['definition']['update'](上下文快照(上下文),匹配))
            下标+=1
        上下文['revision']+=1
        自身.已修订.add(上下文)
        自身.标脏(上下文)

    def 索引目标上下文(自身,上下文):
        '有目标的上下文放进目标集合'
        目标=上下文['definition'].get('target')
        if 目标 is None:
            return
        集合=自身.按目标.get(目标)
        if 集合 is None:
            集合=set()
            自身.按目标[目标]=集合
        集合.add(上下文)

    def 标脏(自身,上下文):
        '活动目标上的脏上下文单独记一份'
        if 上下文 in 自身.脏:
            return
        自身.脏.add(上下文)
        目标=上下文['definition'].get('target')
        if 目标 is None or 目标 not in 自身.活动目标:
            return
        集合=自身.按目标脏.get(目标)
        if 集合 is None:
            集合=set()
            自身.按目标脏[目标]=集合
        集合.add(上下文)

    def 替换依赖(自身,上下文,依赖):
        '先摘旧依赖，再挂上新的'
        for 项 in 上下文['dependencies'].values():
            if 项.get('key') is None:
                continue
            当前=自身.依赖者.get(项['key'])
            if 当前 is not None:
                当前.discard(上下文)
                if len(当前)==0:
                    del 自身.依赖者[项['key']]
        上下文['dependencies']=依赖
        for 项 in 依赖.values():
            if 项.get('key') is None:
                continue
            当前=自身.依赖者.get(项['key'])
            if 当前 is None:
                当前=set()
                自身.依赖者[项['key']]=当前
            当前.add(上下文)

    def 重放已修订依赖者(自身):
        '修订过的上下文，其依赖者整棵重放'
        if len(自身.依赖者)==0:
            return False
        待定=list(自身.已修订)
        受影响=set()
        下标=0
        while 下标<len(待定):
            依赖=待定[下标]
            for 依赖者 in 自身.依赖者.get(依赖['key'],[]):
                if 依赖者 in 受影响:
                    continue
                受影响.add(依赖者)
                待定.append(依赖者)
            下标+=1
        if len(受影响)>0:
            自身.重放上下文(受影响)
        return len(受影响)>0

    def 读者于(自身,序号之前,依赖):
        'start 用来读前一个同种类上下文'
        def 先前(种类):
            '记下依赖，状态还没有就没有前一个'
            前一个=自身.先前上下文(种类,序号之前)
            依赖[种类]={
                'kind':种类,
                'key':None if 前一个 is None else 前一个['key'],
                'revision':None if 前一个 is None else 前一个['revision'],
                'windowGap':前一个 is None and 自身.还有更多,
            }
            if 前一个 is None or 前一个['state'] is None:
                return None
            序号=起始序号(前一个)
            if 序号 is None:
                return None
            return {
                'key':前一个['key'],
                'kind':前一个['kind'],
                'id':前一个['id'],
                'startSeq':序号,
                'state':前一个['state'],
                'matches':前一个['matches'],
            }
        return {'previous':先前}

    def 先前上下文(自身,种类,序号之前):
        '这个序号之前、已经有状态的最近上下文'
        候选=自身.按种类.get(种类,[])
        下标=插入下标(候选,序号之前)-1
        while 下标>=0:
            项=候选[下标]
            if 项['state'] is not None:
                return 项
            下标-=1
        return None

    def 索引已开始(自身,上下文):
        '新发现的起始按序号插进前驱索引'
        序号=上下文['startSeq']
        if 序号 is None:
            return
        候选=自身.按种类.get(上下文['kind'])
        if 候选 is None:
            候选=[]
        先前=末项(候选)
        if 先前 is None or 先前['startSeq']<序号:
            候选.append(上下文)
        else:
            候选.insert(插入下标(候选,序号),上下文)
        自身.按种类[上下文['kind']]=候选

    def 索引多个已开始(自身,种类,新增):
        '一批起始按序号并进种类索引'
        if len(新增)==0:
            return
        排序=sorted(新增,key=lambda 项:项['startSeq'])
        已有=自身.按种类.get(种类,[])
        合并=[]
        前=0
        加=0
        while 前<len(已有) or 加<len(排序):
            左=已有[前] if 前<len(已有) else None
            右=排序[加] if 加<len(排序) else None
            if 右 is None or (左 is not None and 左['startSeq']<右['startSeq']):
                合并.append(左)
                前+=1
            else:
                合并.append(右)
                加+=1
        自身.按种类[种类]=合并

    def 重放依赖(自身):
        '依赖的前一个上下文变了就重放'
        重放过=False
        有序=sorted(
            [项 for 项 in 自身.上下文.values() if 起始序号(项) is not None],
            key=lambda 项:起始序号(项),
        )
        for 上下文 in 有序:
            if 上下文['state'] is None or len(上下文['dependencies'])==0:
                continue
            之前=起始序号(上下文)
            if 之前 is None:
                continue
            变了=False
            for 依赖 in 上下文['dependencies'].values():
                当前=自身.先前上下文(依赖['kind'],之前)
                窗缺口=当前 is None and 自身.还有更多
                当前键=None if 当前 is None else 当前['key']
                当前修订=None if 当前 is None else 当前['revision']
                if 当前键!=依赖.get('key') or 当前修订!=依赖.get('revision') or 窗缺口!=依赖.get('windowGap'):
                    变了=True
                    break
            if 变了:
                自身.重放一个(上下文)
                重放过=True
        return 重放过

    def 刷新匹配位置(自身,变更序号):
        '位置变了的匹配重新取位置'
        受影响=set()
        if len(变更序号)==0:
            return 受影响
        for 序号 in 变更序号:
            for 上下文 in 自身.按序号.get(序号,[]):
                受影响.add(上下文)
        for 上下文 in 受影响:
            起始=上下文['start']
            匹配列=[]
            for 匹配 in 上下文['matches']:
                if 匹配['event']['seq'] not in 变更序号:
                    匹配列.append(匹配)
                    continue
                刷新=dict(匹配)
                刷新['location']=自身.位置.位置于(匹配['event'])
                if 匹配['role']=='start' and 匹配 is 起始:
                    起始=刷新
                匹配列.append(刷新)
            上下文['matches']=匹配列
            上下文['start']=起始
        return 受影响

    def 构建节点(自身,上下文,目标):
        '定义画出这个目标的节点。键和目标必须稳定'
        if 上下文['definition'].get('target')!=目标 or 上下文['definition'].get('buildViewNode') is None:
            return None
        节点=上下文['definition']['buildViewNode'](上下文快照(上下文))
        if 节点 is None:
            return None
        if 节点['key']!=上下文['key']:
            raise 对话错误('conversation Definition "'+上下文['kind']+'" returned unstable key "'+str(节点['key'])+'"; expected "'+上下文['key']+'"')
        if 节点['target']!=目标:
            raise 对话错误('conversation Definition "'+上下文['kind']+'" returned target "'+str(节点['target'])+'" while building "'+目标+'"')
        return 节点

    def 替换视图(自身,视图):
        '用当前全部节点替换这个视图'
        自身.更新视图(视图,True,自身.构建目标节点(视图['target'],自身.按目标.get(视图['target'])),[])

    def 更新视图(自身,视图,替换,节点列,变更回合):
        '替换或增量套用构建器，分组输入不完整就失败'
        构建器=视图['builder'] if 视图['builder'] is not None else 视图['definition']['create']()
        定义=视图['groupDefinition']
        if 定义 is not None and 构建器.get('groupInput') is None:
            raise 对话错误('conversation group target "'+视图['target']+'" requires builder.groupInput()')
        视图['builder']=构建器
        时间线=自身.位置.快照()
        if 替换:
            快照=构建器['replace']({'nodes':节点列,'timeline':时间线,'changedTurns':变更回合})
        else:
            快照=构建器['apply']({'upserts':节点列,'timeline':时间线,'changedTurns':变更回合})
        if 定义 is not None and 构建器.get('groupInput') is not None:
            组上下文=自身.组.get(视图['target'])
            初始=组上下文 is None
            if 组上下文 is None:
                组上下文={'definition':定义,'state':定义['create'](),'store':会话组存储()}
            输入=构建器['groupInput']()
            组上下文['state']=定义['update'](组上下文,输入)
            变更=定义['buildGroups'](组上下文)
            if (初始 or 输入['kind']=='replace') and (变更 is None or 变更.get('entries') is None or 变更['groups']['kind']!='replace'):
                raise 对话错误('conversation group target "'+视图['target']+'" requires complete grouping for replacement input')
            if 变更 is not None:
                组上下文['store'].准备并安装(变更,输入['readNode'])
                自身.待发布组.add(组上下文['store'])
            自身.组[视图['target']]=组上下文
        视图['snapshot']=快照

    def 发布视图(自身,已更新):
        '构建器、组存储和位置数据一起发布'
        变了=len(已更新)>0 or len(自身.待发布组)>0
        存储列=list(自身.待发布组)
        自身.待发布组.clear()
        for 视图 in 已更新:
            构建器=视图['builder']
            if 构建器 is not None and 构建器.get('publish') is not None:
                构建器['publish']()
        for 存储 in 存储列:
            存储.发布()
        自身.位置.发布数据()
        return 变了

    def 构建目标节点(自身,目标,上下文集):
        '这个目标上全部非空节点'
        节点列=[]
        for 上下文 in 上下文集 or []:
            节点=自身.构建节点(上下文,目标)
            上下文['current'][目标]=节点
            if 节点 is not None:
                节点列.append(节点)
        return 节点列

    def 构建目标更新(自身,目标,上下文集):
        '脏上下文的节点。已经物化的节点不能撤回'
        更新=[]
        for 上下文 in 上下文集 or []:
            先前=上下文['current'].get(目标)
            节点=自身.构建节点(上下文,目标)
            if 节点 is None and 先前 is not None:
                raise 对话错误('conversation Definition "'+上下文['kind']+'" withdrew materialized target "'+目标+'"; return the same key with hidden visibility instead')
            上下文['current'][目标]=节点
            if 节点 is not None:
                更新.append(节点)
        return 更新

    def 构建位置数据(自身,上下文,范围,先前):
        '定义发布的位置数据必须用自己的种类和声明的范围'
        if 上下文['definition'].get('buildLocationData') is None:
            return None
        数据=上下文['definition']['buildLocationData'](上下文快照(上下文),范围,先前)
        if 数据 is None:
            return None
        if 数据['kind']!=范围:
            raise 对话错误('conversation Definition "'+上下文['kind']+'" published '+str(数据['kind'])+' data through its '+范围+' scope')
        if 数据['key']!=上下文['kind']:
            raise 对话错误('conversation Definition "'+上下文['kind']+'" published Location data key "'+str(数据['key'])+'"; expected its owned kind')
        回合=数据['turn']
        if not isinstance(回合,int) or isinstance(回合,bool) or 回合<0:
            raise 对话错误('conversation Definition "'+上下文['kind']+'" published invalid turn '+str(回合))
        if 数据['kind']=='step':
            步=数据['step']
            if not isinstance(步,int) or isinstance(步,bool) or 步<0:
                raise 对话错误('conversation Definition "'+上下文['kind']+'" published invalid step '+str(步))
        return 数据

    def 替换位置数据(自身):
        '每个范围整表替换。回合可以读到同一次刷新里的步骤数据'
        for 范围 in 位置范围:
            条目=[]
            for 上下文 in 自身.上下文.values():
                数据=自身.构建位置数据(上下文,范围,上下文['locationData'][范围])
                上下文['locationData'][范围]=数据
                if 数据 is not None:
                    条目.append({'owner':上下文['key'],'data':数据})
            自身.位置.替换数据(条目)

    def 应用脏位置数据(自身):
        '只把脏上下文的位置数据差额写进去'
        变了=False
        for 范围 in 位置范围:
            变更=[]
            for 上下文 in 自身.脏:
                先前=上下文['locationData'][范围]
                下一=自身.构建位置数据(上下文,范围,先前)
                if 先前 is 下一:
                    continue
                上下文['locationData'][范围]=下一
                变更.append({'owner':上下文['key'],'previous':先前,'next':下一})
            if 自身.位置.应用数据(变更):
                变了=True
        return 变了

    def 重置视图构建器(自身):
        '视图定义变了就丢掉对不上的组，并标记整表替换'
        定义列=自身.视图定义.entries()
        目标集=set(项['target'] for 项 in 定义列)
        for 目标,组 in list(自身.组.items()):
            if 目标 not in 目标集 or 自身.组定义.forTarget(目标) is not 组['definition']:
                组['store'].清空()
                自身.待发布组.add(组['store'])
                del 自身.组[目标]
        自身.视图.clear()
        for 定义 in 定义列:
            def 是否活动(快照,定义=定义):
                '拥有者自己的活动判断'
                判断=定义.get('isActive')
                if 判断 is None:
                    return False
                return 判断(快照) is True
            视图={
                'target':定义['target'],
                'definition':定义,
                'groupDefinition':自身.组定义.forTarget(定义['target']),
                'isActive':None if 定义.get('isActive') is None else 是否活动,
                'builder':None,
                'snapshot':None,
            }
            自身.视图[定义['target']]=视图
        自身.待替换=True
