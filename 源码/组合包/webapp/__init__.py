"""浏览器表面组合包的运行时粘合插件。

对齐上游 `@deepseek-ai/dsh-web-app`。公开面仅中文名。

依赖 `host_frontend_static`、`webServer` 等宿主包；若尚未迁入则本包激活时会失败——见未迁移插件说明。
"""
import os,socket,webbrowser#路径、网卡与默认浏览器
from ...依赖.schemastery import 布尔字段,列表字段,字符串字段#配置字段
from ...启动.app启动 import 添加源码段落,审计启动条目#harness 源码段与启动审计
from ...工具.启动环境 import 取启动环境,经ssh拉起#SSH 拉起抑制开浏览器

__all__=['名称','注入','配置','应用','解析局域网信任','内部','网页启动服务键','网页错误']#仅中文公开名

名称='web-app'#插件名
注入=['webServer']#依赖 web 服务器
源码根=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..','..'))#相对本包上溯到中文源码树根旁
运行时服务键='webRuntime'#运行时服务名
网页地址环境键='DSH_WEB_URL'#bash 可见 URL 变量名
回环主机='127.0.0.1'#回环展示主机
全接口主机='0.0.0.0'#全接口绑定字面量

配置={#Web 应用配置
    'openBrowser':布尔字段(默认值=True),#默认打开浏览器
    'printUrl':布尔字段(默认值=True),#默认打印 URL
    'surfaceContext':布尔字段(默认值=True),#默认注册表面上下文
    'trustedHosts':列表字段(字符串字段(),默认值=[]),#默认无额外权威
}#配置结束
已宣告根=set()#已打印 URL 的根上下文身份

网页启动服务键='webStartup'#启动服务名（供补丁与启动模块共用）

class 网页错误(Exception):
    """Web 应用组合包失败。"""
    pass#消息在构造时传入

def 列举局域网地址():#采样非内部 IPv4
    """采样本机非内部 IPv4 字面量。"""
    地址列表=[]#地址
    try:#枚举网卡
        for 信息 in socket.getaddrinfo(socket.gethostname(),None):#解析主机名
            族,类型,协议,规范名,套接=信息#拆开
            if 族==socket.AF_INET:#IPv4
                主机=套接[0]#地址
                if not 主机.startswith('127.'):#非回环
                    if 主机 not in 地址列表:#去重
                        地址列表.append(主机)#收下
    except OSError:#枚举失败
        pass#空列表
    return 地址列表#局域网地址

def 解析局域网信任(绑定主机,额外):#解析局域网信任
    """从活动服务器绑定解析一份局域网信任快照。"""
    局域网=列举局域网地址() if 绑定主机==全接口主机 else []#全接口才采样
    return {'lanAddresses':局域网,'trustedHosts':list(局域网)+list(额外)}#局域网后接显式权威

def 网页表面提示词(网页地址):#拼 web 表面提示词
    """经 dsh web 创建的会话的模型可见定向与接受边界。"""
    更新约定=('The client-plugin HMR receiver is active, but client-plugin changes reload without a refresh only while '
        +'`pnpm run dev:web` is also running from this same checkout to rebuild their bundles; verify that watcher before promising automatic updates. '
        +'Every other change — the apps/web shell and plain packages — requires rebuilding the affected Web artifacts and verifying this existing URL after a page refresh. ')#更新约定
    return ('You are interacting with the user through the DeepSeek Harness Web GUI at '+网页地址+'. '
        +'When the user refers to "this page", "this GUI", or "this app" without naming another target, they mean this GUI. '
        +'The browser provides no implicit DOM, route, or screenshot context. '
        +更新约定
        +'Starting another server does not update this GUI. '
        +'The apps/web Vite entry builds the shell but is not a standalone application because only dsh web injects window.__DSH_BOOT__. '
        +'Do not start a replacement server unless the user asks; if one is needed, use a managed background job and verify its exact URL.')#完整表面提示词

def 本地网页地址(上下文):
    """从活动 Web 服务器解析规范回环 URL。"""
    服务器=上下文.获取服务('webServer')#web 服务器
    if 服务器 is None:#缺少服务
        raise 网页错误('web-app: webServer service missing while resolving Web runtime')#失败
    return 'http://'+回环主机+':'+str(服务器.port)#回环 URL

def 解析前端入口():#解析前端 dist 入口
    """dist 位置是本组合包的工作区知识。"""
    try:#尝试导入前端包
        import web_frontend#前端包
        路径=web_frontend.前端入口#中文入口
        if 路径 is not None:#有路径
            return 路径#入口
    except ImportError:#未安装
        pass#继续
    raise 网页错误('web-app: @deepseek-ai/dsh-web-frontend is not resolvable from this composition')#前端包不可解析

内部={'resolveDistIndex':解析前端入口,'openBrowser':webbrowser.open}#可替换的 dist 解析与开浏览器

def 应用(上下文,配置值):#安装 Web 运行时粘合
    """挂载 Web 运行时：dist 服务、表面提示词、bash 运行时变量，以及 URL 行。"""
    服务器=上下文.webServer#web 服务器
    额外=配置值['trustedHosts'] if 'trustedHosts' in 配置值 else []#额外权威；?? 缺席才空
    运行时=解析局域网信任(服务器.host,额外)#采样局域网信任
    快照=取启动环境(上下文)#启动环境
    交出浏览器=配置值['openBrowser'] is True if 'openBrowser' in 配置值 else True#默认开
    if 快照 is not None and 经ssh拉起(快照):#SSH 拉起
        交出浏览器=False#抑制
    上下文.提供服务(运行时服务键,运行时)#提供运行时服务
    try:#挂载前端静态
        import host_frontend_static as 前端静态#前端静态插件
        上下文.启动插件(前端静态,{'distIndex':内部['resolveDistIndex']()})#挂载
    except ImportError as 错误:#宿主包未迁
        raise 网页错误('web-app: host_frontend_static is not migrated yet') from 错误#阻塞
    if 'surfaceContext' in 配置值 and 配置值['surfaceContext']:#注册表面上下文
        def 提示词接线(提示上下文,*其余):#有系统提示词时注册段
            """登记 harness 源码段与 web 表面段。"""
            添加源码段落(提示上下文,源码根)#harness 源码段
            def 文本():#按当前 URL 生成
                """表面提示词文本。"""
                return 网页表面提示词(本地网页地址(提示上下文))#生成
            提示上下文.systemPrompt.段落({#web 表面段
                'name':'app:web-surface',#段名
                'order':提示上下文.systemPrompt.取段落序号('WEB_SURFACE'),#共享放置
                'text':文本,#按当前 URL
            })#section 结束
        上下文.依赖启动(['systemPrompt'],提示词接线)#依赖启动
        def 环境接线(运行时上下文,*其余):#有 shell 环境时注册变量
            """登记 DSH_WEB_URL。"""
            def 解析环境():
                """解析 DSH_WEB_URL。"""
                return {网页地址环境键:本地网页地址(运行时上下文)}#变量表
            运行时上下文.shellEnv.登记({#注册 web 运行时变量
                'name':'web-runtime',#注册名
                'variables':{#变量表
                    网页地址环境键:{'description':'Canonical local URL of the DeepSeek Harness Web GUI serving this session.'},#说明
                },#variables 结束
                'resolve':解析环境,#解析
            })#register 结束
        上下文.依赖启动(['shellEnv'],环境接线)#依赖启动
    if ('printUrl' in 配置值 and 配置值['printUrl']) or 交出浏览器:#打印就绪 URL 行或开浏览器
        def 打印地址():
            """打印回环与可选局域网，并按配置打开默认浏览器。"""
            根键=id(上下文.根)#根身份
            if 根键 in 已宣告根:#已宣告
                return#一次
            地址列表=运行时['lanAddresses']#局域网
            局域网候选=地址列表[0] if len(地址列表)>0 else None#第一个局域网
            端口=上下文.webServer.port#已绑定端口
            网页地址=本地网页地址(上下文)#回环
            连接=上下文.获取服务('connection',False)#连接服务
            认证地址=网页地址 if 连接 is None else 连接.authenticatedUrl(网页地址)#认证 URL
            局域网地址=None if 局域网候选 is None else (
                'http://'+局域网候选+':'+str(端口) if 连接 is None else 连接.authenticatedUrl('http://'+局域网候选+':'+str(端口))
            )#可选局域网
            已宣告根.add(根键)#记下
            if 'printUrl' in 配置值 and 配置值['printUrl']:#打印
                后缀='' if 局域网地址 is None else ' (LAN: '+局域网地址+')'#可选局域网
                print('dsh web: '+认证地址+后缀)#打印
            if 交出浏览器:#开浏览器
                print('dsh web: opening the default browser; pass --no-open to disable')#预告
                try:#打开
                    内部['openBrowser'](认证地址)#默认浏览器
                except OSError as 错误:#失败
                    print('web-app: could not open the default browser because '+str(错误)+'; use the dsh web URL printed at startup')#警告
        加载器=上下文.获取服务('loader')#Loader
        if 加载器 is None:#无 loader
            打印地址()#立刻打印
        else:#有 loader
            def 结算后():
                """服务仍在才打印。"""
                def 吞警告(行):
                    """审计可选失败不印到标准错误。"""
                    return#空
                try:#审计
                    审计启动条目(上下文.根,'dsh web',吞警告)#审计
                except 网页错误:#本包失败不应到这里
                    return#不宣告
                except Exception:#启动审计失败由 boot 拥有诊断
                    return#不宣告
                if 上下文.获取服务('webServer') is not None and 上下文.获取服务('connection') is not None:#服务仍在
                    打印地址()#打印
            try:#等待结算
                加载器.等待()#加载器.等待 已同步
                结算后()#打印
            except Exception:#加载器.等待 可抛插件启动错误
                pass#保持安静

name=名称#框架槽
inject=注入#框架槽
apply=应用#框架槽
Config=配置#框架槽

