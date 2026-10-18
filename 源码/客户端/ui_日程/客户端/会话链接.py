'原会话能不能打开，以及行上显示的名字'

__all__=['会话链接状态','会话标签']

def 会话链接状态(标识,会话,工作区):
    '不激活、不恢复。成员以宿主列表 ids 为准'
    if 工作区.get('state')=='error':
        return 'unavailable'
    if 会话.get('phase')=='pending' or 工作区.get('phase')=='pending':
        return 'loading'
    if 标识 in 工作区.get('archivedSessionIds',[]):
        return 'archived'
    if 标识 not in 会话.get('ids',[]):
        return 'unavailable'
    return 'available'

def 会话标签(标识,会话):
    '有标题用标题，否则用会话标识，保证不是空串'
    行=会话.get('byId',{}).get(标识)
    标题=None if 行 is None else 行.get('title')
    if 标题 is None or str(标题).strip()=='':
        return {'text':标识,'titled':False}
    return {'text':标题,'titled':True}
