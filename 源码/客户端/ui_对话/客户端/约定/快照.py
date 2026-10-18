'从一个会话事件窗组装出的、与目标无关的会话状态'

__all__=['空会话快照','会话阶段']

空会话快照={
    'views':{
        'get':lambda 键:None,
        'grouped':lambda 键:None,
    },
    'activeTargets':set(),
}

def 会话阶段(会话,对话):
    '由会话生命周期和已登记目标的活动推出外壳阶段'
    活动=len(对话['activeTargets'])>0 or ((not 会话['blank']) and (not 会话['awaitingFirstTurn'])) or 会话['running']
    if 活动:
        return 'active'
    if 会话['promptAttempted']:
        return 'engaging'
    return 'blank'
