'DeepSeek Search API：一次搜索一次直接请求，不另发模型请求'
import re
from urllib.parse import urlparse as 解析网址
from .传输 import (
    派发深度求索网页,
    有深度求索网页凭据,
    无效响应,
    是记录,
)

__all__=[
    '搜索接口提供方标识','网页接口基址','默认条数','网页接口指引',
    '映射搜索响应','深度求索搜索接口提供方',
]

搜索接口提供方标识='deepseek-search-api'
网页接口基址='https://api.deepseek.com/v1/tools'
默认条数=10
原问题最长=128
空白=re.compile(r'\s+')
网页接口指引={
    'plugin':'web-deepseek-api',
    'field':'baseURL',
    'label':'Search / Fetch API base URL',
    'page':'Web search',
}


def 可解析网址(文字):
    '基址可解析则为真，须有协议和主机'
    if not isinstance(文字,str) or len(文字)==0:
        return False
    结果=解析网址(文字)
    return len(结果.scheme)>0 and len(结果.netloc)>0


def 是正整数(值):
    '正整数请求上限。布尔不算'
    return (not isinstance(值,bool)) and isinstance(值,int) and 值>0


def 有界问题(问题):
    '空白收成单空格，只留前 128 个码位'
    if not isinstance(问题,str):
        折叠=''
    else:
        折叠=空白.sub(' ',问题).strip()
    if len(折叠)==0:
        return None
    return 折叠[:原问题最长]


def 映射搜索响应(响应):
    '校验 Search API 响应，并投影成网页服务的来源'
    if not 是记录(响应) or not isinstance(响应.get('results'),list):
        raise 无效响应()
    来源列表=[]
    for 条目 in 响应['results']:
        if not 是记录(条目) or not isinstance(条目.get('url'),str) or len(条目['url'])==0:
            raise 无效响应()
        if not isinstance(条目.get('title'),str) or not isinstance(条目.get('snippet'),str):
            raise 无效响应()
        if 'summary' in 条目 and 条目['summary'] is not None and not isinstance(条目['summary'],str):
            raise 无效响应()
        if 条目.get('date') is not None and not isinstance(条目.get('date'),str):
            raise 无效响应()
        来源={'url':条目['url']}
        if len(条目['title'])>0:
            来源['title']=条目['title']
        if len(条目['snippet'])>0:
            来源['snippet']=条目['snippet']
        if isinstance(条目.get('summary'),str) and len(条目['summary'])>0:
            来源['summary']=条目['summary']
        if isinstance(条目.get('date'),str) and len(条目['date'])>0:
            来源['publishedAt']=条目['date']
        来源列表.append(来源)
    return {'sources':来源列表,'truncated':False}


class 深度求索搜索接口提供方:
    'DeepSeek Search API 提供方。重定向在联系目标前拒绝'
    def __init__(自身,解析选项):
        '收下下一次搜索的选项'
        自身.解析选项=解析选项
        自身.id=搜索接口提供方标识

    def available(自身):
        '有凭据来源、基址可解析，且条数是正整数'
        选项=自身.解析选项()
        return 有深度求索网页凭据(选项) and 可解析网址(选项.get('baseURL')) and 是正整数(选项.get('count'))

    def search(自身,请求,信号=None):
        '按这一次的选项发一次搜索'
        选项=自身.解析选项()
        读取问题=选项.get('originalQuestion')
        问题=有界问题(None if 读取问题 is None else 读取问题())
        条数=选项['count']
        请求上限=请求['maxResults'] if 'maxResults' in 请求 and 请求['maxResults'] is not None else 条数
        体={
            'query':请求['query'],
            'count':条数 if 条数<请求上限 else 请求上限,
            'need_content':False,
        }
        if 问题 is not None:
            体['ori_question']=问题
        基址=re.sub(r'/+$','',选项['baseURL'])
        return 派发深度求索网页(选项,{
            'endpoint':基址+'/search',
            'body':体,
            'decode':映射搜索响应,
            'guidance':{'subject':'Search',**网页接口指引},
        },信号)
