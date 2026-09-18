"""每个沙箱强制工具家族共用的升级词表与编排：严格更宽阶梯、参数配对校验、面向模型的拒绝/提示标记，以及批准升级——在任何东西执行之前经用户审批通道解析 sandbox_permissions 请求的有序失败即关闭序列。一个所在防止两个家族的审批顺序与逐字错误文本漂移。通道是最小结构函数形状，不是审批服务类型：拥有智能体、调用 id 与工具名的工具层闭合审批请求并把闭包往下传，因此本包从不依赖审批或智能体包。"""
from ...模型后端.llm import 断言永不#封闭联合穷尽辅助

class 沙箱升级错误(Exception):
    """沙箱升级失败。"""

更宽模式={#从当前模式可升级到的更宽模式
    'read-only':('workspace-write','danger-full-access'),#只读可升到工作区可写或完全放开
    'workspace-write':('danger-full-access',),#工作区可写只能升到完全放开
}#更宽模式结束

升级目标=('workspace-write','danger-full-access')#可广告的升级目标

升级结果=('allowed-once','rejected','cancelled','unavailable')#封闭升级结果词表

升级审批方字段=('request',)#最小审批请求方字段

升级审批字段=('approver','agent','callId','toolName','signal')#升级审批配料字段

升级请求字段=('requestedMode','justification','effectiveMode','subject')#一次升级请求字段

def 校验升级参数(沙箱权限,理由):
    """校验工具模式无法表达的升级参数配对：sandbox_permissions 与 justification 一起走——没有理由的审批提示，或什么都不驱动的理由，都是畸形询问——且理由必须是非空句子。"""
    if 沙箱权限 is not None and 理由 is None:#有目标没有理由
        raise 沙箱升级错误('invalid escalation: sandbox_permissions requires a justification')#必须带理由
    if 理由 is not None and 沙箱权限 is None:#有理由没有目标
        raise 沙箱升级错误('invalid escalation: justification is only valid together with sandbox_permissions')#理由只能与权限一起
    if 理由 is not None and len(理由.strip())==0:#理由空白
        raise 沙箱升级错误('invalid justification: expected a non-empty sentence')#必须是非空句子

def 沙箱拒绝标记(模式):
    """面向模型的拒绝标记——两个强制家族都教都报的唯一词表。"""
    return '[sandbox: file access denied under '+模式+' mode]'#面向模型的拒绝行

def 升级提示标记(主语):
    """组合广告升级字段时，拒绝上搭载的同回合升级提示。"""
    return '[sandbox: escalation available — retry this exact '+主语+' once with sandbox_permissions (the narrowest wider mode that suffices) + justification; the approval prompt asks the user]'#面向模型的升级提示

def 批准升级(请求,审批):
    """在执行前解析沙箱权限请求。重复生效模式则直接返回；严格更宽需审批。请求与审批都是 dict；审批方是对象。"""
    模式=请求['requestedMode']#目标模式
    生效模式=请求['effectiveMode']#当前生效模式
    理由=请求['justification']#理由
    主语=请求['subject']#动作名词
    if 模式==生效模式:#重复生效模式
        return 生效模式#无需审批
    可升=更宽模式[生效模式] if 生效模式 in 更宽模式 else ()#可升级目标
    if 模式 not in 可升:#不是严格更宽
        raise 沙箱升级错误('sandbox escalation to "'+模式+'" is not strictly wider than this call\'s current "'+生效模式+'" mode')#非加宽拒绝
    if 'approver' not in 审批 or 审批['approver'] is None:#没有审批服务
        raise 沙箱升级错误('sandbox escalation to "'+模式+'" requires approval, but no approval service is composed')#未组合审批
    审批方=审批['approver']#审批方对象
    if 'agent' not in 审批 or 审批['agent'] is None:#没有智能体
        raise 沙箱升级错误('sandbox escalation to "'+模式+'" requires approval, but the call has no agent to route it through')#无智能体无法路由
    请求体={#审批请求
        'agent':审批['agent'],#智能体
        'toolName':审批['toolName'],#工具名
        'callId':审批['callId'],#调用id
        'reason':'escalate sandbox to '+模式+': '+理由,#审计理由
    }#请求骨架
    if 'signal' in 审批 and 审批['signal'] is not None:#有信号才带上
        请求体['signal']=审批['signal']#中止信号
    结果=审批方.请求(请求体)#请人批准，同步返回
    if 结果=='allowed-once':#允许一次
        return 模式#授予该模式
    if 结果=='rejected':#用户拒绝
        raise 沙箱升级错误('the user rejected escalating this '+主语+' to "'+模式+'"')#用户拒绝
    if 结果=='cancelled':#审批取消
        raise 沙箱升级错误('approval for escalating to "'+模式+'" was cancelled')#审批取消
    if 结果=='unavailable':#没有审批通道
        raise 沙箱升级错误('sandbox escalation to "'+模式+'" requires approval, but no approval channel is available')#没有审批通道
    return 断言永不(结果,'EscalationOutcome')#封闭联合穷尽
