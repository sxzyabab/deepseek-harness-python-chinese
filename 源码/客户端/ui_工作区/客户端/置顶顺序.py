from .存储 import 扁平会话顺序键#扁平账本键
from .树 import 未分组键,拥有分组键#分组

__all__=['置顶顺序源','置顶顺序账本']

def 会话成员标识(列表):
    """扁平账本成员：列表 ids 序。"""
    return list(列表['ids']) if 'ids' in 列表 else []

def 置顶顺序源(工作区表,列表,行状态):
    """每个工作区、未分组与扁平列表的完整成员。"""
    已记账=set()
    for 工作区 in 工作区表:
        for 标识 in 工作区['sessionIds']:
            已记账.add(标识)
    成员={}
    for 工作区 in 工作区表:
        成员[工作区['workspaceId']]=工作区['sessionIds']
    标识序=列表['ids'] if 'ids' in 列表 else ()
    摘要=列表['byId'] if 'byId' in 列表 else {}
    成员[未分组键]=[标识 for 标识 in 标识序 if 标识 in 摘要 and 标识 not in 已记账]
    成员[扁平会话顺序键]=会话成员标识(列表)
    return {'members':成员,'summaries':摘要,'rowState':行状态}

def 置顶顺序账本(工作区表,会话标识):
    """被置顶会话领头的账本：其分组（或未分组）与扁平列表。"""
    return [拥有分组键(工作区表,会话标识),扁平会话顺序键]
