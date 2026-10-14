from .调用模型 import 相对化到工作区

__all__=['聊天读最大行数','读卡模型']

聊天读最大行数=8

def 读卡模型(块,会话工作区=None):
    '进行中或非读卡返回 None'
    if 'kind' not in 块:
        return None
    结果视图=块['resultView'] if 'resultView' in 块 else None
    结果=结果视图 if 结果视图 is not None and 结果视图['card']=='read' else None
    if 结果 is None:
        return None
    行列表=[]
    原文行=结果['lines'] if 'lines' in 结果 and 结果['lines'] is not None else []
    for 行 in 原文行:
        行列表.append({'number':行['number'],'text':行['text']})
    标题=结果['title'] if 'title' in 结果 else None
    路径=结果['path'] if 'path' in 结果 and 结果['path'] is not None else ''
    标签=标题 if 标题 is not None else 相对化到工作区(路径,会话工作区)
    return {
        'label':标签,'lines':行列表,
        'totalLines':结果['totalLines'] if 'totalLines' in 结果 else None,
        'lang':结果['lang'] if 'lang' in 结果 else None,
    }
