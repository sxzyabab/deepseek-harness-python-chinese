"""经内部聊天节点索引读工具生命周期。

对齐上游 `ui-conversation/src/client/chat/tool-node-reader.ts`。公开面仅中文名。
"""

__all__=['根工具调用','查找工具调用','工具节点']#仅中文公开名

def 工具上下文键(种,标识):#拼聊天节点索引键
    """对齐 conversationContextKey。"""
    return f'{种}:{标识}'#种:id

def 取字段(对象,键,缺省=None):#读字段
    """映射或对象属性。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 工具节点(节点):#收窄成工具调用聊天节点
    """仅 kind 为 tool-call 时返回。"""
    if 节点 is None:#空
        return None#无
    if 取字段(节点,'kind')=='tool-call':#匹配
        return 节点#原样
    return None#否

def 根工具调用(快照,根调用标识):#按根调用 id 读根生命周期
    """当前窗口已物化则返回根块。"""
    聊天=取字段(快照,'chat')#聊天面
    节点表=取字段(聊天,'nodes')#节点表
    if 节点表 is None:#无表
        return None#无
    取=getattr(节点表,'get',None)#get
    节点=取(工具上下文键('tool-call',根调用标识)) if callable(取) else (节点表.get(工具上下文键('tool-call',根调用标识)) if isinstance(节点表,dict) else None)#取节点
    工具=工具节点(节点)#收窄
    if 工具 is None:#非工具
        return None#无
    数据=取字段(工具,'data')#数据
    return 取字段(数据,'root')#根生命周期

def 查找工具调用(快照,调用标识):#按调用 id 在根与嵌套中查找
    """深度优先走子调用树。"""
    def 访问(块):#DFS
        """命中本块或子树。"""
        if 取字段(块,'callId')==调用标识:#命中
            return 块#本块
        for 子 in (取字段(块,'subCalls') or []):#子调用
            命中=访问(子)#递归
            if 命中 is not None:#命中
                return 命中#短路
        return None#未命中

    聊天=取字段(快照,'chat')#聊天面
    节点表=取字段(聊天,'nodes')#节点表
    if 节点表 is None:#无表
        return None#无
    值们=getattr(节点表,'values',None)#values
    迭代=值们() if callable(值们) else (节点表.values() if isinstance(节点表,dict) else [])#遍历
    for 节点 in 迭代:#逐节点
        工具=工具节点(节点)#收窄
        根=取字段(取字段(工具,'data'),'root') if 工具 is not None else None#根
        if 根 is None:#非工具
            continue#跳过
        命中=访问(根)#查找
        if 命中 is not None:#命中
            return 命中#返回
    return None#未物化
