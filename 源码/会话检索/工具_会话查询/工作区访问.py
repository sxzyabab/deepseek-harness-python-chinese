"""调用方身份、工作区授权，以及可见谱系投影。"""
from ...模型后端.llm import 装备错误#Harness错误
from .服务边界 import 服务边界#服务边界

def 调用方(执行上下文):
    """从工具执行取出调用方。"""
    智能体=执行上下文['agent'] if 'agent' in 执行上下文 else None#绑定智能体
    if 智能体 is None:#没有智能体
        raise 装备错误('session query tools require an agent-bound caller','SESSION_QUERY_TOOL_MISSING_AGENT')#拒绝
    return {'id':智能体.session.id,'header':智能体.session.header,'events':智能体.session.events}#冻结身份

def 目标号(参数,调用方):
    """解析目标会话 id；缺省为调用方自己。"""
    if 'session_id' in 参数 and 参数['session_id'] is not None:#显式目标
        return 参数['session_id']#目标
    return 调用方['id']#缺省自己

def 授权目标(上下文,调用方,目标,信号):
    """授权单个目标；未授权则抛。"""
    if 目标==调用方['id']:#自己总是可见
        return#通过
    头=调用方['header']#调用方头
    工作目录=头['cwd'] if 'cwd' in 头 else None#工作区目录
    if 工作目录 is None:#无cwd
        raise 服务边界['unauthorizedTarget']()#拒绝
    def 执行过滤():
        """按 id 加 cwd 过滤。"""
        return 上下文.sessionQuery.过滤会话([
            {'kind':'id','values':[目标]},{'kind':'cwd','values':[工作目录]},
        ],信号)#过滤
    记录列表=服务边界['call'](上下文,信号,'target authorization',执行过滤)#过滤
    if len(记录列表)!=1:#不是恰好一条
        raise 服务边界['unauthorizedTarget']()#拒绝

def 记录已授权(记录,调用方):
    """记录是否可见。"""
    return 头已授权(记录['header'],调用方)#记录是否可见

def 头已授权(头,调用方):
    """头是否对调用方可见。"""
    调用头=调用方['header']#调用方头
    调用目录=调用头['cwd'] if 'cwd' in 调用头 else None#调用方目录
    if 头['id']==调用方['id']:#自己
        return (头['cwd'] if 'cwd' in 头 else None)==调用目录#cwd还要一致
    return 调用目录 is not None and (头['cwd'] if 'cwd' in 头 else None)==调用目录#同工作区

def 校验观察目标已授权(调用方,目标,观察头):
    """断言观察头属于已授权目标。"""
    if 观察头['id']!=目标 or not 头已授权(观察头,调用方):#不一致
        raise 服务边界['unauthorizedTarget']()#拒绝

def 授权会话号列表(上下文,调用方,号列表,信号):
    """批量授权会话 id。"""
    唯一=list(dict.fromkeys(号列表))#去重
    已授权=set()#结果集
    if 调用方['id'] in 唯一:#自己
        已授权.add(调用方['id'])#收下
    调用头=调用方['header']#头
    工作目录=调用头['cwd'] if 'cwd' in 调用头 else None#工作区
    其他=[标识 for 标识 in 唯一 if 标识!=调用方['id']]#去掉自己
    if 工作目录 is None or len(其他)==0:#无cwd或没有别人
        return 已授权#返回
    def 执行过滤():
        """按 id 加 cwd 过滤。"""
        return 上下文.sessionQuery.过滤会话([
            {'kind':'id','values':其他},{'kind':'cwd','values':[工作目录]},
        ],信号)#过滤
    记录列表=服务边界['call'](上下文,信号,'session-id authorization',执行过滤)#过滤
    请求集=set(其他)#请求集合
    for 记录 in 记录列表:#逐条验收
        标识=记录['header']['id']#会话id
        if 标识 in 请求集 and 记录已授权(记录,调用方):#确实被请求且可见
            已授权.add(标识)#收下
    return 已授权#返回

def 读取标题表(上下文,调用方,号列表,信号):
    """批量读标题。"""
    结果={}#标题表
    def 执行观察():
        """读标题快照。"""
        return 上下文.sessionQuery.批量读取标题快照(号列表,信号)#观察
    观察列表=服务边界['call'](上下文,信号,'title observation',执行观察)#观察
    for 观察 in 观察列表:#逐条
        if 观察['status']=='rejected':
            结果[观察['sessionId']]=不可用标题(上下文,观察['reason'])#不可用标题
            continue#下一项
        值=观察['value']#成功值
        校验观察目标已授权(调用方,观察['sessionId'],值['session'])#再验头
        标题快照=值['title'] if 'title' in 值 else None#嵌套标题
        标题=标题快照['title'] if isinstance(标题快照,dict) and 'title' in 标题快照 else None#文本
        结果[观察['sessionId']]={'text':标题 if 标题 is not None else 'untitled'}#标题视图
    return 结果#完整标题表

def 读取标题(上下文,调用方,标识,信号):
    """读单标题。"""
    return 读取标题表(上下文,调用方,[标识],信号)[标识]#读单标题

def 不可用标题(上下文,错误):
    """把失败收成不可用标题。"""
    消毒=服务边界['sanitizeError'](上下文,'title observation item',错误)#消毒
    if 消毒.code=='SESSION_QUERY_TOOL_UNAUTHORIZED':#未授权仍抛
        raise 消毒#抛出
    return {'text':'untitled','unavailableCode':消毒.code}#untitled加码

def 授权后代(节点列表,调用方):
    """投影可见后代树，洞为 None。"""
    结果=[]#根层
    栈=[{'node':节点,'target':结果,'depth':0} for 节点 in reversed(节点列表)]#压栈
    while len(栈)>0:#迭代
        帧=栈.pop()#弹出
        节点=帧['node']#源节点
        if not 记录已授权(节点['session'],调用方):#不可见
            帧['target'].append(None)#留洞
            continue#不进子树
        投影={'record':节点['session'],'descendants':[]}#可见节点
        帧['target'].append(投影)#写入
        子列表=节点['descendants'] if 'descendants' in 节点 else []#子
        for 子 in reversed(子列表):#子反向压栈
            栈.append({'node':子,'target':投影['descendants'],'depth':帧['depth']+1})#子帧
    return 结果#根层

def 遍历后代(节点列表):
    """前序遍历后代树，带深度。"""
    栈=[{'node':节点,'depth':0} for 节点 in reversed(节点列表)]#压栈
    while len(栈)>0:#迭代
        当前=栈.pop()#弹出
        yield 当前#交给调用方
        if 当前['node'] is None:#洞没有子
            continue#跳过
        for 子 in reversed(当前['node']['descendants']):#子反向压栈
            栈.append({'node':子,'depth':当前['depth']+1})#子访

def 后代号列表(节点列表):
    """收集可见后代 id。"""
    号列表=[]#结果
    for 项 in 遍历后代(节点列表):#遍历
        if 项['node'] is not None:#跳过洞
            号列表.append(项['node']['record']['header']['id'])#收下
    return 号列表#id列表

def 标题文本(视图):
    """渲染标题文本。"""
    if 'unavailableCode' not in 视图 or 视图['unavailableCode'] is None:#可用
        return 视图['text']#原文
    return 视图['text']+' (title unavailable: '+str(视图['unavailableCode'])+')'#附码

工作区访问={
    'callerOf':调用方,'targetId':目标号,'authorizeTarget':授权目标,
    'recordAuthorized':记录已授权,'assertObservedTargetAuthorized':校验观察目标已授权,
    'authorizeSessionIds':授权会话号列表,'readTitles':读取标题表,'readTitle':读取标题,
    'authorizeDescendants':授权后代,'visitDescendants':遍历后代,'descendantIds':后代号列表,'titleText':标题文本,
}#对外出口
