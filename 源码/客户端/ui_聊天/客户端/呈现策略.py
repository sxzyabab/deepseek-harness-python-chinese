from ..聊天设置 import 折叠时机表

__all__=['折叠时机表','导出呈现策略']

策略底={
    'compact':{
        'mode':'compact',
        'foldCompletedTurns':True,
        'stepGrouping':'collapsed',
        'liveProcessDetail':False,
        'settledReasoningPreview':False,
    },
    'standard':{
        'mode':'standard',
        'foldCompletedTurns':True,
        'stepGrouping':'collapsed',
        'liveProcessDetail':True,
        'settledReasoningPreview':True,
    },
    'detailed':{
        'mode':'detailed',
        'foldCompletedTurns':True,
        'stepGrouping':'history',
        'liveProcessDetail':True,
        'settledReasoningPreview':True,
    },
    'verbose':{
        'mode':'verbose',
        'foldCompletedTurns':False,
        'stepGrouping':'none',
        'liveProcessDetail':False,
        'settledReasoningPreview':True,
    },
}


def 带时机(折叠时机):
    '四档都带上同一份收起时机。同一对选择始终是同一份对象'
    结果={}
    for 模式,策略 in 策略底.items():
        副本=dict(策略)
        副本['collapseTiming']=折叠时机
        结果[模式]=副本
    return 结果


时机策略={
    'completion':带时机('completion'),
    'next-input':带时机('next-input'),
}


def 导出呈现策略(模式,折叠时机):
    '不自己订阅。快照跟着两份宿主偏好走'
    def 取快照():
        '按当前模式和收起时机取稳定策略'
        return 时机策略[折叠时机.getSnapshot()][模式.getSnapshot()]

    def 订阅(监听):
        '两份偏好任一变化都通知'
        退模式=模式.subscribe(监听)
        退时机=折叠时机.subscribe(监听)

        def 退订():
            '同时拆掉两份订阅'
            退模式()
            退时机()

        return 退订

    return {'getSnapshot':取快照,'subscribe':订阅}
