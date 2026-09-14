__all__=['聊天差异最大行数','收窄差异','差异卡模型']#仅中文公开名

聊天差异最大行数=8#聊天行折叠前的 diff 最大行数

def 收窄差异(差异列表):#收窄 diffs 为合法 hunk 或 None
    """非数组或空或畸形则 None。"""
    if not isinstance(差异列表,list) or len(差异列表)==0:#不可用
        return None#None
    输出=[]#已校验
    for 块 in 差异列表:#逐项
        if not isinstance(块,dict):#非对象
            return None#整份不可用
        if 'path' not in 块:#缺 path
            return None#不可用
        路径=块['path']#path
        旧=块['oldText'] if 'oldText' in 块 else None#oldText
        if 'newText' not in 块:#缺 newText
            return None#不可用
        新=块['newText']#newText
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
    if 'kind' not in 块:#仍在跑
        调用视图=块['callView'] if 'callView' in 块 else None#调用视图
        调用=调用视图 if 调用视图 is not None and 调用视图['card']=='diff' else None#仅 diff
        差异=None if 调用 is None else 收窄差异(调用['diffs'] if 'diffs' in 调用 else None)#收窄
        return None if 差异 is None else {'card':{'diffs':差异}}#模型
    结果视图=块['resultView'] if 'resultView' in 块 else None#结果视图
    结果=结果视图 if 结果视图 is not None and 结果视图['card']=='diff' else None#仅 diff
    差异=None if 结果 is None else 收窄差异(结果['diffs'] if 'diffs' in 结果 else None)#收窄
    return None if 差异 is None else {'card':{'diffs':差异}}#模型
