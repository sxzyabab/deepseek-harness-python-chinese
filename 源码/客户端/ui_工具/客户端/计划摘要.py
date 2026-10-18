__all__=['计划摘要']

def 计划摘要(待办列表):
    'done、total、第一条进行中的内容，以及其余并行进行中的个数'
    进行中=[]
    完成数=0
    for 条目 in 待办列表:
        状态=条目.get('status') if isinstance(条目,dict) else None
        if 状态=='in_progress':
            进行中.append(条目)
        if 状态=='completed':
            完成数=完成数+1
    首条=进行中[0].get('content') if len(进行中)>0 else None
    可名=isinstance(首条,str) and 首条.strip()!=''
    return {
        'done':完成数,
        'total':len(待办列表),
        'activeContent':首条 if 可名 else None,
        'activeExtra':len(进行中)-1 if 可名 else 0,
    }
