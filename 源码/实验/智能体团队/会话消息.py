"""供应与邮箱恢复共享的持久 Session 消息接受检查。

对齐上游 `agent-team/src/session-message.ts`。公开面仅中文名。
"""
__all__=['消息已接受']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 待认领收件箱消息(事件们):#待认领 inbox
    """把持久 inbox 后缀折叠成仍等待 claim 的消息。"""
    收件箱={'next-turn':[],'next-step':[]}#两目标
    for 事件 in 事件们:#遍历事件
        if 取字段(事件,'type')!='agent/inbox/spliced':#非 inbox 事件
            continue#下一事件
        数据=取字段(事件,'data') or {}#载荷
        待处理=收件箱[取字段(数据,'target')]#目标队列
        起点=取字段(数据,'start') or 0#splice 起点
        移除数=取字段(数据,'removedCount')#可选移除数
        if 移除数 is None:#缺省 0
            移除数=0#默认
        插入=取字段(数据,'inserted') or []#插入项
        待处理[起点:起点+移除数]=list(插入)#应用 splice
    return list(收件箱['next-turn'])+list(收件箱['next-step'])#合并

def 消息已接受(事件们,谓词):#消息是否已接受
    """测试一条消息是否已对模型可见或仍持久待认领。"""
    for 事件 in 事件们:#历史命中
        if 取字段(事件,'type')=='user/message' and 谓词(取字段(事件,'data')):#历史
            return True#命中
    for 消息 in 待认领收件箱消息(事件们):#或 inbox 命中
        if 谓词(消息):#谓词
            return True#命中
    return False#未命中
