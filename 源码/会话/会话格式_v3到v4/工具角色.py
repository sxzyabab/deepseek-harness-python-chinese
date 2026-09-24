"""V4 表示中的一等工具角色消息。"""
from ..会话格式 import 会话格式错误,会话格式不支持迁移错误,是否会话格式json对象#从会话格式导入

包装字段=frozenset(['type','toolCallId','content','isError'])#包装自有字段
消息字段=frozenset(['id','role','source','content'])#消息自有字段

def 扩展字段(值,字段集,所有者):#扩展字段
    """保留未知字段，且不合并其原始消息与结果所有者。"""
    return {'plugin:'+所有者+':'+键:字段 for 键,字段 in 值.items() if 键 not in 字段集}#加前缀

def 结果内容(值,主语):#结果内容数组
    """要求工具结果内容为数组且不含嵌套 tool-result。"""
    if not isinstance(值,list):#须数组
        raise 会话格式错误(主语+' tool-result content must be an array')#错误
    for 块 in 值:#查嵌套
        if 是否会话格式json对象(块) and 块.get('type')=='tool-result':#嵌套
            raise 会话格式不支持迁移错误(主语+' contains a nested tool-result unsupported by this converter')#拒绝
    return 值#返回

def 提升工具结果(事件):#提升工具结果
    """把已发布 V3 包装 tool/result 行提升为一等 V4 消息。"""
    if 事件['type']!='tool/result' or not 是否会话格式json对象(事件.get('data')):#非目标
        return 事件#原样
    数据=事件['data']#载荷
    消息=数据.get('message')#消息
    if not 是否会话格式json对象(消息) or 消息.get('role')!='user':#非包装形态
        return 事件#原样
    来源=消息.get('source')#来源
    调用标识=来源.get('callId') if 是否会话格式json对象(来源) else None#调用标识
    内容=消息.get('content')#内容
    块=内容[0] if isinstance(内容,list) and len(内容)==1 else None#唯一块
    包装=块 if 是否会话格式json对象(块) else None#包装块
    标识=消息.get('id')#消息标识
    if (not isinstance(标识,str) or len(标识)==0
        or not 是否会话格式json对象(来源) or 来源.get('kind')!='tool'
        or not isinstance(调用标识,str) or len(调用标识)==0
        or 包装 is None or 包装.get('type')!='tool-result'
        or 包装.get('toolCallId')!=调用标识):#须精确包装
        raise 会话格式错误('format v3 '+事件['type']+' at seq '+str(事件['seq'])+' requires exactly one tool-result wrapper matching its tool source')#错误
    是否错误=包装.get('isError') if 'isError' in 包装 else None#错误旗标
    if 是否错误 is not None and not isinstance(是否错误,bool):#须布尔
        raise 会话格式错误('format v3 '+事件['type']+' at seq '+str(事件['seq'])+' tool-result isError must be boolean')#错误
    目标消息={#一等工具消息
        'role':'tool',#角色
        'source':来源,#来源
        'toolCallId':调用标识,#调用标识
        'content':结果内容(包装.get('content'),'format v3 '+事件['type']+' at seq '+str(事件['seq'])),#内容
        'id':标识,#标识
    }#基字段
    if 是否错误 is not None:#有错误旗标
        目标消息['isError']=是否错误#写入
    目标消息={**目标消息,**扩展字段(消息,消息字段,'message'),**扩展字段(包装,包装字段,'result')}#扩展
    return {**事件,'data':{**数据,'message':目标消息}}#写回

def 断言v4工具结果消息(事件):#断言v4工具结果消息
    """校验一条 tool/result 行的原生 V4 一等工具角色消息。"""
    if 事件['type']!='tool/result':#非工具结果
        return#返回
    主语='format v4 '+事件['type']+' at seq '+str(事件['seq'])#诊断主语
    数据=事件.get('data')#载荷
    if not 是否会话格式json对象(数据):#须对象
        raise 会话格式错误(主语+' data must be an object')#错误
    消息=数据.get('message')#消息
    if not 是否会话格式json对象(消息):#须对象
        raise 会话格式错误(主语+' message must be an object')#错误
    标识=消息.get('id')#标识
    角色=消息.get('role')#角色
    工具调用标识=消息.get('toolCallId')#工具调用标识
    来源=消息.get('source')#来源
    是否错误=消息.get('isError') if 'isError' in 消息 else None#错误旗标
    内容=消息.get('content')#内容
    来源调用标识=来源.get('callId') if 是否会话格式json对象(来源) else None#来源callId
    if not isinstance(标识,str) or len(标识)==0:#须标识
        raise 会话格式错误(主语+' requires a first-class message with a string id')#错误
    if 角色!='tool':#须工具角色
        raise 会话格式错误(主语+' requires a tool-role message')#错误
    if not isinstance(工具调用标识,str) or len(工具调用标识)==0 or 来源调用标识!=工具调用标识:#须匹配
        raise 会话格式错误(主语+' requires toolCallId matching its tool source')#错误
    if not 是否会话格式json对象(来源) or 来源.get('kind')!='tool':#须工具来源
        raise 会话格式错误(主语+' requires a tool source')#错误
    if not isinstance(内容,list):#须数组
        raise 会话格式错误(主语+' requires array content')#错误
    for 块 in 内容:#查包装
        if 是否会话格式json对象(块) and 块.get('type')=='tool-result':#退役包装
            raise 会话格式错误(主语+' content must not contain a released tool-result wrapper')#错误
    if 是否错误 is not None and not isinstance(是否错误,bool):#须布尔
        raise 会话格式错误(主语+' isError must be boolean when present')#错误
    if 'error' in 数据 and 是否错误 is not True:#错误元数据须配isError
        raise 会话格式错误(主语+' carries error metadata for a non-error tool result')#错误
