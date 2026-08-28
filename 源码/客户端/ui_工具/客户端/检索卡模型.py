"""从冻结调用切片纯派生 search 卡片 props。

对齐上游 `ui-tool/src/client/tool/models/search-card-model.ts`。公开面仅中文名。
"""
from .调用模型 import 取字段#读字段

__all__=['聊天检索最大行数','检索卡模型','CHAT_SEARCH_MAX_LINES','searchCardModel']#仅中文公开名

聊天检索最大行数=8#聊天行 search 正文折叠前最大行数
CHAT_SEARCH_MAX_LINES=聊天检索最大行数#上游名

def 合法文件们(文件们):#files 是否为合法 SearchFileGroup 数组
    """须是数组且每个分组都合法。"""
    if not isinstance(文件们,list):#非数组
        return False#非法
    for 文件 in 文件们:#每个分组
        if not isinstance(文件,dict) or 文件 is None:#非对象
            return False#非法
        if not isinstance(文件.get('path'),str):#path
            return False#非法
        匹配们=文件.get('matches')#matches
        if not isinstance(匹配们,list):#非数组
            return False#非法
        for 匹配 in 匹配们:#每条
            if not isinstance(匹配,dict) or 匹配 is None:#非对象
                return False#非法
            if not isinstance(匹配.get('lineNumber'),(int,float)) or isinstance(匹配.get('lineNumber'),bool):#行号
                return False#非法
            if not isinstance(匹配.get('line'),str):#行文本
                return False#非法
    return True#合法

def 展平内容(内容):#把内容块展平为文本
    """空则 None。"""
    段们=[]#文本
    for 块 in 内容 or []:#块
        if 取字段(块,'type')=='text' and isinstance(取字段(块,'text'),str):#文本块
            段们.append(取字段(块,'text'))#收下
    文本='\n'.join(段们)#拼接
    return None if 文本=='' else 文本#空当缺席

def 检索卡模型(块):#从工具调用派生 search 卡片
    """非 search 则 None。"""
    if 取字段(块,'kind') is None and not (isinstance(块,dict) and 'kind' in 块):#运行中
        return None#通用路径
    结果视图=取字段(块,'resultView')#结果视图
    结果=结果视图 if 取字段(结果视图,'card')=='search' else None#仅 search
    if 结果 is None:#非 search
        return None#通用路径
    共用={'truncated':取字段(结果,'truncated'),'total':取字段(结果,'total')}#共用
    恢复=展平内容(取字段(块,'content')) if 取字段(结果,'truncated') else None#截断才恢复
    形=取字段(结果,'shape')#shape
    if 形=='matches':#匹配分组
        if not 合法文件们(取字段(结果,'files')):#files 不合法
            return None#通用路径
        return {'title':取字段(结果,'title'),'recovery':恢复,'card':{'kind':'matches','files':取字段(结果,'files'),**共用}}#matches
    if 形!='paths':#不是 paths
        return None#通用路径
    路径们=取字段(结果,'paths')#paths
    if not isinstance(路径们,list) or not all(isinstance(项,str) for 项 in 路径们):#须字符串数组
        return None#通用路径
    return {'title':取字段(结果,'title'),'recovery':恢复,'card':{'kind':'paths','paths':路径们,**共用}}#paths

searchCardModel=检索卡模型#上游名
