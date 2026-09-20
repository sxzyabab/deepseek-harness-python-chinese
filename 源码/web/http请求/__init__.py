"""向 web 注册匿名公开 HTTP(S) 抓取提供方。"""
import math
from ...依赖.schemastery import 字符串字段,数字字段
from .提供方 import (
    HTTP抓取提供方,
    本地抓取提供方标识,
    HTTP抓取上限字段,
)

__all__=['包名','名称','依赖','应用','默认','配置模式']

定时器延迟上限毫秒=2147483647#Node 定时器延迟上限；更大值会被钳成 1ms
默认用户代理='deepseek-harness/0.0.1 (+https://github.com/deepseek-ai)'#产品代理，不是浏览器伪装

包名='@deepseek-ai/dsh-web-fetch-http'
名称='web-fetch-http'
依赖=['web']
配置模式={
    'maxUrlLength':数字字段(默认值=2048),#接受的请求 URL 最大长度
    'maxResponseBytes':数字字段(默认值=5000000),#响应正文最大字节数
    'maxBodyChars':数字字段(默认值=100000),#解码正文最大字符数
    'timeoutMs':数字字段(默认值=30000),#默认抓取超时毫秒，须在定时器延迟上限内
    'maxRedirects':数字字段(默认值=5),#跟随的同源重定向跳数上限
    'userAgent':字符串字段(默认值=默认用户代理),#每次请求发送的 User-Agent 头
}

class 抓取配置错误(Exception):
    """web-fetch-http 配置校验失败。"""

def 断言正有限(名称字,值):
    """资源上限（字节/字符/长度/超时封顶）必须是正有限数。"""
    if isinstance(值,bool) or not isinstance(值,(int,float)) or not math.isfinite(值) or 值<=0:
        raise 抓取配置错误('web-fetch-http: '+名称字+' must be a positive finite number')

def 断言超时毫秒(值):
    """超出定时器延迟上限的值会被钳成 1ms，因此在配置时拒绝。"""
    断言正有限('timeoutMs',值)
    if 值>定时器延迟上限毫秒:
        raise 抓取配置错误('web-fetch-http: timeoutMs must be no greater than '+str(定时器延迟上限毫秒))

def 断言非负整数(名称字,值):
    """重定向跳数上限必须是非负整数（0 表示不跟随重定向）。"""
    if isinstance(值,bool):
        raise 抓取配置错误('web-fetch-http: '+名称字+' must be a non-negative integer')
    if isinstance(值,int):
        if 值<0:
            raise 抓取配置错误('web-fetch-http: '+名称字+' must be a non-negative integer')
        return
    if isinstance(值,float) and 值.is_integer() and 值>=0:
        return
    raise 抓取配置错误('web-fetch-http: '+名称字+' must be a non-negative integer')

def 应用(上下文,配置):
    """向 web 注册本地 HTTP(S) 抓取提供方。配置为 dict。"""
    已解析=配置
    断言正有限('maxUrlLength',已解析['maxUrlLength'])
    断言正有限('maxResponseBytes',已解析['maxResponseBytes'])
    断言正有限('maxBodyChars',已解析['maxBodyChars'])
    断言超时毫秒(已解析['timeoutMs'])
    断言非负整数('maxRedirects',已解析['maxRedirects'])
    上限={
        'maxUrlLength':已解析['maxUrlLength'],
        'maxResponseBytes':已解析['maxResponseBytes'],
        'maxBodyChars':已解析['maxBodyChars'],
        'timeoutMs':已解析['timeoutMs'],
        'maxRedirects':已解析['maxRedirects'],
        'userAgent':已解析['userAgent'],
    }
    上下文.web.注册抓取提供方(HTTP抓取提供方(上限))

默认=应用
name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
Config=配置模式#框架槽
default=默认#框架槽
