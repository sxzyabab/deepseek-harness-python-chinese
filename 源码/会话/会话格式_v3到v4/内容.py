"""V3 内容标签与请求工具字段，在 V4 解释前准入。"""
from ..会话格式 import 会话格式错误,会话格式不支持迁移错误,是否会话格式json对象#从会话格式导入
from .源列表 import 映射事件消息#映射事件消息

v3块类型=frozenset(['text','reasoning','image','file','tool-call','tool-result'])#V3块类型

def 迁移块(值,主语):#迁移单个内容块
    """把未声明块类型加上 plugin 前缀。"""
    if not 是否会话格式json对象(值) or not isinstance(值.get('type'),str):#须带字符串type
        raise 会话格式错误(主语+' requires content blocks with string type tags')#错误
    类型=值['type']#类型
    if 类型 in v3块类型:#已声明
        return 值#原样
    return {**值,'type':'plugin:'+类型}#加前缀

def 迁移v3内容(值,主语):#迁移v3内容数组
    """转换已声明内容标签，参数与扩展数据保持不透明。"""
    if not isinstance(值,list):#须数组
        raise 会话格式错误(主语+' content must be an array')#错误
    已映射=[迁移块(块,主语+'['+str(下标)+']') for 下标,块 in enumerate(值)]#逐块
    if all(已映射[下标] is 值[下标] for 下标 in range(len(值))):#无变化
        return 值#原样
    return 已映射#新数组

def 迁移消息(消息,主语):#迁移消息内容
    """迁移一条消息的 content。"""
    内容=迁移v3内容(消息.get('content'),主语)#内容
    return 消息 if 内容 is 消息.get('content') else {**消息,'content':内容}#无变化则原样

def 迁移分块(值,主语):#迁移流分块
    """迁移 block-end / block-start 上的内容标签。"""
    if not 是否会话格式json对象(值):#非对象
        return 值#原样
    if 值.get('type')=='block-end':#结束块
        块=迁移块(值.get('block'),主语+'.block')#迁移block
        return 值 if 块 is 值.get('block') else {**值,'block':块}#写回
    if 值.get('type')!='block-start':#非起始
        return 值#原样
    原始=值.get('blockType')#块类型
    if not isinstance(原始,str):#须串
        raise 会话格式错误(主语+' blockType must be a string')#错误
    块类型=原始 if 原始 in v3块类型 else 'plugin:'+原始#加前缀
    return 值 if 块类型==原始 else {**值,'blockType':块类型}#写回

def 迁移v3事件内容(事件):#迁移v3事件内容
    """在规范结果提升之后转换已声明的 V3 扩展内容与流标签。"""
    主语='format v3 '+事件['type']+' at seq '+str(事件['seq'])#诊断主语
    def 变换消息(消息):#消息变换
        return 迁移消息(消息,主语)#委托
    已映射=映射事件消息(事件,变换消息)#映射消息
    if not 是否会话格式json对象(已映射.get('data')):#无对象载荷
        return 已映射#返回
    数据=已映射['data']#载荷
    def 内容字段(键):#迁移指定内容字段
        nonlocal 数据#写回
        内容=迁移v3内容(数据.get(键),主语+'.'+键)#迁移
        if 内容 is not 数据.get(键):#有变化
            数据={**数据,键:内容}#写回
    if 事件['type']=='compaction/summary':#压缩摘要
        内容字段('summary')#摘要
        if 'rawOutput' in 数据:#可选原文
            内容字段('rawOutput')#原文
    elif 事件['type']=='tool/ptc-dispatch':#ptc分发
        内容字段('content')#内容
    elif 事件['type']=='team/message/queued' and 是否会话格式json对象(数据.get('message')):#团队排队
        消息=迁移消息(数据['message'],主语)#迁移嵌套
        if 消息 is not 数据['message']:#有变化
            数据={**数据,'message':消息}#写回
    if 事件['type']=='request/header' and 是否会话格式json对象(数据.get('header')):#请求头
        工具列表=数据['header'].get('tools')#工具定义
        if isinstance(工具列表,list):#有工具
            for 下标,工具 in enumerate(工具列表):#逐项
                if 是否会话格式json对象(工具) and 'deferLoading' in 工具:#V4专用字段
                    raise 会话格式不支持迁移错误(#拒绝
                        主语+'.header.tools['+str(下标)+'] contains deferLoading, which is only defined in V4',#消息
                    )#Error结束
    if (事件['type']=='assistant/message' or 事件['type']=='assistant/attempt') and isinstance(数据.get('stream'),list):#内嵌流
        流=数据['stream']#流
        已转=[]#转换结果
        for 下标,条目 in enumerate(流):#逐条
            if not 是否会话格式json对象(条目) or 条目.get('type')!='chunk':#非chunk
                已转.append(条目)#原样
                continue#继续
            分块=迁移分块(条目.get('chunk'),主语+'.stream['+str(下标)+']')#迁移chunk
            已转.append(条目 if 分块 is 条目.get('chunk') else {**条目,'chunk':分块})#写回
        if any(已转[下标] is not 流[下标] for 下标 in range(len(流))):#有变化
            数据={**数据,'stream':已转}#写回
    if 数据 is not 已映射['data']:#载荷变了
        已映射={**已映射,'data':数据}#写回
    return 已映射#返回
