"""会话检索消费方用的第一方语义文本抽取。"""

def 抽取会话事件文本(事件):
    """从一条第一方会话事件抽出可检索的语义文本。"""
    类型=事件['type']#判别标签
    数据=事件['data'] if 'data' in 事件 else {}#载荷
    if 类型=='user/message':#用户消息
        return 内容文本(数据['content'] if 'content' in 数据 else None)#内容块文本
    if 类型=='assistant/message':#助手消息
        消息=数据['message'] if 'message' in 数据 else {}#助手消息
        return 内容文本(消息['content'] if 'content' in 消息 else None)#助手内容
    if 类型=='tool/call':#工具调用
        return 拼接文本([数据['name'] if 'name' in 数据 else None,数据['arguments'] if 'arguments' in 数据 else None])#名与参数
    if 类型=='tool/result':#工具结果
        错误=数据['error'] if 'error' in 数据 else None#可选错误
        消息=数据['message'] if 'message' in 数据 else {}#结果消息
        return 拼接文本([
            内容文本(消息['content'] if 'content' in 消息 else None),
            错误['name'] if isinstance(错误,dict) and 'name' in 错误 else '',
            错误['code'] if isinstance(错误,dict) and 'code' in 错误 else '',
        ])#结果与错误标识
    if 类型=='todo/write':#待办写入
        片段=[]#状态与内容
        待办列表=数据['todos'] if 'todos' in 数据 else []#待办
        for 条 in 待办列表:#逐条待办
            片段.append(条['status'] if 'status' in 条 else None)#状态
            片段.append(条['content'] if 'content' in 条 else None)#内容
        return 拼接文本(片段)#拼接
    if 类型=='turn/end':#回合结束
        return 回合结束文本(数据['reason'] if 'reason' in 数据 else None)#按原因抽文本
    return ''#结构边界与未知类型不贡献文本

def 回合结束文本(原因):
    """按回合结束原因抽出可检索文本。"""
    if not isinstance(原因,dict):#必须是对象
        return ''#不贡献
    种类=原因['kind'] if 'kind' in 原因 else None#原因标签
    if 种类=='error':#出错结束
        错误=原因['error'] if 'error' in 原因 else {}#错误
        消息=错误['message'] if isinstance(错误,dict) and 'message' in 错误 else ''#消息
        return 拼接文本(['error',消息])#错误消息
    if 种类=='aborted':#中止
        return 'aborted'#固定文本
    if 种类 in ('max-tokens','interrupted'):#其他结构化结局
        return 种类#原因标签
    return ''#完成与未知不贡献

def 内容文本(内容):
    """把内容块列表收成换行拼接的语义文本。"""
    片段=[]#收集片段
    块列表=内容 if isinstance(内容,list) else []#块列表
    for 块 in 块列表:#逐块
        片段.extend(块文本(块))#展开块
    return 拼接文本(片段)#拼接

def 块文本(块):
    """从单块抽出可检索片段。"""
    if not isinstance(块,dict):#必须是对象
        return []#不贡献
    类型=块['type'] if 'type' in 块 else None#块类型
    if 类型=='text':#普通文本
        return [块['text'] if 'text' in 块 else '']#文本
    if 类型=='tool-call':#块内工具调用
        return [块['name'] if 'name' in 块 else '',块['arguments'] if 'arguments' in 块 else '']#名与参数
    return []#推理与未知块不贡献

def 拼接文本(片段列表):
    """去空白、丢掉空串、换行拼接。"""
    干净=[str(段).strip() for 段 in 片段列表 if 段 is not None and str(段).strip()!='']#修剪非空
    return '\n'.join(干净)#换行拼接
