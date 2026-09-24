__all__=['呈现策略于','派生呈现策略']

策略表={#工作详情模式 → 呈现能力；渲染器只读字段不比较模式枚举
    'compact':{
        'mode':'compact','foldCompletedTurns':True,'stepGrouping':'collapsed',
        'liveProcessDetail':False,'settledReasoningPreview':False,
    },
    'standard':{
        'mode':'standard','foldCompletedTurns':True,'stepGrouping':'collapsed',
        'liveProcessDetail':True,'settledReasoningPreview':True,
    },
    'detailed':{
        'mode':'detailed','foldCompletedTurns':True,'stepGrouping':'history',
        'liveProcessDetail':True,'settledReasoningPreview':True,
    },
    'verbose':{
        'mode':'verbose','foldCompletedTurns':False,'stepGrouping':'none',
        'liveProcessDetail':False,'settledReasoningPreview':True,
    },
}

def 呈现策略于(模式):
    """同一模式恒返回同一对象，选择器看到稳定身份。"""
    return 策略表[模式]

def 派生呈现策略(模式源):
    """由表查找派生策略可观察源，变更通知复用模式源。"""
    def 取快照():
        """当前模式对应策略。"""
        return 策略表[模式源.getSnapshot()]
    def 订阅(监听):
        """转发模式源订阅。"""
        return 模式源.subscribe(监听)
    return {'getSnapshot':取快照,'subscribe':订阅}
