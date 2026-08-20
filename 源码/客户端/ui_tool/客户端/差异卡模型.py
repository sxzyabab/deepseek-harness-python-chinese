"""从冻结调用切片纯推导 diff 卡片 props。

对齐上游 `ui-tool/src/client/tool/models/diff-card-model.ts`。公开面仅中文名。
"""
from .调用模型 import 取字段#读字段

__all__=['聊天差异最大行数','收窄差异','差异卡模型','CHAT_DIFF_MAX_LINES','diffCardModel']#仅中文公开名

聊天差异最大行数=8#聊天行折叠前的 diff 最大行数
CHAT_DIFF_MAX_LINES=聊天差异最大行数#上游名

def 收窄差异(差异们):#收窄 diffs 为合法 hunk 或 None
    """非数组或空或畸形则 None。"""
    if not isinstance(差异们,list) or len(差异们)==0:#不可用
        return None#None
    输出=[]#已校验
    for 块 in 差异们:#逐项
        if not isinstance(块,dict) or 块 is None:#非对象
            return None#整份不可用
        路径=块.get('path')#path
        旧=块.get('oldText')#oldText
        新=块.get('newText')#newText
        if not isinstance(路径,str):#path 必须字符串
            return None#不可用
        if 旧 is not None and not isinstance(旧,str):#oldText 只能 null 或字符串
            return None#不可用
        if not isinstance(新,str):#newText 必须字符串
            return None#不可用
        输出.append({'path':路径,'oldText':旧,'newText':新})#收下
    return 输出#全部通过

def 差异卡模型(块):#从调用块推导 diff 卡片或走通用路径
    """非 diff 卡片返回 None。"""
    if 取字段(块,'kind') is None and not (isinstance(块,dict) and 'kind' in 块):#仍在跑
        调用视图=取字段(块,'callView')#调用视图
        调用=调用视图 if 取字段(调用视图,'card')=='diff' else None#仅 diff
        差异=None if 调用 is None else 收窄差异(取字段(调用,'diffs'))#收窄
        return None if 差异 is None else {'card':{'diffs':差异}}#模型
    结果视图=取字段(块,'resultView')#结果视图
    结果=结果视图 if 取字段(结果视图,'card')=='diff' else None#仅 diff
    差异=None if 结果 is None else 收窄差异(取字段(结果,'diffs'))#收窄
    return None if 差异 is None else {'card':{'diffs':差异}}#模型

diffCardModel=差异卡模型#上游名
