'浏览器客户端 RPC 的宿主 HTTP 桥'
import math#图像正文的 base64 膨胀
from ...依赖.schemastery import 自然数字段#天数和正文字节
from .http桥 import 桥接,默认最大请求正文字节#HTTP 桥与默认正文上限
from .接口路径 import 接口路径# /api
from .连接协议 import 连接路径# /connect
from .接口请求信任 import 断言受信任权威#权威必须是裸 host[:port]
from .浏览器认证 import 浏览器认证#启动令牌和饼干
from .rpc宿主 import 宿主连接服务#宿主连接服务
from .恢复流程配置 import 解析连接配置,恢复配置模式#恢复时序
from .异常 import 连接错误#正文上限不够
from .rpc import Rpc标识,传输错误#关联与传输失败
from .rpc数据架构 import (
    客户端请求模式,rpc错误模式,rpc标识模式,rpc消息模式,rpc结果模式,服务端响应模式,
)#信封模式
from .对等 import 对等#操作方
from . import (
    http桥,#桥
    rpc,#结果与中止
    rpc宿主,#宿主服务
    rpc数据架构,#信封
    接口路径 as 接口路径模块,#前缀
    接口请求信任,#围栏
    回环主机名,#回环
    对等 as 对等模块,#操作方模块
    浏览器认证 as 浏览器认证模块,#认证模块。类名已经占用 浏览器认证
    恢复流程配置,#时序
    连接协议,# /connect
    异常,#异常类
    客户端,#浏览器半边，不转发里面的类
)#同目录模块。导入时执行它们的顶层

__all__=[#同目录模块，以及 index 再导出的值。不转发客户端里面的类
    '名称','依赖','配置','应用','客户端','异常',
    'rpc','rpc宿主','http桥','连接协议','浏览器认证模块','接口请求信任',
    '恢复流程配置','rpc数据架构','接口路径模块','回环主机名','对等模块',
    'Rpc标识','传输错误','对等','连接路径','宿主连接服务','接口路径',
    '客户端请求模式','rpc错误模式','rpc标识模式','rpc消息模式','rpc结果模式','服务端响应模式',
]#公开名

名称='client-connection'#插件名
依赖=['credentials']#凭证
请求信封余量字节=1024*1024#图像 base64 之外的 JSON 余量


def 断言图像正文容量(上下文,最大请求正文字节):
    '有附件服务时，正文上限必须装得下合计图像的 base64 和信封'
    附件=上下文.获取服务('attachments')#可选
    if 附件 is None:#还没有附件服务
        return#不检查
    图像上限=附件.imageLimits['maxMessageImageBytes']#合计图像上限
    所需=math.ceil(图像上限*4/3)+请求信封余量字节#base64 膨胀后再加信封
    if 最大请求正文字节<所需:#配置上限不够
        raise 连接错误(#加载期失败
            'client-connection maxRequestBodyBytes ('+str(最大请求正文字节)+') must be at least '
            +str(所需)+' for the configured aggregate image limit',
        )#原文


class 连接配置:
    '浏览器认证、请求上限和恢复时序'
    天数字段=自然数字段(最小=1)#至少一天
    正文字段=自然数字段(最小=1)#至少一字节

    @classmethod
    def 校验数据(类,数据=None):
        '补默认值。布尔值不能当成整数。权威形态留到应用里检查'
        if 数据 is None:#没传
            数据={}#空
        if not isinstance(数据,dict):#必须是对象
            raise ValueError('connection config must be an object')#拒绝
        恢复=解析连接配置(数据['recovery'] if 'recovery' in 数据 else {})#时序
        if 'trustedHosts' in 数据:#写了
            主机=数据['trustedHosts']#原值
        else:#没写
            主机=[]#空名单
        if isinstance(主机,bool) or not isinstance(主机,list) or any(not isinstance(项,str) for 项 in 主机):#不是字符串列表
            raise ValueError('trustedHosts must be an array of strings')#拒绝
        if 'cookieMaxAgeDays' in 数据:#写了
            天数=数据['cookieMaxAgeDays']#原值
        else:#没写
            天数=30#30 天
        if isinstance(天数,bool):#布尔不是天数
            raise ValueError('cookieMaxAgeDays must be an integer')#拒绝
        类.天数字段.校验数据(天数)#至少 1
        if 'maxRequestBodyBytes' in 数据:#写了
            上限=数据['maxRequestBodyBytes']#原值
        else:#没写
            上限=默认最大请求正文字节#300 MiB
        if isinstance(上限,bool):#布尔不是字节数
            raise ValueError('maxRequestBodyBytes must be an integer')#拒绝
        类.正文字段.校验数据(上限)#至少 1
        return {#校验后的配置
            'recovery':恢复,#时序
            'trustedHosts':list(主机),#权威
            'cookieMaxAgeDays':天数,#饼干天数
            'maxRequestBodyBytes':上限,#正文上限
        }#配置结束


def 应用(上下文,配置值=None):
    '提供与载体无关的 RPC 和 Fetch 登记。有网页服务器时再挂上 /api 和 /connect'
    恢复=解析连接配置(None if 配置值 is None else 配置值.get('recovery'))#时序
    受信任主机表=[] if 配置值 is None or 'trustedHosts' not in 配置值 else 配置值['trustedHosts']#权威
    饼干天数=30 if 配置值 is None or 'cookieMaxAgeDays' not in 配置值 else 配置值['cookieMaxAgeDays']#天数
    最大请求正文字节=默认最大请求正文字节 if 配置值 is None or 'maxRequestBodyBytes' not in 配置值 else 配置值['maxRequestBodyBytes']#上限
    for 条目 in 受信任主机表:#逐条
        断言受信任权威(条目)#畸形就在加载时失败
    断言图像正文容量(上下文,最大请求正文字节)#有附件才核
    连接=宿主连接服务(上下文,受信任主机表,浏览器认证.创建(上下文.根,上下文.credentials,饼干天数))#宿主服务

    def 挂网页(网页上下文,配置=None):
        '挂上 /api 与 /connect，并把恢复时序注入索引'
        断言图像正文容量(网页上下文,最大请求正文字节)#网页服务器出现后再核一次
        共享处理=连接.createSharedFetchHandler(接口路径)#共享 fetch

        def 注入(表):
            '把恢复时序放进页面全局'
            表.append({'kind':'global','name':'__DSH_CONNECTION_RECOVERY__','value':恢复})#一行

        网页上下文.监听('webserver/index-inject',注入)#索引注入

        def 路由处理(节点请求,节点响应):
            '围栏和认证之后，瀑布可以包住共享桥'
            准入=连接.admit(节点请求)#准入
            if 'rejection' in 准入:#被拒绝
                节点响应.writeHead(准入['rejection'])#状态
                节点响应.end('unauthorized' if 准入['rejection']==401 else 'forbidden')#正文
                return#结束

            def 下一():
                '落到共享 API 桥'
                桥接(节点请求,节点响应,共享处理,准入['peer'],最大请求正文字节)#桥

            网页上下文.链式拦截('connection/request',节点请求,节点响应,下一)#瀑布

        接口路由={'kind':'prefix','path':接口路径,'handler':路由处理}# /api

        def 登记接口():
            '登记 /api'
            return 网页上下文.webServer.register(接口路由)#登记

        网页上下文.副作用(登记接口,'client-connection: /api route')# /api

        def 登记连接():
            '登记 /connect'
            return 网页上下文.webServer.register({#精确路由
                'kind':'exact',#精确
                'path':连接路径,# /connect
                'handler':连接.authorizeConnect,#交换令牌
            })#路由结束

        网页上下文.副作用(登记连接,'client-connection: /connect route')# /connect

    上下文.依赖启动(['webServer'],挂网页)#等网页服务器

    def 挂附件(附件上下文,配置=None):
        '附件限额出现后再核一次正文上限'
        断言图像正文容量(附件上下文,最大请求正文字节)#再核

    上下文.依赖启动(['attachments'],挂附件)#等附件


name=名称#框架槽
inject=依赖#框架槽
Config=连接配置#框架槽
apply=应用#框架槽
配置=连接配置#中文配置槽
RpcId=Rpc标识#index 再导出
transportError=传输错误#index 再导出
Peer=对等#index 再导出
CONNECT_PATH=连接路径#index 再导出
API_PATH=接口路径#index 再导出
HostConnectionService=宿主连接服务#index 再导出
clientRequestSchema=客户端请求模式#index 再导出
rpcErrorSchema=rpc错误模式#index 再导出
rpcIdSchema=rpc标识模式#index 再导出
rpcMessageSchema=rpc消息模式#index 再导出
rpcResultSchema=rpc结果模式#index 再导出
serverResponseSchema=服务端响应模式#index 再导出
ConnectionRecoveryConfigSchema=恢复配置模式#配置字段用的模式
