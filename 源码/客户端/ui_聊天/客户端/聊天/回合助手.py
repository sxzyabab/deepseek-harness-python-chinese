"""从一个助手生命周期收集可见散文。

对齐上游 `ui-chat/src/client/chat/turn-assistant.ts`。公开面仅中文名。
块为快照 dict。
"""

__all__=['助手文本']#仅中文公开名

def 助手文本(块列表):
    """只拼 text 块。"""
    文列表=[]#累积
    序列=块列表 if 块列表 is not None else []#缺则空
    for 块 in 序列:#逐块
        if 'kind' in 块 and 块['kind']=='text':#文本
            文=块['text'] if 'text' in 块 and 块['text'] is not None else ''#文
            文列表.append(文)#收
    return ''.join(文列表)#拼接
