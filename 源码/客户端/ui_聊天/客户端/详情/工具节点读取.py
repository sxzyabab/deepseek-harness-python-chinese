"""经内部节点 store 查找任意根级或嵌套工具生命周期。

对齐上游 `ui-chat/src/client/details/tool-node-reader.ts`。公开面仅中文名。
"""

__all__=['查找工具调用']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """映射或属性。"""
    if 对象 is None:#空
        return 缺省#缺
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 工具节点(节点):#窄化为工具调用节点
    """非工具则 None。"""
    return 节点 if 取字段(节点,'kind')=='tool-call' else None#窄化

def 查找工具调用(快照,调用标识):#按 callId 找工具块
    """已在加载窗口物化时的当前工具生命周期。"""
    def 访问(块):#深度优先
        """命中本块或子树。"""
        if 取字段(块,'callId')==调用标识:#命中
            return 块#返
        for 子 in 取字段(块,'subCalls') or []:#子
            找到=访问(子)#递归
            if 找到 is not None:#命中
                return 找到#返
        return None#未命中
    节点们=取字段(快照,'nodes')#节点 store
    值们=节点们.values() if hasattr(节点们,'values') else []#全部
    for 节点 in 值们:#扫
        根=取字段(取字段(工具节点(节点),'data'),'root')#根块
        if 根 is None:#非工具
            continue#跳
        找到=访问(根)#找
        if 找到 is not None:#命中
            return 找到#返
    return None#窗口内无
