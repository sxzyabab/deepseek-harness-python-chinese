__all__=['计划摘要']

def 计划摘要(待办列表):
    'done、total、activeContent、activeExtra'
    活跃=[项 for 项 in 待办列表 if 项['status']=='in_progress']
    首=活跃[0]['content'] if len(活跃)>0 else None
    命名=isinstance(首,str) and 首.strip()!=''
    return {
        'done':len([项 for 项 in 待办列表 if 项['status']=='completed']),
        'total':len(待办列表),
        'activeContent':首 if 命名 else None,
        'activeExtra':(len(活跃)-1) if 命名 else 0,
    }
