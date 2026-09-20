"""从事件日志折叠最新标题。"""

def 折叠会话标题(事件列表):
    """折叠最新已记录标题，不查可变元数据；无标题事件时返回 None。"""
    事件=None#最后一条标题事件
    for 项 in 事件列表:#按日志顺序扫描
        if 项['type']=='session/title':#标题事件
            事件=项#记下最后一条
    if 事件 is None:#没有标题
        return None#无标题
    数据=事件['data']#标题载荷
    return {
        'title':数据['title'],#标题文本
        'messageSeqs':数据['messageSeqs'] if 'messageSeqs' in 数据 else None,#来源消息序号
        'source':数据['source'],#标题来源
        'eventSeq':事件['seq'],#事件序号
        'updatedAt':事件['time'],#更新时间
    }#快照结束
