"""浏览器表面组合包的运行时粘合插件。

依赖 `host_frontend_static`、`webServer` 等宿主包；缺包时激活会失败。
"""
import os,socket,webbrowser
from ...依赖.schemastery import 布尔字段,列表字段,字符串字段
from ...启动.app启动 import 添加源码段落,审计启动条目,启动错误
from ...工具.启动环境 import 取启动环境,经ssh拉起#SSH 拉起时抑制打开浏览器

__all__=['名称','依赖','配置','应用','解析局域网信任','内部','网页启动服务键','网页错误']

名称='web-app'
依赖=['webServer']
源码根=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..','..'))
运行时服务键='webRuntime'
网页地址环境键='DSH_WEB_URL'
回环主机='127.0.0.1'
全接口主机='0.0.0.0'

配置={
    'openBrowser':布尔字段(默认值=True),
    'printUrl':布尔字段(默认值=True),
    'surfaceContext':布尔字段(默认值=True),
    'trustedHosts':列表字段(字符串字段(),默认值=[]),
}
已宣告根=set()

网页启动服务键='webStartup'#供补丁与启动模块共用

class 网页错误(Exception):
    """Web 应用组合包失败。"""

def 列举局域网地址():
    """采样本机非内部 IPv4 字面量。"""
    地址列表=[]
    try:
        for 信息 in socket.getaddrinfo(socket.gethostname(),None):
            族,类型,协议,规范名,套接=信息
            if 族==socket.AF_INET:
                主机=套接[0]
                if not 主机.startswith('127.'):
                    if 主机 not in 地址列表:
                        地址列表.append(主机)
    except OSError:
        pass
    return 地址列表

def 解析局域网信任(绑定主机,额外):
    """从活动服务器绑定解析一份局域网信任快照。"""
    局域网=列举局域网地址() if 绑定主机==全接口主机 else []#全接口才采样
    return {'lanAddresses':局域网,'trustedHosts':list(局域网)+list(额外)}#局域网后接显式权威

def 网页表面提示词(网页地址):
    """经 dsh web 创建的会话的模型可见定向与接受边界。"""
    更新约定=('The client-plugin HMR receiver is active, but client-plugin changes reload without a refresh only while '
        +'`pnpm run dev:web` is also running from this same checkout to rebuild their bundles; verify that watcher before promising automatic updates. '
        +'Every other change — the apps/web shell and plain packages — requires rebuilding the affected Web artifacts and verifying this existing URL after a page refresh. ')
    return ('You are interacting with the user through the DeepSeek Harness Web GUI at '+网页地址+'. '
        +'When the user refers to "this page", "this GUI", or "this app" without naming another target, they mean this GUI. '
        +'The browser provides no implicit DOM, route, or screenshot context. '
        +更新约定
        +'Starting another server does not update this GUI. '
        +'The apps/web Vite entry builds the shell but is not a standalone application because only dsh web injects window.__DSH_BOOT__. '
        +'Do not start a replacement server unless the user asks; if one is needed, use a managed background job and verify its exact URL.')

def 本地网页地址(上下文):
    """从活动 Web 服务器解析规范回环 URL。"""
    服务器=上下文.获取服务('webServer')
    if 服务器 is None:
        raise 网页错误('web-app: 解析 Web 运行时时缺少 webServer 服务')
    return 'http://'+回环主机+':'+str(服务器.port)

def 解析前端入口():
    """dist 位置是本组合包的工作区知识。"""
    try:
        import web_frontend
        路径=web_frontend.前端入口
        if 路径 is not None:
            return 路径
    except ImportError:
        pass
    raise 网页错误('web-app: 本组合无法解析 @deepseek-ai/dsh-web-frontend')

内部={'resolveDistIndex':解析前端入口,'openBrowser':webbrowser.open}

def 应用(上下文,配置值):
    """挂载 Web 运行时：dist 服务、表面提示词、bash 运行时变量，以及 URL 行。"""
    服务器=上下文.webServer
    额外=配置值['trustedHosts'] if 'trustedHosts' in 配置值 else []
    运行时=解析局域网信任(服务器.host,额外)
    快照=取启动环境(上下文)
    交出浏览器=配置值['openBrowser'] is True if 'openBrowser' in 配置值 else True
    if 快照 is not None and 经ssh拉起(快照):
        交出浏览器=False
    上下文.提供服务(运行时服务键,运行时)
    try:
        import host_frontend_static as 前端静态
        上下文.启动插件(前端静态,{'distIndex':内部['resolveDistIndex']()})
    except ImportError as 错误:
        raise 网页错误('web-app: 缺少 host_frontend_static 包') from 错误
    if 'surfaceContext' in 配置值 and 配置值['surfaceContext']:
        def 提示词接线(提示上下文,*其余):
            """登记 harness 源码段与 web 表面段。"""
            添加源码段落(提示上下文,源码根)
            def 文本():
                return 网页表面提示词(本地网页地址(提示上下文))
            提示上下文.systemPrompt.段落({
                'name':'app:web-surface',
                'order':提示上下文.systemPrompt.取段落序号('WEB_SURFACE'),
                'text':文本,
            })
        上下文.依赖启动(['systemPrompt'],提示词接线)
        def 环境接线(运行时上下文,*其余):
            """登记 DSH_WEB_URL。"""
            def 解析环境():
                return {网页地址环境键:本地网页地址(运行时上下文)}
            运行时上下文.shellEnv.登记({
                'name':'web-runtime',
                'variables':{
                    网页地址环境键:{'description':'Canonical local URL of the DeepSeek Harness Web GUI serving this session.'},
                },
                'resolve':解析环境,
            })
        上下文.依赖启动(['shellEnv'],环境接线)
    if ('printUrl' in 配置值 and 配置值['printUrl']) or 交出浏览器:
        def 打印地址():
            """打印回环与可选局域网，并按配置打开默认浏览器。"""
            根键=id(上下文.根)
            if 根键 in 已宣告根:
                return
            地址列表=运行时['lanAddresses']
            局域网候选=地址列表[0] if len(地址列表)>0 else None
            端口=上下文.webServer.port
            网页地址=本地网页地址(上下文)
            连接=上下文.获取服务('connection',False)
            认证地址=网页地址 if 连接 is None else 连接.authenticatedUrl(网页地址)
            局域网地址=None if 局域网候选 is None else (
                'http://'+局域网候选+':'+str(端口) if 连接 is None else 连接.authenticatedUrl('http://'+局域网候选+':'+str(端口))
            )
            已宣告根.add(根键)
            if 'printUrl' in 配置值 and 配置值['printUrl']:
                后缀='' if 局域网地址 is None else ' (局域网: '+局域网地址+')'
                print('dsh web: '+认证地址+后缀)
            if 交出浏览器:
                print('dsh web: 正在打开默认浏览器；传入 --no-open 可关闭')
                try:
                    内部['openBrowser'](认证地址)
                except OSError as 错误:
                    print('web-app: 无法打开默认浏览器，原因：'+str(错误)+'；请使用启动时打印的 dsh web 地址')
        加载器=上下文.获取服务('loader')
        if 加载器 is None:
            打印地址()
        else:
            def 结算后():
                """服务仍在才打印。"""
                def 吞警告(行):
                    """审计可选失败不印到标准错误。"""
                    return
                try:
                    审计启动条目(上下文.根,'dsh web',吞警告)
                except 启动错误:
                    return
                if 上下文.获取服务('webServer') is not None and 上下文.获取服务('connection') is not None:
                    打印地址()
            加载器.等待()
            结算后()

name=名称
inject=依赖
apply=应用
Config=配置
