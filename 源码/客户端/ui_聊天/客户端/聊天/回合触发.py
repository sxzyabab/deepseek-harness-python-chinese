__all__=['回合触发详情']

回合触发图标=('agent','github','goal','job','plugin','request','schedule','subagent','team','webhook')

def 记录对象(值):
    """非对象则空表。"""
    if isinstance(值,dict):
        return 值
    return {}

def 字段串(源,键):
    """非字符串则空串。"""
    if 键 not in 源:
        return ''
    值=源[键]
    return 值 if isinstance(值,str) else ''

def 回合触发详情(节点):
    """用源与可识别生产者框架描述唤醒消息。节点为 dict。"""
    源=记录对象(节点['source'] if 'source' in 节点 else None)
    种=字段串(源,'kind')
    标题='message.trigger.request'
    图标='request'
    if 种=='goal':
        标题='message.trigger.goal'
        图标='goal'
    elif 种=='agent-message':
        标题='message.trigger.agent'
        图标='agent'
    elif 种=='team-message':
        标题='message.trigger.team'
        图标='team'
    elif 种=='subagent-settled':
        标题='message.trigger.subagent'
        图标='subagent'
    elif 种=='webhook':
        是github=字段串(源,'provider')=='github'
        标题='message.trigger.github' if 是github else 'message.trigger.webhook'
        图标='github' if 是github else 'webhook'
    elif 种=='schedule':
        标题='message.trigger.schedule'
        图标='schedule'
    elif 种=='tool-jobs':
        标题='message.trigger.job'
        图标='job'
    elif 种=='cordis-host-runner':
        标题='message.trigger.plugin'
        图标='plugin'
    return {'title':标题,'icon':图标}
