"""调用方身份、工作区授权，以及可见谱系投影。对齐上游 `tool-session-query/src/workspace-access.ts`。"""
from ...模型后端.llm import 装备错误#Harness错误
from .服务边界 import 服务边界#服务边界

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

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

def 信号已中止(信号):#信号是否已中止
    """信号是否已中止。"""
    if 信号 is None:#无信号
        return False#未中止
    return getattr(信号,'aborted',False) is True or getattr(信号,'已中止',False) is True#中英旗标

def 调用方(执行上下文):#从工具执行取出调用方
    """从工具执行取出调用方。"""
    智能体=取字段(执行上下文,'agent')#绑定智能体
    if 智能体 is None:#没有智能体
        raise 装备错误('session query tools require an agent-bound caller','SESSION_QUERY_TOOL_MISSING_AGENT')#拒绝
    return {'id':智能体.session.id,'header':智能体.session.header,'events':智能体.session.events}#冻结身份

def 目标号(参数,调用方):#解析目标会话
    """解析目标会话 id；缺省为调用方自己。"""
    return 取字段(参数,'session_id',调用方['id']) if 取字段(参数,'session_id') is not None else 调用方['id']#缺省自己

def 授权目标(上下文,调用方,目标,信号):#授权单个目标
    """授权单个目标；未授权则抛。"""
    if 目标==调用方['id']:#自己总是可见
        return#通过
    工作目录=取字段(调用方['header'],'cwd')#工作区目录
    if 工作目录 is None:#无cwd
        raise 服务边界['unauthorizedTarget']()#拒绝
    记录们=服务边界['call'](上下文,信号,'target authorization',lambda:上下文.sessionQuery.过滤会话([
        {'kind':'id','values':[目标]},{'kind':'cwd','values':[工作目录]},
    ],信号))#按id加cwd过滤
    if len(记录们)!=1:#不是恰好一条
        raise 服务边界['unauthorizedTarget']()#拒绝

def 记录已授权(记录,调用方):return 头已授权(取字段(记录,'header'),调用方)#记录是否可见

def 头已授权(头,调用方):#头是否对调用方可见
    """头是否对调用方可见。"""
    if 取字段(头,'id')==调用方['id']:#自己
        return 取字段(头,'cwd')==取字段(调用方['header'],'cwd')#cwd还要一致
    return 取字段(调用方['header'],'cwd') is not None and 取字段(头,'cwd')==取字段(调用方['header'],'cwd')#同工作区

def 断言观察目标已授权(调用方,目标,观察头):#断言观察头属于已授权目标
    """断言观察头属于已授权目标。"""
    if 取字段(观察头,'id')!=目标 or not 头已授权(观察头,调用方):#不一致
        raise 服务边界['unauthorizedTarget']()#拒绝

def 授权会话号们(上下文,调用方,号们,信号):#批量授权会话id
    """批量授权会话 id。"""
    唯一=list(dict.fromkeys(号们))#去重
    已授权=set()#结果集
    if 调用方['id'] in 唯一:#自己
        已授权.add(调用方['id'])#收下
    工作目录=取字段(调用方['header'],'cwd')#工作区
    其他=[标识 for 标识 in 唯一 if 标识!=调用方['id']]#去掉自己
    if 工作目录 is None or len(其他)==0:#无cwd或没有别人
        return 已授权#返回
    记录们=服务边界['call'](上下文,信号,'session-id authorization',lambda:上下文.sessionQuery.过滤会话([
        {'kind':'id','values':其他},{'kind':'cwd','values':[工作目录]},
    ],信号))#过滤
    请求集=set(其他)#请求集合
    for 记录 in 记录们:#逐条验收
        标识=取字段(取字段(记录,'header'),'id')#会话id
        if 标识 in 请求集 and 记录已授权(记录,调用方):#确实被请求且可见
            已授权.add(标识)#收下
    return 已授权#返回

def 读取标题们(上下文,调用方,号们,信号):#批量读标题
    """批量读标题。"""
    结果={}#标题表
    观察们=服务边界['call'](上下文,信号,'title observation',lambda:上下文.sessionQuery.读取标题快照们(号们,信号))#观察
    for 观察 in 观察们:#逐条
        if 取字段(观察,'status')=='rejected':#失败
            结果[取字段(观察,'sessionId')]=不可用标题(上下文,取字段(观察,'reason'))#不可用标题
            continue#下一项
        断言观察目标已授权(调用方,取字段(观察,'sessionId'),取字段(取字段(观察,'value'),'session'))#再验头
        标题=取字段(取字段(取字段(观察,'value'),'title'),'title')#嵌套标题
        结果[取字段(观察,'sessionId')]={'text':标题 if 标题 is not None else 'untitled'}#标题视图
    return 结果#完整标题表

def 读取标题(上下文,调用方,标识,信号):return 读取标题们(上下文,调用方,[标识],信号)[标识]#读单标题

def 不可用标题(上下文,错误):#把失败收成不可用标题
    """把失败收成不可用标题。"""
    消毒=服务边界['sanitizeError'](上下文,'title observation item',错误)#消毒
    if 取字段(消毒,'code')=='SESSION_QUERY_TOOL_UNAUTHORIZED':#未授权仍抛
        raise 消毒#抛出
    return {'text':'untitled','unavailableCode':取字段(消毒,'code')}#untitled加码

def 授权后代(节点们,调用方):#投影可见后代树
    """投影可见后代树，洞为 None。"""
    结果=[]#根层
    栈=[{'node':节点,'target':结果,'depth':0} for 节点 in reversed(节点们)]#压栈
    while len(栈)>0:#迭代
        帧=栈.pop()#弹出
        节点=取字段(帧,'node')#源节点
        if not 记录已授权(取字段(节点,'session'),调用方):#不可见
            取字段(帧,'target').append(None)#留洞
            continue#不进子树
        投影={'record':取字段(节点,'session'),'descendants':[]}#可见节点
        取字段(帧,'target').append(投影)#写入
        for 子 in reversed(取字段(节点,'descendants',[])):#子反向压栈
            栈.append({'node':子,'target':投影['descendants'],'depth':取字段(帧,'depth')+1})#子帧
    return 结果#根层

def 遍历后代(节点们):#前序遍历已授权后代
    """前序遍历后代树，带深度。"""
    栈=[{'node':节点,'depth':0} for 节点 in reversed(节点们)]#压栈
    while len(栈)>0:#迭代
        当前=栈.pop()#弹出
        yield 当前#交给调用方
        if 当前['node'] is None:#洞没有子
            continue#跳过
        for 子 in reversed(当前['node']['descendants']):#子反向压栈
            栈.append({'node':子,'depth':当前['depth']+1})#子访

def 后代号们(节点们):#收集可见后代id
    """收集可见后代 id。"""
    号们=[]#结果
    for 项 in 遍历后代(节点们):#遍历
        if 项['node'] is not None:#跳过洞
            号们.append(取字段(取字段(项['node']['record'],'header'),'id'))#收下
    return 号们#id列表

def 标题文本(视图):#渲染标题文本
    """渲染标题文本。"""
    if 取字段(视图,'unavailableCode') is None:#可用
        return 取字段(视图,'text')#原文
    return f"{取字段(视图,'text')} (title unavailable: {取字段(视图,'unavailableCode')})"#附码

工作区访问={
    'callerOf':调用方,'targetId':目标号,'authorizeTarget':授权目标,
    'recordAuthorized':记录已授权,'assertObservedTargetAuthorized':断言观察目标已授权,
    'authorizeSessionIds':授权会话号们,'readTitles':读取标题们,'readTitle':读取标题,
    'authorizeDescendants':授权后代,'visitDescendants':遍历后代,'descendantIds':后代号们,'titleText':标题文本,
}#对外出口
