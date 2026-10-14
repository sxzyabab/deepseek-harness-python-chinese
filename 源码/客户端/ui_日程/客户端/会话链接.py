'任务详情里原会话是否还能打开'

__all__=['会话链接状态','会话标签']

def 取(对象,键):
    '字典走键，对象走属性'
    if isinstance(对象,dict):
        return 对象[键] if 键 in 对象 else None
    return getattr(对象,键,None)

def 会话链接状态(标识,会话表,工作区表):
    '不激活会话，只看列表和归档'
    if 取(工作区表,'state')=='error':
        return 'unavailable'
    if 取(会话表,'phase')=='pending' or 取(工作区表,'phase')=='pending':
        return 'loading'
    归档=取(工作区表,'archivedSessionIds')
    if isinstance(归档,(list,tuple)) and 标识 in 归档:
        return 'archived'
    标识表=取(会话表,'ids')
    if not isinstance(标识表,(list,tuple)) or 标识 not in 标识表:
        return 'unavailable'
    return 'available'

def 会话标签(标识,会话表):
    '有标题用标题，否则用会话标识'
    按标识=取(会话表,'byId')
    行=None
    if isinstance(按标识,dict) and 标识 in 按标识:
        行=按标识[标识]
    标题=取(行,'title')
    if not isinstance(标题,str) or 标题.strip()=='':
        return {'text':标识 if isinstance(标识,str) else '','titled':False}
    return {'text':标题,'titled':True}
