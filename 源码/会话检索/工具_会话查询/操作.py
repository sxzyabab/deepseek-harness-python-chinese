"""盖在会话检索服务能力上的工具操作编排。"""
from ...模型后端.llm import 装备错误#Harness错误
from ..会话查询 import 会话查询错误#检索错误
from ..会话查询.配置 import 若已中止则抛出#中止
from .入参 import 工具入参#参数归一化
from .呈现 import 呈现#文本渲染
from .服务边界 import 服务边界#服务边界
from .工作区访问 import 工作区访问#工作区授权

def 执行会话搜索(上下文,参数,执行上下文,最大结果数):
    """执行跨会话检索。"""
    调用方=工作区访问['callerOf'](执行上下文)#取调用方
    工作目录=调用方['header']['cwd'] if 'cwd' in 调用方['header'] else None#工作区目录
    if 工作目录 is None:#无工作区
        raise 装备错误('cross-session search is unavailable because the caller session has no workspace','SESSION_QUERY_TOOL_UNAUTHORIZED')#拒绝
    查询=工具入参['normalizeQuery'](参数['query'])#归一化查询
    会话过滤器=工具入参['buildSessionFilters'](参数)#会话过滤
    事件过滤器=工具入参['buildEventFilters']({
        'seqFrom':参数['event_seq_from'] if 'event_seq_from' in 参数 else None,
        'seqTo':参数['event_seq_to'] if 'event_seq_to' in 参数 else None,
        'timeFrom':参数['event_time_from'] if 'event_time_from' in 参数 else None,
        'timeTo':参数['event_time_to'] if 'event_time_to' in 参数 else None,
        'eventTypes':参数['event_types'] if 'event_types' in 参数 else None,
        'surfaces':参数['event_surfaces'] if 'event_surfaces' in 参数 else None,
    })#事件过滤
    请求父列表=工具入参['materializeParentSessionIds'](参数['parent_session_ids'] if 'parent_session_ids' in 参数 else None)#父id
    if 请求父列表 is not None or ('include_root_sessions' in 参数 and 参数['include_root_sessions'] is True):#要按父过滤
        信号=执行上下文['signal'] if 'signal' in 执行上下文 else None#取消信号
        已授权父集合=工作区访问['authorizeSessionIds'](上下文,调用方,请求父列表 if 请求父列表 is not None else [],信号) if 请求父列表 is not None else set()#可见父
        父值=list(已授权父集合) if 请求父列表 is not None else []#可见父id
        if 'include_root_sessions' in 参数 and 参数['include_root_sessions'] is True:#包含根
            父值.append(None)#根会话
        if len(父值)==0:#全被滤掉
            return 呈现['formatEmptySessionSearch']()#空
        会话过滤器.append({'kind':'parent','values':父值})#加上父过滤
    会话过滤器.append({'kind':'cwd','values':[工作目录]})#强制本工作区
    信号=执行上下文['signal'] if 'signal' in 执行上下文 else None#取消信号
    def 请求页(游标):
        """取一页会话检索。"""
        请求={'query':查询,'sessionFilters':会话过滤器,'eventFilters':事件过滤器}#请求
        if 游标 is not None:#续页
            请求['cursor']=游标#游标
        def 执行搜索():
            """调用检索引擎。"""
            return 上下文.sessionQuery.搜索会话(请求,{'signal':信号})#搜索
        return 服务边界['call'](上下文,信号,'session search',执行搜索)#边界
    def 接受命中(命中):
        """排除调用方且工作区授权。"""
        return 命中['header']['id']!=调用方['id'] and 工作区访问['recordAuthorized'](命中,调用方)#过滤
    集合=收集页(最大结果数,信号,请求页,接受命中)#翻页收集
    父号列表=[命中['header']['parentSession'] for 命中 in 集合['items'] if 'parentSession' in 命中['header'] and 命中['header']['parentSession'] is not None]#父id
    已授权父集合=工作区访问['authorizeSessionIds'](上下文,调用方,父号列表,信号)#可见父
    标题表=工作区访问['readTitles'](上下文,调用方,[命中['header']['id'] for 命中 in 集合['items']],信号)#读标题
    return 呈现['formatSessionSearch'](集合,标题表,已授权父集合)#渲染

def 执行事件搜索(上下文,参数,执行上下文,最大结果数):
    """执行会话内事件检索。"""
    调用方=工作区访问['callerOf'](执行上下文)#取调用方
    会话号=工作区访问['targetId'](参数,调用方)#解析目标
    信号=执行上下文['signal'] if 'signal' in 执行上下文 else None#取消信号
    工作区访问['authorizeTarget'](上下文,调用方,会话号,信号)#授权
    查询=工具入参['normalizeQuery'](参数['query'])#归一化查询
    区间=工具入参['sequenceRange'](参数['seq_from'] if 'seq_from' in 参数 else None,参数['seq_to'] if 'seq_to' in 参数 else None)#序号区间
    if 会话号==调用方['id']:#搜当前会话
        步骤起点=None#当前步骤
        for 事件 in reversed(调用方['events']):#从新到旧
            if 事件['type']=='step/start':#步骤开始
                步骤起点=事件#记下
                break#停
        if 步骤起点 is None:#没有步骤
            raise 装备错误('current-session search requires an active step boundary','SESSION_QUERY_TOOL_NO_CURRENT_STEP')#拒绝
        上限=区间['to'] if 'to' in 区间 else 2**53-1#原上界
        区间['to']=min(上限,步骤起点['seq']-1)#不搜当前步骤及之后
    标题=工作区访问['readTitle'](上下文,调用方,会话号,信号)#读标题
    if 'from' in 区间 and 'to' in 区间 and 区间['from']>区间['to']:#空区间
        return 呈现['formatEventSearch'](会话号,标题,{'items':[],'capped':False})#空结果
    过滤器=工具入参['buildEventFilters']({
        'seqFrom':区间['from'] if 'from' in 区间 else None,
        'seqTo':区间['to'] if 'to' in 区间 else None,
        'timeFrom':参数['time_from'] if 'time_from' in 参数 else None,
        'timeTo':参数['time_to'] if 'time_to' in 参数 else None,
        'eventTypes':参数['event_types'] if 'event_types' in 参数 else None,
        'surfaces':参数['surfaces'] if 'surfaces' in 参数 else None,
    })#事件过滤
    def 请求页(游标):
        """取一页事件检索。"""
        请求={'sessionId':会话号,'query':查询,'filters':过滤器}#请求
        if 游标 is not None:#续页
            请求['cursor']=游标#游标
        def 执行搜索():
            """调用检索引擎。"""
            return 上下文.sessionQuery.搜索事件(请求,{'signal':信号})#搜索
        页=服务边界['call'](上下文,信号,'event search',执行搜索)#边界
        工作区访问['assertObservedTargetAuthorized'](调用方,会话号,页['session'])#再验头
        return 页#页
    def 全收(项):
        """事件页不过滤条目。"""
        return True#全收
    集合=收集页(最大结果数,信号,请求页,全收)#事件页
    return 呈现['formatEventSearch'](会话号,标题,集合)#渲染

def 执行会话谱系(上下文,参数,执行上下文):
    """执行会话谱系追踪。"""
    调用方=工作区访问['callerOf'](执行上下文)#取调用方
    会话号=工作区访问['targetId'](参数,调用方)#解析目标
    信号=执行上下文['signal'] if 'signal' in 执行上下文 else None#取消信号
    工作区访问['authorizeTarget'](上下文,调用方,会话号,信号)#授权
    def 执行追踪():
        """追踪谱系。"""
        return 上下文.sessionQuery.追踪会话谱系(会话号,信号)#追踪
    谱系=服务边界['call'](上下文,信号,'session lineage trace',执行追踪)#追踪
    工作区访问['assertObservedTargetAuthorized'](调用方,会话号,谱系['target']['header'])#再验头
    祖先列表=[]#可见祖先
    祖先边界=False#边界
    for 祖先 in 谱系['ancestors']:#由近到远
        if not 工作区访问['recordAuthorized'](祖先,调用方):#不可见
            祖先边界=True#记下边界
            break#停止
        祖先列表.append(祖先)#收下
    if len(祖先列表)==len(谱系['ancestors']) and not 谱系['complete']:#语料外
        祖先边界=True#也算边界
    后代列表=工作区访问['authorizeDescendants'](谱系['descendants'],调用方)#投影后代
    可见号列表=[谱系['target']['header']['id'],*[记录['header']['id'] for 记录 in 祖先列表],*工作区访问['descendantIds'](后代列表)]#要读标题
    标题表=工作区访问['readTitles'](上下文,调用方,可见号列表,信号)#批量读标题
    return 呈现['formatSessionTrace'](谱系,祖先列表,祖先边界,后代列表,标题表)#渲染

def 执行事件追踪(上下文,参数,执行上下文):
    """执行事件关系追踪。"""
    工具入参['assertNonNegativeSafeInteger']('seq',参数['seq'])#校验序号
    调用方=工作区访问['callerOf'](执行上下文)#取调用方
    会话号=工作区访问['targetId'](参数,调用方)#解析目标
    信号=执行上下文['signal'] if 'signal' in 执行上下文 else None#取消信号
    工作区访问['authorizeTarget'](上下文,调用方,会话号,信号)#授权
    def 执行追踪():
        """追踪事件。"""
        return 上下文.sessionQuery.追踪事件关系({'sessionId':会话号,'seq':参数['seq']},信号)#追踪
    追踪=服务边界['call'](上下文,信号,'event trace',执行追踪)#追踪
    工作区访问['assertObservedTargetAuthorized'](调用方,会话号,追踪['session'])#再验头
    标题=工作区访问['readTitle'](上下文,调用方,会话号,信号)#读标题
    return 呈现['formatEventTrace'](会话号,标题,追踪)#渲染

def 执行事件读取(上下文,参数,执行上下文):
    """执行带邻域的事件读取。"""
    工具入参['assertNonNegativeSafeInteger']('seq',参数['seq'])#校验序号
    if 'before' in 参数 and 参数['before'] is not None:#前窗口
        工具入参['assertNonNegativeSafeInteger']('before',参数['before'])#校验
    if 'after' in 参数 and 参数['after'] is not None:#后窗口
        工具入参['assertNonNegativeSafeInteger']('after',参数['after'])#校验
    调用方=工作区访问['callerOf'](执行上下文)#取调用方
    会话号=工作区访问['targetId'](参数,调用方)#解析目标
    信号=执行上下文['signal'] if 'signal' in 执行上下文 else None#取消信号
    工作区访问['authorizeTarget'](上下文,调用方,会话号,信号)#授权
    请求={'sessionId':会话号,'seq':参数['seq']}#读取请求
    if 'before' in 参数 and 参数['before'] is not None:#前窗口
        请求['before']=参数['before']#前
    if 'after' in 参数 and 参数['after'] is not None:#后窗口
        请求['after']=参数['after']#后
    def 执行读取():
        """读取事件窗口。"""
        return 上下文.sessionQuery.读取事件(请求,信号)#读取
    窗口=服务边界['call'](上下文,信号,'event read',执行读取)#读取
    工作区访问['assertObservedTargetAuthorized'](调用方,会话号,窗口['session'])#再验头
    标题=工作区访问['readTitle'](上下文,调用方,会话号,信号)#读标题
    return 呈现['formatEventRead'](会话号,标题,窗口)#渲染

def 收集页(最大结果数,信号,请求,接受):
    """翻页收集直到上限或末页。"""
    条目列表=[]#已收条目
    已见=set()#已见游标
    游标=None#当前续页
    while True:#直到末页或封顶
        若已中止则抛出(信号)#每页前检查取消
        页=请求(游标)#取一页
        若已中止则抛出(信号)#返回后检查取消
        项列表=页['items'] if 'items' in 页 else []#条目
        for 项 in 项列表:#逐条
            if not 接受(项):#过滤掉
                continue#跳过
            if len(条目列表)==最大结果数:#已满
                return {'items':条目列表,'capped':True}#封顶返回
            条目列表.append(项)#收下
        下一游标=页['nextCursor'] if 'nextCursor' in 页 else None#下一页游标
        if 下一游标 is None:#末页
            return {'items':条目列表,'capped':False}#返回
        if 下一游标 in 已见:#游标循环
            raise 会话查询错误('session-search provider repeated a continuation cursor','SESSION_QUERY_INVALID_CURSOR')#非法游标
        已见.add(下一游标)#记下
        游标=下一游标#下一页

操作={
    'executeSessionSearch':执行会话搜索,'executeEventSearch':执行事件搜索,
    'executeSessionTrace':执行会话谱系,'executeEventTrace':执行事件追踪,'executeEventRead':执行事件读取,
}#对外出口
