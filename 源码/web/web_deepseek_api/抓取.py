'DeepSeek Fetch API：一次请求取回页面 Markdown，不另发模型请求'
import re
from urllib.parse import urlparse as 解析网址
from .搜索 import 网页接口指引
from .传输 import (
    派发深度求索网页,
    有深度求索网页凭据,
    无效响应,
    是记录,
)

__all__=['抓取接口提供方标识','深度求索抓取接口提供方']

抓取接口提供方标识='deepseek-fetch-api'


def 可解析网址(文字):
    '基址可解析则为真，须有协议和主机'
    if not isinstance(文字,str) or len(文字)==0:
        return False
    结果=解析网址(文字)
    return len(结果.scheme)>0 and len(结果.netloc)>0


class 深度求索抓取接口提供方:
    'DeepSeek Fetch API 提供方。成功时报告请求 URL 和 HTTP 200'
    def __init__(自身,解析选项):
        '收下下一次抓取的选项'
        自身.解析选项=解析选项
        自身.id=抓取接口提供方标识

    def available(自身):
        '有凭据来源且基址可解析'
        选项=自身.解析选项()
        return 有深度求索网页凭据(选项) and 可解析网址(选项.get('baseURL'))

    def fetch(自身,请求,信号=None):
        '按这一次的选项抓取页面 Markdown'
        选项=自身.解析选项()
        网址=请求['url']

        def 解码(载荷):
            '正文必须是字符串。状态固定为 200'
            if not 是记录(载荷) or not isinstance(载荷.get('content'),str):
                raise 无效响应()
            return {
                'url':网址,
                'statusCode':200,
                'body':{'kind':'text','content':载荷['content']},
                'truncated':False,
            }

        基址=re.sub(r'/+$','',选项['baseURL'])
        return 派发深度求索网页(选项,{
            'endpoint':基址+'/fetch',
            'body':{'url':网址},
            'decode':解码,
            'guidance':{'subject':'Fetch',**网页接口指引},
        },信号)
