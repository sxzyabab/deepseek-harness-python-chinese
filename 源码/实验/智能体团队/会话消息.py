"""供应与邮箱恢复共享的持久 Session 消息接受检查。

对齐上游 `agent-team/src/session-message.ts`。公开面仅中文名。
"""
__all__=['消息已接受']#仅中文公开名

def 待认领收件箱消息(事件列表):#待认领 inbox
    """把持久 inbox 后缀折叠成仍等待 claim 的消息。"""
    收件箱={'next-turn':[],'next-step':[]}#两目标
    for 事件 in 事件列表:#遍历事件
        if 'type' not in 事件 or 事件['type']!='agent/inbox/spliced':#非 inbox 事件
            continue#下一事件
        数据=事件['data'] if 'data' in 事件 else {}#载荷
        待处理=收件箱[数据['target']]#目标队列
        起点=数据['start'] if 'start' in 数据 else 0#splice 起点
        移除数=数据['removedCount'] if 'removedCount' in 数据 else 0#可选移除数
        插入=数据['inserted'] if 'inserted' in 数据 else []#插入项
        待处理[起点:起点+移除数]=list(插入)#应用 splice
    return list(收件箱['next-turn'])+list(收件箱['next-step'])#合并

def 消息已接受(事件列表,谓词):#消息是否已接受
    """测试一条消息是否已对模型可见或仍持久待认领。"""
    for 事件 in 事件列表:#历史命中
        if 'type' in 事件 and 事件['type']=='user/message' and 谓词(事件['data']):#历史
            return True#命中
    for 消息 in 待认领收件箱消息(事件列表):#或 inbox 命中
        if 谓词(消息):#谓词
            return True#命中
    return False#未命中
