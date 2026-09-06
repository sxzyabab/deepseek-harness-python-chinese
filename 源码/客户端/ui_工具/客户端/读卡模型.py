"""从冻结调用切片纯派生读卡道具。

对齐上游 `ui-tool/src/client/tool/models/read-card-model.ts`。公开面仅中文名。
"""
from .调用模型 import 相对化到工作区#相对化

__all__=['聊天读最大行数','读卡模型']#仅中文公开名

聊天读最大行数=8#聊天行驻留读正文折叠前行数上限

def 读卡模型(块,会话工作区=None):#从调用块派生读卡道具
    """进行中或非读卡返回 None。"""
    if 'kind' not in 块:#进行中
        return None#通用路径
    结果视图=块['resultView'] if 'resultView' in 块 else None#结果视图
    结果=结果视图 if 结果视图 is not None and 结果视图['card']=='read' else None#仅 read
    if 结果 is None:#非读卡
        return None#通用路径
    行列表=[]#拷入原语行形
    原文行=结果['lines'] if 'lines' in 结果 and 结果['lines'] is not None else []#逐行
    for 行 in 原文行:#逐行
        行列表.append({'number':行['number'],'text':行['text']})#拷贝
    标题=结果['title'] if 'title' in 结果 else None#替换标题
    路径=结果['path'] if 'path' in 结果 and 结果['path'] is not None else ''#路径
    标签=标题 if 标题 is not None else 相对化到工作区(路径,会话工作区)#标签
    return {#读卡道具
        'label':标签,'lines':行列表,
        'totalLines':结果['totalLines'] if 'totalLines' in 结果 else None,
        'lang':结果['lang'] if 'lang' in 结果 else None,
    }#模型
