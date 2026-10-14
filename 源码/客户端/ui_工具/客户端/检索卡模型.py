__all__=['聊天检索最大行数','检索卡模型']

聊天检索最大行数=8

def 合法文件列表(文件列表):
    '须是数组且每个分组都合法'
    if not isinstance(文件列表,list):
        return False
    for 文件 in 文件列表:
        if not isinstance(文件,dict):
            return False
        if 'path' not in 文件 or not isinstance(文件['path'],str):
            return False
        匹配列表=文件['matches'] if 'matches' in 文件 else None
        if not isinstance(匹配列表,list):
            return False
        for 匹配 in 匹配列表:
            if not isinstance(匹配,dict):
                return False
            行号=匹配['lineNumber'] if 'lineNumber' in 匹配 else None
            if not isinstance(行号,(int,float)) or isinstance(行号,bool):
                return False
            if 'line' not in 匹配 or not isinstance(匹配['line'],str):
                return False
    return True

def 展平内容(内容):
    '空则 None'
    段列表=[]
    块列表=内容 if 内容 is not None else []
    for 块 in 块列表:
        if isinstance(块,dict) and 'type' in 块 and 块['type']=='text' and 'text' in 块 and isinstance(块['text'],str):
            段列表.append(块['text'])
    文本='\n'.join(段列表)
    return None if 文本=='' else 文本

def 检索卡模型(块):
    '非 search 则 None'
    if 'kind' not in 块:
        return None
    结果视图=块['resultView'] if 'resultView' in 块 else None
    结果=结果视图 if 结果视图 is not None and 结果视图['card']=='search' else None
    if 结果 is None:
        return None
    共用={'truncated':结果['truncated'] if 'truncated' in 结果 else None,'total':结果['total'] if 'total' in 结果 else None}
    截断=结果['truncated'] if 'truncated' in 结果 else False
    恢复=展平内容(块['content'] if 'content' in 块 else None) if 截断 else None
    形=结果['shape'] if 'shape' in 结果 else None
    if 形=='matches':
        文件列表=结果['files'] if 'files' in 结果 else None
        if not 合法文件列表(文件列表):
            return None
        return {'title':结果['title'] if 'title' in 结果 else None,'recovery':恢复,'card':{'kind':'matches','files':文件列表,**共用}}
    if 形!='paths':
        return None
    路径列表=结果['paths'] if 'paths' in 结果 else None
    if not isinstance(路径列表,list) or not all(isinstance(项,str) for 项 in 路径列表):
        return None
    return {'title':结果['title'] if 'title' in 结果 else None,'recovery':恢复,'card':{'kind':'paths','paths':路径列表,**共用}}
