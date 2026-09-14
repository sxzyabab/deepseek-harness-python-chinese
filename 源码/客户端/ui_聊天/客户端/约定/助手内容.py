__all__=['有助手回复内容']#仅中文公开名

def 有助手回复内容(块列表):
    """非仅有推理或工具调用协议材料。块列表为 dict 列表。"""
    序列=块列表 if 块列表 is not None else []#缺则空
    for 块 in 序列:#逐块
        种=块['kind'] if 'kind' in 块 else None#种类
        if 种=='reasoning' or 种=='tool-call':#协议材料
            continue#不算
        if 种=='text':#文本
            文=块['text'] if 'text' in 块 and 块['text'] is not None else ''#文本
            if str(文).strip()!='':#非空白
                return True#有
            continue#空白跳过
        return True#图片等其他可见块
    return False#无
