"""面向模型的目标工具在执行时的权限检查。"""
from ...模型后端.llm import 装备错误#结构化工具策略失败

def 拒绝(消息,码='GOAL_TOOL_AUTHORITY_REQUIRED'):
    """抛出一次结构化工具策略失败。默认权限不足码。"""
    raise 装备错误(消息,码)#交给工具层

def 打开回合(智能体):
    """从日志尾往前找打开回合边界，返回 start 与其后事件。智能体是对象，events 是事件 dict 元组。"""
    事件列表=智能体.session.events#该会话已提交事件
    下标=len(事件列表)-1#从最新往回扫
    while 下标>=0:#仍有候选
        边界=事件列表[下标]#候选边界
        种类=边界['type']#事件类型
        if 种类=='turn/end':#已经碰到结束，说明没有打开回合
            拒绝('goal tools require an open model turn','GOAL_TOOL_DRIVER_REQUIRED')#必须在回合内
        if 种类=='turn/start':#找到打开边界
            return {'start':边界,'events':事件列表[下标+1:]}#窗口是其后事件
        下标-=1#继续往回
    拒绝('goal tools require an open model turn','GOAL_TOOL_DRIVER_REQUIRED')#整份日志都没有打开回合

def 目标工具执行(上下文,执行元数据):
    """解析并认证调用方智能体及其驱动器边界，返回已认证的智能体及其当前回合窗口。执行元数据是 dict。"""
    智能体=执行元数据['agent'] if 'agent' in 执行元数据 else None#工具调用绑定的智能体
    if 智能体 is None:#没有调用方
        拒绝('goal tools require a calling agent','GOAL_TOOL_AGENT_REQUIRED')#必须有智能体
    if 上下文.agents.获取(智能体.id) is not 智能体 or 智能体.状态!='running':#不是注册表里的实时实例或未在跑
        拒绝(#不在自己的驱动器里
            'goal tools require the exact live calling agent inside its active driver',#必须是活跃驱动器内的精确实例
            'GOAL_TOOL_DRIVER_REQUIRED',#驱动器边界失败
        )#结束拒绝
    if 上下文.agents.currentInitiator() is not 智能体:#当前驱动器发起方也必须是它
        拒绝(#不在自己的驱动器里
            'goal tools require the exact live calling agent inside its active driver',#必须是活跃驱动器内的精确实例
            'GOAL_TOOL_DRIVER_REQUIRED',#驱动器边界失败
        )#结束拒绝
    窗口=打开回合(智能体)#认证通过，附上打开回合
    return {'agent':智能体,'start':窗口['start'],'events':窗口['events']}#已认证执行窗口

def 有直接人类输入(上下文,执行):
    """当前根智能体回合里是否出现宿主证明的人类输入。省略的 Agent.followup()/steer() 来源会收成 user，因此非人类生产者必须自带来源，而不能继承这份权限。执行是 dict。"""
    根列表=上下文.agents.roots()#运行时根智能体列表
    if 执行['agent'] not in 根列表:#子智能体没有这份权限；根列表按对象身份
        return False#非根
    for 事件 in 执行['events']:#打开回合后的事件里
        if 事件['type']!='user/message':#非用户消息
            continue#下一条
        载荷=事件['data']#消息载荷
        来源=载荷['source'] if 'source' in 载荷 else None#消息来源
        if 来源 is None:#无来源
            continue#下一条
        if 来源['kind']=='user':#有用户来源消息
            return True#人类回合
    return False#没有人类输入

def 是否匹配目标轮次(执行,目标):
    """来源钉死当前修订与轮次时返回真。目标是 dict 快照。"""
    目标标识=目标['id']#当前目标 id
    修订=目标['revision']#当前修订
    已接纳=目标['roundsStarted']#已接纳轮次
    for 事件 in 执行['events']:#打开回合后的事件
        if 事件['type']!='user/message':#非用户消息
            continue#下一条
        载荷=事件['data']#消息载荷
        来源=载荷['source'] if 'source' in 载荷 else None#消息来源
        if 来源 is None:#无来源
            continue#下一条
        if 来源['kind']!='goal':#非目标来源
            continue#下一条
        if 来源['goalId']!=目标标识:#不是同一目标
            continue#下一条
        if 来源['revision']!=修订:#不是同一修订
            continue#下一条
        if 来源['round']!=已接纳:#轮次不等于已接纳计数
            continue#下一条
        return True#匹配当前目标轮次
    return False#未匹配

def 要求直接人类(上下文,执行):
    """要求权限来自运行时根所接受的一条人类消息。"""
    if 有直接人类输入(上下文,执行):#根回合有人类输入则放行
        return#放行
    拒绝('this goal operation requires a direct human turn on a top-level agent')#否则拒绝

def 完成权限(上下文,执行):
    """从直接人类输入或精确目标轮次解析完成权限。"""
    if 有直接人类输入(上下文,执行):#人类回合优先
        return {'kind':'direct-human'}#直接人类权限
    目标=上下文.goals.get(执行['agent'])#当前目标
    if 目标 is not None and 是否匹配目标轮次(执行,目标):#本回合就是该目标的当前轮
        return {'kind':'goal-round','goal':目标}#授予轮次权限
    拒绝('complete and blocked require a direct human turn or the current goal round')#两种权限都没有
