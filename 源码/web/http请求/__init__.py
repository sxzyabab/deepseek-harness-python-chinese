"""`@deepseek-ai/dsh-web-fetch-http`：向 `ctx.web` 注册匿名公开 HTTP(S) `WebFetchProvider`。这是函数/命名空间插件（不是默认导出服务）：它注册进 seam 的抓取注册表，正如搜索提供方注册进搜索注册表。"""
import math#有限数判定
from ...依赖.schemastery import 字符串字段,数字字段#配置字段
from .提供方 import (
    HTTP抓取提供方,#提供方类
    本地抓取提供方标识,#本地抓取提供方 id
    HTTP抓取上限字段,#传输上限字段
)#提供方模块

__all__=['名称','注入','配置模式','应用','Config','name','inject']#公开面

定时器延迟上限毫秒=2147483647#Node 定时器延迟上限毫秒
默认用户代理='deepseek-harness/0.0.1 (+https://github.com/deepseek-ai)'#默认 UA：明确的产品代理，绝不是浏览器伪装

名称='web-fetch-http'#loader 诊断所用的 Cordis 插件名
注入=['web']#本提供方注册进去的 web seam
name=名称#Cordis插件名
inject=注入#Cordis依赖声明

配置模式={#插件配置：提供方的传输与大小上限以及 User-Agent（全部有默认值）
    'maxUrlLength':数字字段(默认值=2048),#接受的请求 URL 最大长度
    'maxResponseBytes':数字字段(默认值=5000000),#响应正文最大字节数
    'maxBodyChars':数字字段(默认值=100000),#解码正文最大字符数
    'timeoutMs':数字字段(默认值=30000),#默认抓取超时毫秒，须在 Node 定时器范围内
    'maxRedirects':数字字段(默认值=5),#跟随的同源重定向跳数上限
    'userAgent':字符串字段(默认值=默认用户代理),#每次请求发送的 User-Agent 头
}#配置模式结束
Config=配置模式#Cordis 配置模式

class 抓取配置错误(Exception):#本包加载时配置错误
    """web-fetch-http 配置校验失败。"""
    pass#消息在构造时传入

def 断言正有限(名称字,值):#校验正有限数；入口校验
    """资源上限（字节/字符/长度/超时封顶）必须是正有限数。"""
    if isinstance(值,bool) or not isinstance(值,(int,float)) or not math.isfinite(值) or 值<=0:#非正或非有限
        raise 抓取配置错误('web-fetch-http: '+名称字+' must be a positive finite number')#字段名进入错误文案

def 断言超时毫秒(值):#校验超时在 Node 定时器范围内
    """Node 会把更大的定时器延迟钳成 1 ms，因此在配置时拒绝它们。"""
    断言正有限('timeoutMs',值)#先要求正有限
    if 值>定时器延迟上限毫秒:#超过 Node 定时器上限
        raise 抓取配置错误('web-fetch-http: timeoutMs must be no greater than '+str(定时器延迟上限毫秒))#拒绝过大延迟

def 断言非负整数(名称字,值):#校验非负整数；先排除 bool
    """重定向跳数上限必须是非负整数（0 表示不跟随重定向）。"""
    if isinstance(值,bool):#布尔不是整数
        raise 抓取配置错误('web-fetch-http: '+名称字+' must be a non-negative integer')#字段名进入错误文案
    if isinstance(值,int):#整型
        if 值<0:#为负
            raise 抓取配置错误('web-fetch-http: '+名称字+' must be a non-negative integer')#字段名进入错误文案
        return#合格
    if isinstance(值,float) and 值.is_integer() and 值>=0:#整值非负浮点
        return#合格
    raise 抓取配置错误('web-fetch-http: '+名称字+' must be a non-negative integer')#字段名进入错误文案

def 应用(上下文对象,配置):#向 ctx.web 注册本地 HTTP(S) 抓取提供方
    """向 `ctx.web` 注册本地 HTTP(S) 抓取提供方。配置为 dict。"""
    已解析=配置#schemastery（Config）已经填完每个有默认值的字段
    断言正有限('maxUrlLength',已解析['maxUrlLength'])#校验 URL 长度
    断言正有限('maxResponseBytes',已解析['maxResponseBytes'])#校验正文字节
    断言正有限('maxBodyChars',已解析['maxBodyChars'])#校验解码字符
    断言超时毫秒(已解析['timeoutMs'])#校验超时
    断言非负整数('maxRedirects',已解析['maxRedirects'])#校验重定向跳数
    上限={#组装传输上限
        'maxUrlLength':已解析['maxUrlLength'],#URL 长度
        'maxResponseBytes':已解析['maxResponseBytes'],#正文字节
        'maxBodyChars':已解析['maxBodyChars'],#解码字符
        'timeoutMs':已解析['timeoutMs'],#超时
        'maxRedirects':已解析['maxRedirects'],#重定向跳数
        'userAgent':已解析['userAgent'],#UA
    }#上限结束
    上下文对象.web.注册抓取提供方(HTTP抓取提供方(上限))#注册进抓取注册表

apply=应用#Cordis插件入口
default=应用#默认导出
默认=应用#中文默认导出
