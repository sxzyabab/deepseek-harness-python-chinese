"""从冻结调用切片纯派生 web 卡片 props。

对齐上游 `ui-tool/src/client/tool/models/web-card-model.ts`。公开面仅中文名。
"""

__all__=['网页卡模型']#仅中文公开名

def 网页卡模型(块):#从调用切片派生 web 卡片 props
    """非 web 卡片返回 None。"""
    if 'kind' not in 块:#仍在跑
        return None#通用路径
    结果=块['resultView'] if 'resultView' in 块 else None#结果视图
    if 结果 is None or 结果['card']!='web':#不是 web
        return None#通用路径
    种类=结果['kind']#kind
    if 种类=='search':#检索结果
        来源列表=[]#来源
        源列=结果['sources'] if 'sources' in 结果 and 结果['sources'] is not None else []#来源
        for 源 in 源列:#逐条
            来源列表.append({#卡片条目
                'url':源['url'],'title':源['title'],
                'snippet':源['snippet'] if 'snippet' in 源 else None,
                'publishedAt':源['publishedAt'] if 'publishedAt' in 源 else None,
            })#条目
        return {'kind':'search','answer':结果['answer'] if 'answer' in 结果 else None,'sources':来源列表,'truncated':结果['truncated'] if 'truncated' in 结果 else None}#search
    if 种类=='fetch':#抓取结果
        return {#fetch 形
            'kind':'fetch','url':结果['url'],
            'statusCode':结果['statusCode'] if 'statusCode' in 结果 else None,
            'truncated':结果['truncated'] if 'truncated' in 结果 else None,
        }#fetch
    return None#未知 kind
