"""从冻结调用切片纯派生 web 卡片 props。

对齐上游 `ui-tool/src/client/tool/models/web-card-model.ts`。公开面仅中文名。
"""
from .调用模型 import 取字段#读字段

__all__=['网页卡模型','webCardModel']#仅中文公开名

def 网页卡模型(块):#从调用切片派生 web 卡片 props
    """非 web 卡片返回 None。"""
    if 取字段(块,'kind') is None and not (isinstance(块,dict) and 'kind' in 块):#仍在跑
        return None#通用路径
    结果=取字段(块,'resultView')#结果视图
    if 取字段(结果,'card')!='web':#不是 web
        return None#通用路径
    种类=取字段(结果,'kind')#kind
    if 种类=='search':#检索结果
        来源们=[]#来源
        for 源 in 取字段(结果,'sources') or []:#逐条
            来源们.append({#卡片条目
                'url':取字段(源,'url'),'title':取字段(源,'title'),
                'snippet':取字段(源,'snippet'),'publishedAt':取字段(源,'publishedAt'),
            })#条目
        return {'kind':'search','answer':取字段(结果,'answer'),'sources':来源们,'truncated':取字段(结果,'truncated')}#search
    if 种类=='fetch':#抓取结果
        return {#fetch 形
            'kind':'fetch','url':取字段(结果,'url'),
            'statusCode':取字段(结果,'statusCode'),'truncated':取字段(结果,'truncated'),
        }#fetch
    return None#未知 kind

webCardModel=网页卡模型#上游名
