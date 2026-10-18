from urllib.parse import urlparse
from .原始工具调用 import 解析工具调用

__all__=['网页卡模型','网页获取链接']

def 合法网页调用(块):
    'web_search 的 queries 或 web_fetch 的 url'
    已解析=解析工具调用(块)
    if 已解析 is None:
        return None
    if 已解析['name']=='web_search':
        查询=已解析['args'].get('queries')
        if not isinstance(查询,list) or len(查询)==0:
            return None
        for 项 in 查询:
            if not isinstance(项,str) or 项.strip()=='':
                return None
        return 已解析['name']
    if 已解析['name']=='web_fetch':
        网址=已解析['args'].get('url')
        if isinstance(网址,str) and 网址.strip()!='':
            return 已解析['name']
    return None

def 网页来源(值):
    '每条至少有 url'
    if not isinstance(值,list):
        return None
    来源表=[]
    for 来源 in 值:
        if not isinstance(来源,dict):
            return None
        网址=来源.get('url')
        if not isinstance(网址,str):
            return None
        条目={'url':网址}
        for 键 in ('title','snippet','publishedAt'):
            if 键 in 来源:
                if not isinstance(来源[键],str):
                    return None
                条目[键]=来源[键]
        来源表.append(条目)
    return 来源表

def 网页卡模型(块):
    '非根网页卡片返回 None'
    if 块.get('parentCallId') is not None or 'kind' not in 块 or 块.get('isError') is True:
        return None
    工具=合法网页调用(块)
    元数据=块.get('meta')
    if 工具 is None or not isinstance(元数据,dict):
        return None
    if not isinstance(元数据.get('truncated'),bool):
        return None
    if 工具=='web_search':
        来源=网页来源(元数据.get('sources'))
        if 来源 is None:
            return None
        if 'answer' in 元数据 and not isinstance(元数据.get('answer'),str):
            return None
        结果={'kind':'search','sources':来源,'truncated':元数据['truncated']}
        if 'answer' in 元数据:
            结果['answer']=元数据['answer']
        return 结果
    if not isinstance(元数据.get('url'),str):
        return None
    状态码=元数据.get('statusCode')
    if isinstance(状态码,bool) or not isinstance(状态码,int):
        return None
    return {
        'kind':'fetch',
        'url':元数据['url'],
        'statusCode':状态码,
        'truncated':元数据['truncated'],
    }

def 网页获取链接(块):
    'web_fetch 参数里的 http 或 https。其他协议或无法解析则没有'
    已解析=解析工具调用(块)
    if 已解析 is None or 已解析['name']!='web_fetch':
        return None
    网址=已解析['args'].get('url')
    if not isinstance(网址,str):
        return None
    try:
        解析=urlparse(网址)
    except ValueError:
        return None
    if 解析.scheme=='http' or 解析.scheme=='https':
        return 网址
    return None
