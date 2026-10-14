__all__=['网页卡模型']

def 网页卡模型(块):
    '非网页卡片返回 None'
    if 'kind' not in 块:
        return None
    结果=块['resultView'] if 'resultView' in 块 else None
    if 结果 is None or 结果['card']!='web':
        return None
    种类=结果['kind']
    if 种类=='search':
        来源列表=[]
        源列=结果['sources'] if 'sources' in 结果 and 结果['sources'] is not None else []
        for 源 in 源列:
            来源列表.append({
                'url':源['url'],'title':源['title'],
                'snippet':源['snippet'] if 'snippet' in 源 else None,
                'publishedAt':源['publishedAt'] if 'publishedAt' in 源 else None,
            })
        return {'kind':'search','answer':结果['answer'] if 'answer' in 结果 else None,'sources':来源列表,'truncated':结果['truncated'] if 'truncated' in 结果 else None}
    if 种类=='fetch':
        return {
            'kind':'fetch','url':结果['url'],
            'statusCode':结果['statusCode'] if 'statusCode' in 结果 else None,
            'truncated':结果['truncated'] if 'truncated' in 结果 else None,
        }
    return None
