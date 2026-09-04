"""从一个助手生命周期收集可见散文。

对齐上游 `ui-chat/src/client/chat/turn-assistant.ts`。公开面仅中文名。
"""

__all__=['助手文本']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """映射或属性。"""
    if 对象 is None:#空
        return 缺省#缺
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 助手文本(块们):#收集助手可见文本
    """只拼 text 块。"""
    文们=[]#累积
    for 块 in 块们 or []:#逐块
        if 取字段(块,'kind')=='text':#文本
            文们.append(取字段(块,'text') or '')#收
    return ''.join(文们)#拼接
