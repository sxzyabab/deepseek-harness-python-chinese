"""`@deepseek-ai/dsh-web-fetch-http`：向 `ctx.web` 注册匿名公开 HTTP(S) `WebFetchProvider`。这是函数/命名空间插件（不是默认导出服务）：它注册进 seam 的抓取注册表，正如搜索提供方注册进搜索注册表。"""
import math#有限数判定
from ...依赖 import schemastery#外部依赖胶水
模式=schemastery.模式#导入配置校验
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

配置模式=模式.对象({#插件配置：提供方的传输与大小上限以及 User-Agent（全部有默认值）
    'maxUrlLength':模式.数字().默认(2048),#接受的请求 URL 最大长度
    'maxResponseBytes':模式.数字().默认(5000000),#响应正文最大字节数
    'maxBodyChars':模式.数字().默认(100000),#解码正文最大字符数
    'timeoutMs':模式.数字().默认(30000),#默认抓取超时毫秒，须在 Node 定时器范围内
    'maxRedirects':模式.数字().默认(5),#跟随的同源重定向跳数上限
    'userAgent':模式.字符串().默认(默认用户代理),#每次请求发送的 User-Agent 头
})#配置模式结束
Config=配置模式#Cordis 配置模式

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 断言正有限(名称字,值):#校验正有限数
    """资源上限（字节/字符/长度/超时封顶）必须是正有限数。"""
    if isinstance(值,bool) or not isinstance(值,(int,float)) or not math.isfinite(值) or 值<=0:#非正或非有限
        raise Exception('web-fetch-http: '+名称字+' must be a positive finite number')#字段名进入错误文案

def 断言超时毫秒(值):#校验超时在 Node 定时器范围内
    """Node 会把更大的定时器延迟钳成 1 ms，因此在配置时拒绝它们。"""
    断言正有限('timeoutMs',值)#先要求正有限
    if 值>定时器延迟上限毫秒:#超过 Node 定时器上限
        raise Exception('web-fetch-http: timeoutMs must be no greater than '+str(定时器延迟上限毫秒))#拒绝过大延迟

def 断言非负整数(名称字,值):#校验非负整数
    """重定向跳数上限必须是非负整数（0 表示不跟随重定向）。"""
    if isinstance(值,bool):#布尔不是整数
        raise Exception('web-fetch-http: '+名称字+' must be a non-negative integer')#字段名进入错误文案
    if isinstance(值,int):#整型
        if 值<0:#为负
            raise Exception('web-fetch-http: '+名称字+' must be a non-negative integer')#字段名进入错误文案
        return#合格
    if isinstance(值,float) and 值.is_integer() and 值>=0:#整值非负浮点
        return#合格
    raise Exception('web-fetch-http: '+名称字+' must be a non-negative integer')#字段名进入错误文案

def 应用(上下文对象,配置):#向 ctx.web 注册本地 HTTP(S) 抓取提供方
    """向 `ctx.web` 注册本地 HTTP(S) 抓取提供方。"""
    已解析=配置#schemastery（Config）已经填完每个有默认值的字段
    断言正有限('maxUrlLength',取字段(已解析,'maxUrlLength'))#校验 URL 长度
    断言正有限('maxResponseBytes',取字段(已解析,'maxResponseBytes'))#校验正文字节
    断言正有限('maxBodyChars',取字段(已解析,'maxBodyChars'))#校验解码字符
    断言超时毫秒(取字段(已解析,'timeoutMs'))#校验超时
    断言非负整数('maxRedirects',取字段(已解析,'maxRedirects'))#校验重定向跳数
    上限={#组装传输上限
        'maxUrlLength':取字段(已解析,'maxUrlLength'),#URL 长度
        'maxResponseBytes':取字段(已解析,'maxResponseBytes'),#正文字节
        'maxBodyChars':取字段(已解析,'maxBodyChars'),#解码字符
        'timeoutMs':取字段(已解析,'timeoutMs'),#超时
        'maxRedirects':取字段(已解析,'maxRedirects'),#重定向跳数
        'userAgent':取字段(已解析,'userAgent'),#UA
    }#上限结束
    上下文对象.web.注册抓取提供方(HTTP抓取提供方(上限))#注册进抓取注册表

apply=应用#Cordis插件入口
default=应用#默认导出
默认=应用#中文默认导出
