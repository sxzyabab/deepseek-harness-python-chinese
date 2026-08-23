"""面向模型的目标工具在执行时的权限检查。"""
from ..llm import 装备错误#结构化工具策略失败

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 拒绝(消息,码='GOAL_TOOL_AUTHORITY_REQUIRED'):#抛出一次结构化工具策略失败
    """抛出一次结构化工具策略失败。默认权限不足码。"""
    raise 装备错误(消息,码)#交给工具层

def 打开回合(智能体):#定位包围一次模型工具调用的打开回合
    """从日志尾往前找打开回合边界，返回 start 与其后事件。"""
    事件们=智能体.session.events#该会话已提交事件
    下标=len(事件们)-1#从最新往回扫
    while 下标>=0:#仍有候选
        边界=事件们[下标]#候选边界
        种类=取字段(边界,'type')#事件类型
        if 种类=='turn/end':#已经碰到结束，说明没有打开回合
            拒绝('goal tools require an open model turn','GOAL_TOOL_DRIVER_REQUIRED')#必须在回合内
        if 种类=='turn/start':#找到打开边界
            return {'start':边界,'events':事件们[下标+1:]}#窗口是其后事件
        下标-=1#继续往回
    拒绝('goal tools require an open model turn','GOAL_TOOL_DRIVER_REQUIRED')#整份日志都没有打开回合

def 目标工具执行(上下文,执行元数据):#认证调用方智能体及其驱动器边界
    """解析并认证调用方智能体及其驱动器边界，返回已认证的智能体及其当前回合窗口。"""
    智能体=取字段(执行元数据,'agent')#工具调用绑定的智能体
    if 智能体 is None:#没有调用方
        拒绝('goal tools require a calling agent','GOAL_TOOL_AGENT_REQUIRED')#必须有智能体
    if 上下文.agents.get(智能体.id) is not 智能体 or 取字段(智能体,'status')!='running':#不是注册表里的实时实例或未在跑
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

def 有直接人类输入(上下文,执行):#本回合是否有人类消息
    """当前根智能体回合里是否出现宿主证明的人类输入。省略的 Agent.followup()/steer() 来源会收成 user，因此非人类生产者必须自带来源，而不能继承这份权限。"""
    根们=上下文.agents.roots()#运行时根智能体列表
    if 执行['agent'] not in 根们:#子智能体没有这份权限
        return False#非根
    for 事件 in 执行['events']:#打开回合后的事件里
        if 取字段(事件,'type')!='user/message':#非用户消息
            continue#下一条
        来源=取字段(取字段(事件,'data'),'source')#消息来源
        if 取字段(来源,'kind')=='user':#有用户来源消息
            return True#人类回合
    return False#没有人类输入

def 是否匹配目标轮次(执行,目标):#本回合是否恰好是当前目标的已接纳轮次
    """来源钉死当前修订与轮次时返回真。"""
    目标标识=取字段(目标,'id')#当前目标 id
    修订=取字段(目标,'revision')#当前修订
    已接纳=取字段(目标,'roundsStarted')#已接纳轮次
    for 事件 in 执行['events']:#打开回合后的事件
        if 取字段(事件,'type')!='user/message':#非用户消息
            continue#下一条
        来源=取字段(取字段(事件,'data'),'source')#消息来源
        if 取字段(来源,'kind')!='goal':#非目标来源
            continue#下一条
        if 取字段(来源,'goalId')!=目标标识:#不是同一目标
            continue#下一条
        if 取字段(来源,'revision')!=修订:#不是同一修订
            continue#下一条
        if 取字段(来源,'round')!=已接纳:#轮次不等于已接纳计数
            continue#下一条
        return True#匹配当前目标轮次
    return False#未匹配

def 要求直接人类(上下文,执行):#创建/编辑/暂停/恢复
    """要求权限来自运行时根所接受的一条人类消息。"""
    if 有直接人类输入(上下文,执行):#根回合有人类输入则放行
        return#放行
    拒绝('this goal operation requires a direct human turn on a top-level agent')#否则拒绝

def 完成权限(上下文,执行):#完成/阻塞
    """从直接人类输入或精确目标轮次解析完成权限。"""
    if 有直接人类输入(上下文,执行):#人类回合优先
        return {'kind':'direct-human'}#直接人类权限
    目标=上下文.goals.get(执行['agent'])#当前目标
    if 目标 is not None and 是否匹配目标轮次(执行,目标):#本回合就是该目标的当前轮
        return {'kind':'goal-round','goal':目标}#授予轮次权限
    拒绝('complete and blocked require a direct human turn or the current goal round')#两种权限都没有
