"""盖在会话检索服务能力上的工具操作编排。对齐上游 `tool-session-query/src/operations.ts`。"""
from ...模型后端.llm import 装备错误#Harness错误
from ..会话查询 import 会话查询错误#检索错误
from .入参 import 工具入参#参数归一化
from .展示 import 展示#文本渲染
from .服务边界 import 服务边界#服务边界
from .工作区访问 import 工作区访问#工作区授权

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 信号已中止(信号):#信号是否已中止
    """信号是否已中止。"""
    if 信号 is None:#无信号
        return False#未中止
    return getattr(信号,'aborted',False) is True or getattr(信号,'已中止',False) is True#中英旗标

def 信号抛出若已中止(信号):#已取消则抛出
    """已取消则抛出。"""
    if 信号已中止(信号):#已中止
        raise 会话查询错误('session-search aborted','SESSION_QUERY_ABORTED')#取消

def 是否thenable(值):#判定可等待对象
    """判定值是否可等待。"""
    if 值 is None:#空不是
        return False#不是
    return callable(getattr(值,'wait',None)) or callable(getattr(值,'等待',None))#Future或thenable

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        if callable(getattr(值,'wait',None)):#Future风格
            return 值.wait()#等待
        return 值.等待()#thenable
    return 值#同步值

def 执行会话搜索(上下文,参数,执行上下文,最大结果数):#执行跨会话检索
    """执行跨会话检索。"""
    调用方=工作区访问['callerOf'](执行上下文)#取调用方
    工作目录=取字段(调用方['header'],'cwd')#工作区目录
    if 工作目录 is None:#无工作区
        raise 装备错误('cross-session search is unavailable because the caller session has no workspace','SESSION_QUERY_TOOL_UNAUTHORIZED')#拒绝
    查询=工具入参['normalizeQuery'](取字段(参数,'query'))#归一化查询
    会话过滤器=工具入参['buildSessionFilters'](参数)#会话过滤
    事件过滤器=工具入参['buildEventFilters']({
        'seqFrom':取字段(参数,'event_seq_from'),'seqTo':取字段(参数,'event_seq_to'),
        'timeFrom':取字段(参数,'event_time_from'),'timeTo':取字段(参数,'event_time_to'),
        'eventTypes':取字段(参数,'event_types'),'surfaces':取字段(参数,'event_surfaces'),
    })#事件过滤
    请求父们=工具入参['materializeParentSessionIds'](取字段(参数,'parent_session_ids'))#父id
    if 请求父们 is not None or 取字段(参数,'include_root_sessions') is True:#要按父过滤
        已授权父们=工作区访问['authorizeSessionIds'](上下文,调用方,请求父们 or [],取字段(执行上下文,'signal')) if 请求父们 is not None else set()#可见父
        父值=list(已授权父们) if 请求父们 is not None else []#可见父id
        if 取字段(参数,'include_root_sessions') is True:#包含根
            父值.append(None)#根会话
        if len(父值)==0:#全被滤掉
            return 展示['formatEmptySessionSearch']()#空
        会话过滤器.append({'kind':'parent','values':父值})#加上父过滤
    会话过滤器.append({'kind':'cwd','values':[工作目录]})#强制本工作区
    信号=取字段(执行上下文,'signal')#取消信号
    集合=解开(收集页(最大结果数,信号,lambda 游标:服务边界['call'](上下文,信号,'session search',lambda:上下文.sessionQuery.搜索会话({
        'query':查询,'sessionFilters':会话过滤器,'eventFilters':事件过滤器,**({} if 游标 is None else {'cursor':游标}),
    },{'signal':信号})),lambda 命中:取字段(取字段(命中,'header'),'id')!=调用方['id'] and 工作区访问['recordAuthorized'](命中,调用方)))#翻页收集
    父号们=[取字段(取字段(命中,'header'),'parentSession') for 命中 in 集合['items'] if 取字段(取字段(命中,'header'),'parentSession') is not None]#父id
    已授权父们=工作区访问['authorizeSessionIds'](上下文,调用方,父号们,信号)#可见父
    标题表=工作区访问['readTitles'](上下文,调用方,[取字段(取字段(命中,'header'),'id') for 命中 in 集合['items']],信号)#读标题
    return 展示['formatSessionSearch'](集合,标题表,已授权父们)#渲染

def 执行事件搜索(上下文,参数,执行上下文,最大结果数):#执行会话内事件检索
    """执行会话内事件检索。"""
    调用方=工作区访问['callerOf'](执行上下文)#取调用方
    会话号=工作区访问['targetId'](参数,调用方)#解析目标
    工作区访问['authorizeTarget'](上下文,调用方,会话号,取字段(执行上下文,'signal'))#授权
    查询=工具入参['normalizeQuery'](取字段(参数,'query'))#归一化查询
    区间=工具入参['sequenceRange'](取字段(参数,'seq_from'),取字段(参数,'seq_to'))#序号区间
    if 会话号==调用方['id']:#搜当前会话
        步骤起点=next((事件 for 事件 in reversed(调用方['events']) if 取字段(事件,'type')=='step/start'),None)#当前步骤
        if 步骤起点 is None:#没有步骤
            raise 装备错误('current-session search requires an active step boundary','SESSION_QUERY_TOOL_NO_CURRENT_STEP')#拒绝
        区间['to']=min(区间.get('to',2**53-1),取字段(步骤起点,'seq')-1)#不搜当前步骤及之后
    标题=工作区访问['readTitle'](上下文,调用方,会话号,取字段(执行上下文,'signal'))#读标题
    if 区间.get('from') is not None and 区间.get('to') is not None and 区间['from']>区间['to']:#空区间
        return 展示['formatEventSearch'](会话号,标题,{'items':[],'capped':False})#空结果
    过滤器=工具入参['buildEventFilters']({
        'seqFrom':区间.get('from'),'seqTo':区间.get('to'),
        'timeFrom':取字段(参数,'time_from'),'timeTo':取字段(参数,'time_to'),
        'eventTypes':取字段(参数,'event_types'),'surfaces':取字段(参数,'surfaces'),
    })#事件过滤
    信号=取字段(执行上下文,'signal')#取消信号
    集合=解开(收集页(最大结果数,信号,lambda 游标:(_页:=服务边界['call'](上下文,信号,'event search',lambda:上下文.sessionQuery.搜索事件({
        'sessionId':会话号,'query':查询,'filters':过滤器,**({} if 游标 is None else {'cursor':游标}),
    },{'signal':信号})),工作区访问['assertObservedTargetAuthorized'](调用方,会话号,取字段(_页,'session')),_页)[2],lambda _:True))#事件页
    return 展示['formatEventSearch'](会话号,标题,集合)#渲染

def 执行会话谱系(上下文,参数,执行上下文):#执行会话谱系追踪
    """执行会话谱系追踪。"""
    调用方=工作区访问['callerOf'](执行上下文)#取调用方
    会话号=工作区访问['targetId'](参数,调用方)#解析目标
    信号=取字段(执行上下文,'signal')#取消信号
    工作区访问['authorizeTarget'](上下文,调用方,会话号,信号)#授权
    谱系=服务边界['call'](上下文,信号,'session lineage trace',lambda:上下文.sessionQuery.追踪会话谱系(会话号,信号))#追踪
    工作区访问['assertObservedTargetAuthorized'](调用方,会话号,取字段(取字段(谱系,'target'),'header'))#再验头
    祖先们=[]#可见祖先
    祖先边界=False#边界
    for 祖先 in 取字段(谱系,'ancestors'):#由近到远
        if not 工作区访问['recordAuthorized'](祖先,调用方):#不可见
            祖先边界=True#记下边界
            break#停止
        祖先们.append(祖先)#收下
    if len(祖先们)==len(取字段(谱系,'ancestors')) and not 取字段(谱系,'complete'):#语料外
        祖先边界=True#也算边界
    后代们=工作区访问['authorizeDescendants'](取字段(谱系,'descendants'),调用方)#投影后代
    可见号们=[取字段(取字段(谱系,'target'),'header')['id'],*[取字段(取字段(记录,'header'),'id') for 记录 in 祖先们],*工作区访问['descendantIds'](后代们)]#要读标题
    标题表=工作区访问['readTitles'](上下文,调用方,可见号们,信号)#批量读标题
    return 展示['formatSessionTrace'](谱系,祖先们,祖先边界,后代们,标题表)#渲染

def 执行事件追踪(上下文,参数,执行上下文):#执行事件关系追踪
    """执行事件关系追踪。"""
    工具入参['assertNonNegativeSafeInteger']('seq',取字段(参数,'seq'))#校验序号
    调用方=工作区访问['callerOf'](执行上下文)#取调用方
    会话号=工作区访问['targetId'](参数,调用方)#解析目标
    信号=取字段(执行上下文,'signal')#取消信号
    工作区访问['authorizeTarget'](上下文,调用方,会话号,信号)#授权
    追踪=服务边界['call'](上下文,信号,'event trace',lambda:上下文.sessionQuery.追踪事件关系({'sessionId':会话号,'seq':取字段(参数,'seq')},信号))#追踪
    工作区访问['assertObservedTargetAuthorized'](调用方,会话号,取字段(追踪,'session'))#再验头
    标题=工作区访问['readTitle'](上下文,调用方,会话号,信号)#读标题
    return 展示['formatEventTrace'](会话号,标题,追踪)#渲染

def 执行事件读取(上下文,参数,执行上下文):#执行带邻域的事件读取
    """执行带邻域的事件读取。"""
    工具入参['assertNonNegativeSafeInteger']('seq',取字段(参数,'seq'))#校验序号
    if 取字段(参数,'before') is not None:#前窗口
        工具入参['assertNonNegativeSafeInteger']('before',取字段(参数,'before'))#校验
    if 取字段(参数,'after') is not None:#后窗口
        工具入参['assertNonNegativeSafeInteger']('after',取字段(参数,'after'))#校验
    调用方=工作区访问['callerOf'](执行上下文)#取调用方
    会话号=工作区访问['targetId'](参数,调用方)#解析目标
    信号=取字段(执行上下文,'signal')#取消信号
    工作区访问['authorizeTarget'](上下文,调用方,会话号,信号)#授权
    窗口=服务边界['call'](上下文,信号,'event read',lambda:上下文.sessionQuery.读取事件({
        'sessionId':会话号,'seq':取字段(参数,'seq'),
        **({} if 取字段(参数,'before') is None else {'before':取字段(参数,'before')}),
        **({} if 取字段(参数,'after') is None else {'after':取字段(参数,'after')}),
    },信号))#读取
    工作区访问['assertObservedTargetAuthorized'](调用方,会话号,取字段(窗口,'session'))#再验头
    标题=工作区访问['readTitle'](上下文,调用方,会话号,信号)#读标题
    return 展示['formatEventRead'](会话号,标题,窗口)#渲染

def 收集页(最大结果数,信号,请求,接受):#翻页收集直到上限或末页
    """翻页收集直到上限或末页。"""
    条目们=[]#已收条目
    已见=set()#已见游标
    游标=None#当前续页
    while True:#直到末页或封顶
        信号抛出若已中止(信号)#每页前检查取消
        页=解开(请求(游标))#取一页
        信号抛出若已中止(信号)#返回后检查取消
        for 项 in 取字段(页,'items',[]):#逐条
            if not 接受(项):#过滤掉
                continue#跳过
            if len(条目们)==最大结果数:#已满
                return {'items':条目们,'capped':True}#封顶返回
            条目们.append(项)#收下
        下一游标=取字段(页,'nextCursor')#下一页游标
        if 下一游标 is None:#末页
            return {'items':条目们,'capped':False}#返回
        if 下一游标 in 已见:#游标循环
            raise 会话查询错误('session-search provider repeated a continuation cursor','SESSION_QUERY_INVALID_CURSOR')#非法游标
        已见.add(下一游标)#记下
        游标=下一游标#下一页

操作={
    'executeSessionSearch':执行会话搜索,'executeEventSearch':执行事件搜索,
    'executeSessionTrace':执行会话谱系,'executeEventTrace':执行事件追踪,'executeEventRead':执行事件读取,
}#对外出口
