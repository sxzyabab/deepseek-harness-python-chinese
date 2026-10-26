'向 web 注册 DeepSeek Search 与 Fetch API 提供方'
import types
from ...依赖.schemastery import 字符串字段,整数字段,布尔字段
from .传输 import 凭据就绪,深度求索网页认证
from .搜索 import (
    搜索接口提供方标识,
    网页接口基址,
    默认条数,
    深度求索搜索接口提供方,
    映射搜索响应,
)
from .抓取 import 抓取接口提供方标识,深度求索抓取接口提供方
from . import 传输,搜索,抓取

__all__=[
    '名称','注入','配置','应用',
    '搜索接口提供方标识','抓取接口提供方标识','网页接口基址','默认条数',
    '深度求索搜索接口提供方','深度求索抓取接口提供方','映射搜索响应',
    '传输','搜索','抓取',
]

名称='web-deepseek-api'
注入=['web']


def 读易失(字段):
    '易失单元格读 get。普通值原样返回'
    if isinstance(字段,(dict,list,str,bytes,bytearray,bool,int,float)) or 字段 is None:
        return 字段
    取值=getattr(字段,'get',None)
    if callable(取值):
        return 取值()
    return 字段


def 易失(字段,角色=None):
    '标记运行中可更新。角色是设置面的 secret 或 credential-ref'
    元={'volatile':True}
    if 角色 is not None:
        元['role']=角色
    字段.meta=元
    return 字段


配置={
    'apiKey':易失(字符串字段(),'secret'),
    'apiKeyEnv':易失(字符串字段(默认值='DEEPSEEK_API_KEY'),'credential-ref'),
    'baseURL':易失(字符串字段(默认值=网页接口基址)),
    'count':易失(整数字段(最小=1,最大=50,默认值=默认条数)),
    'sendOriginalQuestion':易失(布尔字段(默认值=True)),
}


def 最近用户问题(会话):
    '当前轮次触发搜索的那条用户提示。别的 user 来源不算'
    if 会话 is None:
        return None
    命中=None
    for 消息 in 会话.派生消息():
        来源=消息.get('source') if isinstance(消息,dict) else None
        if isinstance(消息,dict) and 消息.get('role')=='user' and isinstance(来源,dict) and 来源.get('kind')=='user':
            命中=消息
    if 命中 is None:
        return None
    块列表=命中.get('content')
    if not isinstance(块列表,list):
        return None
    文本=[]
    for 块 in 块列表:
        if isinstance(块,dict) and 块.get('type')=='text' and isinstance(块.get('text'),str):
            文本.append(块['text'])
    return '\n'.join(文本)


def 应用(上下文,配置值):
    '注册两个提供方。每次操作重读这一份易失设置'
    def 密钥配置():
        '这一次的密钥和引用'
        return {
            'apiKey':读易失(配置值['apiKey']),
            'apiKeyEnv':读易失(配置值['apiKeyEnv']),
        }

    def 认证():
        '这一次的认证来源'
        return 深度求索网页认证(上下文,密钥配置())

    def 就绪(路由):
        '这一路由是否有可发送的凭据'
        当前=密钥配置()
        当前['baseURL']=读易失(配置值['baseURL'])
        return 凭据就绪(上下文,当前,路由)

    def 搜索选项():
        '这一次搜索的选项'
        选项=认证()
        选项['baseURL']=读易失(配置值['baseURL'])
        选项['count']=读易失(配置值['count'])
        if 读易失(配置值['sendOriginalQuestion']) is True:
            def 原问题():
                '发起会话里最近一条用户提示'
                智能体=上下文.获取服务('agents')
                发起方=None if 智能体 is None else 智能体.当前发起方()
                会话=None if 发起方 is None else 发起方.session
                return 最近用户问题(会话)
            选项['originalQuestion']=原问题
        return 选项

    def 抓取选项():
        '这一次抓取的选项'
        选项=认证()
        选项['baseURL']=读易失(配置值['baseURL'])
        return 选项

    搜索接口=深度求索搜索接口提供方(搜索选项)
    抓取接口=深度求索抓取接口提供方(抓取选项)

    def 搜索可用():
        '搜索提供方当前是否可注册使用'
        return 搜索接口.available()

    def 搜索一次(请求,信号=None):
        '跑一次搜索'
        return 搜索接口.search(请求,信号)

    def 抓取可用():
        '抓取提供方当前是否可注册使用'
        return 抓取接口.available()

    def 抓取一次(请求,信号=None):
        '跑一次抓取'
        return 抓取接口.fetch(请求,信号)

    登记=types.SimpleNamespace
    上下文.web.注册搜索提供方(登记(
        id=搜索接口.id,
        available=搜索可用,
        ready=就绪,
        search=搜索一次,
    ))
    上下文.web.注册抓取提供方(登记(
        id=抓取接口.id,
        available=抓取可用,
        ready=就绪,
        fetch=抓取一次,
    ))


name=名称
inject=注入
Config=配置
apply=应用
