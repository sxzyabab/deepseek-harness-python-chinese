安全整数上限=2**53-1#对齐 Number.MAX_SAFE_INTEGER

def 委托深度于(智能体):
    """读取智能体的委托深度，缺失视为顶层深度零。持久会话头是权威且单调的：运行时 AgentOptions.subagentDepth 可以加深计数，但绝不能降低——恢复的子体带着全新选项到达，从零计数会让它像顶层一样再委托。智能体为对象，选项与头为 dict。"""
    选项=智能体.options#运行时选项
    运行时=选项['subagentDepth'] if isinstance(选项,dict) and 'subagentDepth' in 选项 else None#运行时选项深度
    if 运行时 is not None:#给出了运行时深度
        if isinstance(运行时,bool) or (not isinstance(运行时,int)) or 运行时<0 or 运行时>安全整数上限:#非法运行时深度
            raise TypeError('智能体 subagentDepth 必须是非负安全整数')#拒绝
    会话=智能体.session#会话
    头=会话.header#会话头
    if isinstance(头,dict) and 'delegationDepth' in 头 and 头['delegationDepth'] is not None:#头上有委托深度
        头深度=头['delegationDepth']#头上的委托深度
    else:#头缺失
        头深度=0#顶层零
    if 运行时 is None:#无运行时
        运行时=0#按零计
    return max(头深度,运行时)#取头与运行时的较大者

def 断言子智能体最大深度(最大深度):
    """拒绝不能表示精确委托深度的递归上限。"""
    if 最大深度 is None:#未给出
        return#跳过
    if isinstance(最大深度,bool) or (not isinstance(最大深度,int)) or 最大深度<0 or 最大深度>安全整数上限:#非法上限
        raise TypeError('子智能体 maxDepth 必须是非负安全整数')#拒绝
