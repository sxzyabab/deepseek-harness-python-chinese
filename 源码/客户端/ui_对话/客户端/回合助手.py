"""助手生命周期可见正文收集。

对齐上游 `ui-conversation/src/client/chat/turn-assistant.ts`。公开面仅中文名。
块为快照 dict。
"""

__all__=['助手文本']#仅中文公开名

def 助手文本(块列表):
    """非 text 丢弃，按序拼接。"""
    段=[]#段
    序列=块列表 if 块列表 is not None else []#缺则空
    for 块 in 序列:#逐块
        if 'kind' in 块 and 块['kind']=='text':#正文
            文=块['text'] if 'text' in 块 and 块['text'] is not None else ''#加
            段.append(文)#加
    return ''.join(段)#拼
