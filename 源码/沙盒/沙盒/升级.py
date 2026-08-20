"""每个沙箱强制工具家族共用的升级词表与编排：严格更宽阶梯、参数配对校验、面向模型的拒绝/提示标记，以及批准升级——在任何东西执行之前经用户审批通道解析 sandbox_permissions 请求的有序失败即关闭序列。一个所在防止两个家族的审批顺序与逐字错误文本漂移。通道是最小结构函数形状，不是审批服务类型：拥有智能体、调用 id 与工具名的工具层闭合审批请求并把闭包往下传，因此本包从不依赖审批或智能体包。"""
from llm import 断言永不#封闭联合穷尽辅助
from cordis.工具 import 是否thenable#可等待判定

更宽模式={#从当前模式可升级到的更宽模式
    'read-only':('workspace-write','danger-full-access'),#只读可升到工作区可写或完全放开
    'workspace-write':('danger-full-access',),#工作区可写只能升到完全放开
}#更宽模式结束

升级目标=('workspace-write','danger-full-access')#可广告的升级目标

升级结果=('allowed-once','rejected','cancelled','unavailable')#封闭升级结果词表

升级审批方字段=('request',)#最小审批请求方字段

升级审批字段=('approver','agent','callId','toolName','signal')#升级审批配料字段

升级请求字段=('requestedMode','justification','effectiveMode','subject')#一次升级请求字段

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待承诺
    return 值#同步值

def 校验升级参数(沙箱权限,理由):#校验升级参数配对
    """校验工具模式无法表达的升级参数配对：sandbox_permissions 与 justification 一起走——没有理由的审批提示，或什么都不驱动的理由，都是畸形询问——且理由必须是非空句子。"""
    if 沙箱权限 is not None and 理由 is None:#有目标没有理由
        raise Exception('invalid escalation: sandbox_permissions requires a justification')#必须带理由
    if 理由 is not None and 沙箱权限 is None:#有理由没有目标
        raise Exception('invalid escalation: justification is only valid together with sandbox_permissions')#理由只能与权限一起
    if 理由 is not None and len(理由.strip())==0:#理由空白
        raise Exception('invalid justification: expected a non-empty sentence')#必须是非空句子

def 沙箱拒绝标记(模式):#沙箱拒绝标记
    """面向模型的拒绝标记——两个强制家族都教都报的唯一词表，因此无论是内核拒绝了 bash 文件效果，还是文件系统提供方的围栏拒绝了变更，模型都以同样方式认出政策拒绝。"""
    return '[sandbox: file access denied under '+模式+' mode]'#面向模型的拒绝行

def 升级提示标记(主语):#升级提示标记
    """组合广告升级字段时，拒绝上搭载的同回合升级提示——轻推放在决策点，因此受准的重试不依赖模型回忆工具描述。"""
    return '[sandbox: escalation available — retry this exact '+主语+' once with sandbox_permissions (the narrowest wider mode that suffices) + justification; the approval prompt asks the user]'#面向模型的升级提示

def 批准升级(请求,审批):#解析升级请求
    """在任何东西执行之前解析沙箱升级请求：对照调用的生效模式检查严格加宽，然后解析审批通道，然后映射每个结果——两个强制家族共用的有序失败即关闭序列。返回盖到恰好这次调用上的授予模式；其他每条路径抛出不同的逐字文本。非加宽请求从不提示人。"""
    模式=取字段(请求,'requestedMode')#目标模式
    生效模式=取字段(请求,'effectiveMode')#当前生效模式
    理由=取字段(请求,'justification')#理由
    主语=取字段(请求,'subject')#动作名词
    if 模式 not in 更宽模式.get(生效模式,()):#不是严格更宽
        raise Exception('sandbox escalation to "'+模式+'" is not strictly wider than this call\'s current "'+生效模式+'" mode')#非加宽拒绝
    审批方=取字段(审批,'approver')#审批方
    if 审批方 is None:#没有审批服务
        raise Exception('sandbox escalation to "'+模式+'" requires approval, but no approval service is composed')#未组合审批
    智能体=取字段(审批,'agent')#智能体
    if 智能体 is None:#没有智能体
        raise Exception('sandbox escalation to "'+模式+'" requires approval, but the call has no agent to route it through')#无智能体无法路由
    请求体={#审批请求
        'agent':智能体,#智能体
        'toolName':取字段(审批,'toolName'),#工具名
        'callId':取字段(审批,'callId'),#调用id
        'reason':'escalate sandbox to '+模式+': '+理由,#审计理由
    }#请求骨架
    信号=取字段(审批,'signal')#可选取消
    if 信号 is not None:#有信号才带上
        请求体['signal']=信号#中止信号
    发出=取字段(审批方,'request')#审批请求方法（与 TS approval.approver.request 同形，不可调用则原样失败）
    结果=解开(发出(请求体))#请人批准并等待
    if 结果=='allowed-once':#允许一次
        return 模式#授予该模式
    if 结果=='rejected':#用户拒绝
        raise Exception('the user rejected escalating this '+主语+' to "'+模式+'"')#用户拒绝
    if 结果=='cancelled':#审批取消
        raise Exception('approval for escalating to "'+模式+'" was cancelled')#审批取消
    if 结果=='unavailable':#没有审批通道
        raise Exception('sandbox escalation to "'+模式+'" requires approval, but no approval channel is available')#没有审批通道
    return 断言永不(结果,'EscalationOutcome')#封闭联合穷尽
