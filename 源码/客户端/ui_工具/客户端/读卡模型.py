"""从冻结调用切片纯派生读卡道具。

对齐上游 `ui-tool/src/client/tool/models/read-card-model.ts`。公开面仅中文名。
"""
from .调用模型 import 取字段,相对化到工作区#字段与相对化

__all__=['聊天读最大行数','读卡模型','CHAT_READ_MAX_LINES','readCardModel']#仅中文公开名

聊天读最大行数=8#聊天行驻留读正文折叠前行数上限
CHAT_READ_MAX_LINES=聊天读最大行数#上游名

def 读卡模型(块,会话工作区=None):#从调用块派生读卡道具
    """进行中或非读卡返回 None。"""
    if 取字段(块,'kind') is None and not (isinstance(块,dict) and 'kind' in 块):#进行中
        return None#通用路径
    结果视图=取字段(块,'resultView')#结果视图
    结果=结果视图 if 取字段(结果视图,'card')=='read' else None#仅 read
    if 结果 is None:#非读卡
        return None#通用路径
    行们=[]#拷入原语行形
    for 行 in 取字段(结果,'lines') or []:#逐行
        行们.append({'number':取字段(行,'number'),'text':取字段(行,'text')})#拷贝
    标题=取字段(结果,'title')#替换标题
    标签=标题 if 标题 is not None else 相对化到工作区(取字段(结果,'path') or '',会话工作区)#标签
    return {#读卡道具
        'label':标签,'lines':行们,
        'totalLines':取字段(结果,'totalLines'),'lang':取字段(结果,'lang'),
    }#模型

readCardModel=读卡模型#上游名
