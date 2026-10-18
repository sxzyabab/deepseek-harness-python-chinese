__all__=['有助手回复内容']


def 有助手回复内容(块列表):
    '有面对用户的回复。只有推理或工具调用协议不算'
    for 块 in 块列表:
        种类=块.get('kind')
        if 种类=='reasoning' or 种类=='tool-call':
            continue
        if 种类=='text':
            文=块.get('text')
            if isinstance(文,str) and 文.strip()!='':
                return True
            continue
        return True
    return False
