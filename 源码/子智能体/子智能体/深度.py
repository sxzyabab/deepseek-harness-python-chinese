"""委托深度记账：父传给其子的递归预算。与服务分开存放，以便组合辅助函数读取它而不导入注册表。"""
安全整数上限=2**53-1#对齐 Number.MAX_SAFE_INTEGER

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 委托深度于(智能体):#读取委托深度
    """读取智能体的委托深度，缺失视为顶层深度零。持久会话头是权威且单调的：运行时 AgentOptions.subagentDepth 可以加深计数，但绝不能降低——恢复的子体带着全新选项到达，从零计数会让它像顶层一样再委托。"""
    运行时=取字段(取字段(智能体,'options'),'subagentDepth')#运行时选项深度
    if 运行时 is not None:#给出了运行时深度
        if not isinstance(运行时,int) or isinstance(运行时,bool) or 运行时<0 or 运行时>安全整数上限:#非法运行时深度
            raise TypeError('agent subagentDepth must be a non-negative safe integer')#拒绝
        if 运行时==0 and str(运行时)=='-0':#负零防御（Python 无 -0 int，保留语义位）
            raise TypeError('agent subagentDepth must be a non-negative safe integer')#拒绝
    头深度=取字段(取字段(取字段(智能体,'session'),'header'),'delegationDepth')#头上的委托深度
    if 头深度 is None:#头缺失
        头深度=0#顶层零
    if 运行时 is None:#无运行时
        运行时=0#按零计
    return max(头深度,运行时)#取头与运行时的较大者

def 断言子智能体最大深度(最大深度):#断言maxDepth形态
    """拒绝不能表示精确委托深度的递归上限。"""
    if 最大深度 is None:#未给出
        return#跳过
    if not isinstance(最大深度,int) or isinstance(最大深度,bool) or 最大深度<0 or 最大深度>安全整数上限:#非法上限
        raise TypeError('subagent maxDepth must be a non-negative safe integer')#拒绝
