"""从事件日志折叠最新标题。对齐上游 `session-title` 的 `foldSessionTitle` 纯函数面。"""

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 折叠会话标题(事件们):#折叠最新标题快照
    """折叠最新已记录标题，不查可变元数据；无标题事件时返回 None。"""
    事件=None#最后一条标题事件
    for 项 in 事件们:#按日志顺序扫描
        if 取字段(项,'type')=='session/title':#标题事件
            事件=项#记下最后一条
    if 事件 is None:#没有标题
        return None#无标题
    数据=取字段(事件,'data')#标题载荷
    return {#标题快照
        'title':取字段(数据,'title'),#标题文本
        'messageSeqs':取字段(数据,'messageSeqs'),#来源消息序号
        'source':取字段(数据,'source'),#标题来源
        'eventSeq':取字段(事件,'seq'),#事件序号
        'updatedAt':取字段(事件,'time'),#更新时间
    }#快照结束
