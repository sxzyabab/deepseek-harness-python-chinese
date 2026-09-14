__all__=['聊天检索最大行数','检索卡模型']#仅中文公开名

聊天检索最大行数=8#聊天行 search 正文折叠前最大行数

def 合法文件列表(文件列表):#files 是否为合法 SearchFileGroup 数组
    """须是数组且每个分组都合法。"""
    if not isinstance(文件列表,list):#非数组
        return False#非法
    for 文件 in 文件列表:#每个分组
        if not isinstance(文件,dict):#非对象
            return False#非法
        if 'path' not in 文件 or not isinstance(文件['path'],str):#path
            return False#非法
        匹配列表=文件['matches'] if 'matches' in 文件 else None#matches
        if not isinstance(匹配列表,list):#非数组
            return False#非法
        for 匹配 in 匹配列表:#每条
            if not isinstance(匹配,dict):#非对象
                return False#非法
            行号=匹配['lineNumber'] if 'lineNumber' in 匹配 else None#行号
            if not isinstance(行号,(int,float)) or isinstance(行号,bool):#行号
                return False#非法
            if 'line' not in 匹配 or not isinstance(匹配['line'],str):#行文本
                return False#非法
    return True#合法

def 展平内容(内容):#把内容块展平为文本
    """空则 None。"""
    段列表=[]#文本
    块列表=内容 if 内容 is not None else []#块
    for 块 in 块列表:#块
        if isinstance(块,dict) and 'type' in 块 and 块['type']=='text' and 'text' in 块 and isinstance(块['text'],str):#文本块
            段列表.append(块['text'])#收下
    文本='\n'.join(段列表)#拼接
    return None if 文本=='' else 文本#空当缺席

def 检索卡模型(块):#从工具调用派生 search 卡片
    """非 search 则 None。"""
    if 'kind' not in 块:#运行中
        return None#通用路径
    结果视图=块['resultView'] if 'resultView' in 块 else None#结果视图
    结果=结果视图 if 结果视图 is not None and 结果视图['card']=='search' else None#仅 search
    if 结果 is None:#非 search
        return None#通用路径
    共用={'truncated':结果['truncated'] if 'truncated' in 结果 else None,'total':结果['total'] if 'total' in 结果 else None}#共用
    截断=结果['truncated'] if 'truncated' in 结果 else False#截断
    恢复=展平内容(块['content'] if 'content' in 块 else None) if 截断 else None#截断才恢复
    形=结果['shape'] if 'shape' in 结果 else None#shape
    if 形=='matches':#匹配分组
        文件列表=结果['files'] if 'files' in 结果 else None#files
        if not 合法文件列表(文件列表):#files 不合法
            return None#通用路径
        return {'title':结果['title'] if 'title' in 结果 else None,'recovery':恢复,'card':{'kind':'matches','files':文件列表,**共用}}#matches
    if 形!='paths':#不是 paths
        return None#通用路径
    路径列表=结果['paths'] if 'paths' in 结果 else None#paths
    if not isinstance(路径列表,list) or not all(isinstance(项,str) for 项 in 路径列表):#须字符串数组
        return None#通用路径
    return {'title':结果['title'] if 'title' in 结果 else None,'recovery':恢复,'card':{'kind':'paths','paths':路径列表,**共用}}#paths
