"""判断 Assistant 块是否含面向用户的回复。

对齐上游 `ui-chat/src/client/contract/assistant-content.ts`。公开面仅中文名。
注意：本文件对应 assistant-content；回合指标见 `回合指标.py`。
"""

__all__=['有助手回复内容']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """映射或属性。"""
    if 对象 is None:#空
        return 缺省#缺
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 有助手回复内容(块们):#是否有可见回复
    """非仅有推理或工具调用协议材料。"""
    for 块 in 块们 or []:#逐块
        种=取字段(块,'kind')#种类
        if 种=='reasoning' or 种=='tool-call':#协议材料
            continue#不算
        if 种=='text':#文本
            文=取字段(块,'text') or ''#文本
            if str(文).strip()!='':#非空白
                return True#有
            continue#空白跳过
        return True#图片等其他可见块
    return False#无
