__all__=['过程活动','过程活动摘要','过程组数据']

过程活动=(
    'read','readImage','search','write','edit','commands','code',
    'webSearch','webFetch','subagents','plan','questions','tools',
)

def 过程活动摘要(计数表,运行中,运行详情,准备中=None):
    """不同调用类别排序与当前现场任务详情。"""
    项={'counts':计数表,'running':运行中,'runningDetail':运行详情}
    if 准备中 is True:
        项['preparing']=True
    return 项

def 过程组数据(回合,已闭合,摘要):
    """独立回复或输入之间一组的呈现事实。"""
    return {'turn':回合,'closed':已闭合,'summary':摘要}
