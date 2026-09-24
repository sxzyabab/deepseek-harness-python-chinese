"""原生 V4 开发者消息与推迟工具模式校验。"""
from ..会话格式 import 会话格式错误,是否会话格式json对象,会话格式计数#从会话格式导入

def 断言工具变更(块,开发者):#断言工具增删块
    """校验 tool-addition / tool-removal 块。"""
    if not 是否会话格式json对象(块) or 块.get('type') not in ('tool-addition','tool-removal'):#非变更块
        return#返回
    if not 开发者:#须开发者角色
        raise 会话格式错误('format v4 '+str(块.get('type'))+' requires developer role')#错误
    if not isinstance(块.get('toolName'),str) or len(块['toolName'])==0:#须非空名
        raise 会话格式错误('format v4 '+str(块.get('type'))+' requires a nonempty toolName')#错误
    if 块.get('type')=='tool-addition' and 'tool' in 块:#禁止内联定义
        raise 会话格式错误('format v4 tool-addition must omit inline tool definitions')#错误

def 断言内容(值,开发者=False):#断言内容中的工具变更
    """走访内容数组上的工具变更块。"""
    if isinstance(值,list):#数组
        for 块 in 值:#逐块
            断言工具变更(块,开发者)#断言

def 断言开发者消息(消息):#断言开发者消息
    """校验开发者消息身份、内容与生产者来源。"""
    断言内容(消息.get('content'),True)#内容须开发者
    来源=消息.get('source')#来源
    if (not isinstance(消息.get('id'),str) or len(消息['id'])==0
        or not isinstance(消息.get('content'),list) or not 是否会话格式json对象(来源)
        or not isinstance(来源.get('kind'),str) or len(来源['kind'])==0 or 来源['kind']=='plugin'):#须完整
        raise 会话格式错误('format v4 developer message requires id, role, content, and a producer-owned source')#错误

def 断言普通消息(值):#断言普通消息
    """普通消息损坏交给解码器；此处拒绝已识别的仅 V4 值。"""
    if not 是否会话格式json对象(值):#非对象
        return#返回
    if 值.get('role')=='developer':#角色与事件类型须同时出现
        raise 会话格式错误('format v4 developer/message and developer role must occur together')#错误
    断言内容(值.get('content'))#内容

def 断言v4开发者数据(事件):#断言v4开发者数据
    """校验原生 V4 开发者消息、工具变更块与推迟工具模式。"""
    数据=事件.get('data')#载荷
    if not 是否会话格式json对象(数据):#非对象
        if 事件.get('type')=='developer/message':#开发者须对象
            raise 会话格式错误('format v4 developer/message data must be an object')#错误
        return#返回
    if 事件.get('type')=='developer/message':#开发者事件
        消息=数据.get('message')#消息
        if not 是否会话格式json对象(消息) or 消息.get('role')!='developer':#须开发者消息
            raise 会话格式错误('format v4 developer/message requires turn, step, and a developer message')#错误
        for 字段 in ('turn','step'):#坐标
            if 会话格式计数(数据.get(字段),'developer/message '+字段)==0:#须为正
                raise 会话格式错误('developer/message '+字段+' must be positive')#错误
        断言开发者消息(消息)#消息
        内容=消息['content']#内容
        有追加=any(是否会话格式json对象(块) and 块.get('type')=='tool-addition' for 块 in 内容)#是否有追加
        if 有追加:#须headerSeq
            会话格式计数(数据.get('headerSeq'),'developer/message headerSeq')#headerSeq
        elif 'headerSeq' in 数据:#无追加却带headerSeq
            raise 会话格式错误('format v4 developer/message must omit headerSeq without tool additions')#错误
    else:#普通事件
        类型=事件.get('type')#类型
        if 类型=='user/message':#用户消息
            断言普通消息(数据)#断言
        elif 类型 in ('system/message','assistant/message','tool/result'):#嵌套
            断言普通消息(数据.get('message'))#断言
        elif 类型=='agent/inbox/spliced' or 类型=='session/title-llm-request':#多消息
            消息列表=数据.get('inserted' if 类型=='agent/inbox/spliced' else 'messages')#消息列表
            if isinstance(消息列表,list):#数组
                for 消息 in 消息列表:#逐条
                    断言普通消息(消息)#断言
    if 事件.get('type')=='compaction/summary':#压缩摘要
        断言内容(数据.get('summary'))#摘要
        断言内容(数据.get('rawOutput'))#原文
    if (事件.get('type')=='assistant/message' or 事件.get('type')=='assistant/attempt') and isinstance(数据.get('stream'),list):#内嵌流
        for 条目 in 数据['stream']:#逐条
            if not 是否会话格式json对象(条目) or 条目.get('type')!='chunk':#非chunk
                continue#继续
            分块=条目.get('chunk')#chunk
            if not 是否会话格式json对象(分块):#非对象
                continue#继续
            if 分块.get('type')=='block-end':#结束块
                断言工具变更(分块.get('block'),False)#非开发者
            if 分块.get('type')=='block-start' and 分块.get('blockType') in ('tool-addition','tool-removal'):#变更块
                raise 会话格式错误('format v4 tool-change blocks require developer role')#错误
    if 事件.get('type')=='request/header' and 是否会话格式json对象(数据.get('header')):#请求头
        工具列表=数据['header'].get('tools')#工具
        if isinstance(工具列表,list):#数组
            for 工具 in 工具列表:#逐项
                if not 是否会话格式json对象(工具) or 'deferLoading' not in 工具:#无推迟
                    continue#继续
                if 工具.get('deferLoading') is not True:#须为true
                    raise 会话格式错误('format v4 tool deferLoading must be true when present')#错误
