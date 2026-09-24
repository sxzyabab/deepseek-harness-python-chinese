"""已退役原生语法即使在可恢复的物理行失败之后仍硬性拒绝。"""
from ..会话格式 import 会话格式错误,会话格式不支持迁移错误,是否会话格式json对象#从会话格式导入

def 断言块(块,主语):#断言内容块
    """拒绝已发布 tool-result 包装。"""
    if 是否会话格式json对象(块) and 块.get('type')=='tool-result':#退役包装
        raise 会话格式错误(主语+' must not contain a released tool-result wrapper')#错误

def 断言内容(内容,主语):#断言内容数组
    """断言内容数组中每一块。"""
    if isinstance(内容,list):#数组
        for 块 in 内容:#逐块
            断言块(块,主语)#断言

def 断言消息内容(消息,主语):#断言嵌套消息内容
    """断言消息对象上的内容。"""
    if 是否会话格式json对象(消息):#对象
        断言内容(消息.get('content'),主语)#内容

def 断言v4已退役语法(行):#断言v4已退役语法
    """拒绝已退役头、PTC 标签，以及解释槽里的 tool-result 块。"""
    if not 是否会话格式json对象(行):#非对象
        return#返回
    if (行.get('type')=='tool/code-dispatch-start' or 行.get('type')=='tool/code-dispatch') and 行.get('ignorable') is not True:#必需前代PTC
        raise 会话格式不支持迁移错误('format v4 rejects retired event type '+str(行.get('type')))#拒绝
    数据=行.get('data')#载荷
    if 行.get('type')=='request/header':#请求头
        if not 是否会话格式json对象(数据) or not 是否会话格式json对象(数据.get('header')):#须对象
            raise 会话格式错误('format v4 request/header requires data and header objects')#错误
        if 'system' in 数据['header']:#退役system
            raise 会话格式错误('format v4 request/header rejects retired header.system')#错误
        return#返回
    if not 是否会话格式json对象(数据):#无对象载荷
        return#返回
    主语='format v4 '+str(行.get('type'))+' at seq '+str(行.get('seq'))+' content'#诊断主语
    类型=行.get('type')#类型
    if 类型=='user/message':#用户消息
        断言内容(数据.get('content'),主语)#内容
    elif 类型 in ('developer/message','assistant/message','team/message/queued'):#嵌套消息
        断言消息内容(数据.get('message'),主语)#消息内容
    elif 类型=='agent/inbox/spliced' or 类型=='session/title-llm-request':#多消息
        消息列表=数据.get('inserted' if 类型=='agent/inbox/spliced' else 'messages')#消息列表
        if isinstance(消息列表,list):#数组
            for 消息 in 消息列表:#逐条
                断言消息内容(消息,主语)#断言
    elif 类型=='compaction/summary':#压缩摘要
        断言内容(数据.get('summary'),主语)#摘要
        断言内容(数据.get('rawOutput'),主语)#原文
    elif 类型=='tool/ptc-dispatch':#ptc分发
        断言内容(数据.get('content'),主语)#内容
    if (类型=='assistant/message' or 类型=='assistant/attempt') and isinstance(数据.get('stream'),list):#内嵌流
        for 条目 in 数据['stream']:#逐条
            if not 是否会话格式json对象(条目) or 条目.get('type')!='chunk':#非chunk
                continue#继续
            分块=条目.get('chunk')#chunk
            if not 是否会话格式json对象(分块):#非对象
                continue#继续
            if 分块.get('type')=='block-end':#结束块
                断言块(分块.get('block'),主语)#断言
            if 分块.get('type')=='block-start' and 分块.get('blockType')=='tool-result':#起始为退役包装
                raise 会话格式错误(主语+' must not contain a released tool-result wrapper')#错误
