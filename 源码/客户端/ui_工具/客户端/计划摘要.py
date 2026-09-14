__all__=['计划摘要']#仅中文公开名

def 计划摘要(待办列表):#从整表推导
    """done/total/activeContent/activeExtra。"""
    活跃=[项 for 项 in 待办列表 if 项['status']=='in_progress']#进行中
    首=活跃[0]['content'] if len(活跃)>0 else None#首正文；length 语义
    命名=isinstance(首,str) and 首.strip()!=''#可用名
    return {#摘要
        'done':len([项 for 项 in 待办列表 if 项['status']=='completed']),#完成
        'total':len(待办列表),#总
        'activeContent':首 if 命名 else None,#活跃正文
        'activeExtra':(len(活跃)-1) if 命名 else 0,#额外
    }#结束
