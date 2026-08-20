"""浏览器表面组合包的运行时粘合插件。

对齐上游 `@deepseek-ai/dsh-web-app`。公开面仅中文名。

依赖 `host_frontend_static`、`webServer` 等宿主包；若尚未迁入则本包激活时会失败——见未迁移插件说明。
"""
import os,socket#路径与网卡
from schemastery import 模式#配置模式
from app_boot import 添加源码段落#harness 源码提示词段

__all__=['名称','注入','配置','应用','解析局域网信任','内部','网页启动服务键']#仅中文公开名

名称='web-app'#插件名
注入=['webServer']#依赖 web 服务器
源码根=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..','..'))#相对本包上溯到中文源码树根旁
运行时服务键='webRuntime'#运行时服务名
网页地址环境键='DSH_WEB_URL'#bash 可见 URL 变量名
回环主机='127.0.0.1'#回环展示主机
全接口主机='0.0.0.0'#全接口绑定字面量

配置=模式.对象({#Web 应用配置
    'printUrl':模式.布尔().默认(True),#默认打印 URL
    'surfaceContext':模式.布尔().默认(True),#默认注册表面上下文
    'trustedHosts':模式.数组(模式.字符串()).默认([]),#默认无额外权威
})#配置结束

网页启动服务键='webStartup'#启动服务名（供补丁与启动模块共用）

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象.get(键,缺省)#映射
    return getattr(对象,键,缺省)#属性

def 列举局域网地址():#采样非内部 IPv4
    """采样本机非内部 IPv4 字面量。"""
    地址们=[]#地址
    try:#枚举网卡
        for 信息 in socket.getaddrinfo(socket.gethostname(),None):#解析主机名
            族,类型,协议,规范名,套接=信息#拆开
            if 族==socket.AF_INET:#IPv4
                主机=套接[0]#地址
                if not 主机.startswith('127.'):#非回环
                    if 主机 not in 地址们:#去重
                        地址们.append(主机)#收下
    except OSError:#枚举失败
        pass#空列表
    return 地址们#局域网地址

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

def 本地网页地址(上下文):#拼本地 URL
    """从活动 Web 服务器解析规范回环 URL。"""
    端口=取字段(上下文.get('webServer'),'port')#已绑定端口
    if 端口 is None:#缺少服务
        raise Exception('web-app: webServer service missing while resolving Web runtime')#失败
    return 'http://'+回环主机+':'+str(端口)#回环 URL

def 解析前端入口():#解析前端 dist 入口
    """dist 位置是本组合包的工作区知识。"""
    try:#尝试导入前端包
        import web_frontend#前端包
        路径=getattr(web_frontend,'前端入口',None) or getattr(web_frontend,'dist_index',None)#入口
        if 路径 is not None:#有路径
            return 路径#入口
    except ImportError:#未安装
        pass#继续
    raise Exception('web-app: frontend dist not built; run pnpm run build from the repository root first')#要求先构建

内部={'resolveDistIndex':解析前端入口}#可替换的 dist 解析

def 应用(上下文,配置值):#安装 Web 运行时粘合
    """挂载 Web 运行时：dist 服务、表面提示词、bash 运行时变量，以及 URL 行。"""
    服务器=上下文.webServer#web 服务器
    运行时=解析局域网信任(取字段(服务器,'host'),取字段(配置值,'trustedHosts') or [])#采样局域网信任
    上下文.provide(运行时服务键,运行时)#提供运行时服务
    try:#挂载前端静态
        import host_frontend_static as 前端静态#前端静态插件
        上下文.plugin(前端静态,{'distIndex':内部['resolveDistIndex']()})#挂载
    except ImportError as 错误:#宿主包未迁
        raise Exception('web-app: host_frontend_static is not migrated yet') from 错误#阻塞
    if 取字段(配置值,'surfaceContext'):#注册表面上下文
        def 提示词接线(提示上下文,*其余):#有系统提示词时注册段
            """登记 harness 源码段与 web 表面段。"""
            添加源码段落(提示上下文,源码根)#harness 源码段
            def 文本():#按当前 URL 生成
                """表面提示词文本。"""
                return 网页表面提示词(本地网页地址(提示上下文))#生成
            提示上下文.systemPrompt.段落({#web 表面段
                'name':'app:web-surface',#段名
                'order':-98,#紧随 harness 身份
                'text':文本,#按当前 URL
            })#section 结束
        上下文.inject(['systemPrompt'],提示词接线)#inject
        def 环境接线(运行时上下文,*其余):#有 shell 环境时注册变量
            """登记 DSH_WEB_URL。"""
            运行时上下文.shellEnv.登记({#注册 web 运行时变量
                'name':'web-runtime',#注册名
                'variables':{#变量表
                    网页地址环境键:{'description':'Canonical local URL of the DeepSeek Harness Web GUI serving this session.'},#说明
                },#variables 结束
                'resolve':lambda:({网页地址环境键:本地网页地址(运行时上下文)}),#解析
            })#register 结束
        上下文.inject(['shellEnv'],环境接线)#inject
    if 取字段(配置值,'printUrl'):#打印就绪 URL 行
        def 打印地址():#打印 URL 行
            """打印回环与可选局域网。"""
            局域网候选=(取字段(运行时,'lanAddresses') or [None])[0]#第一个局域网
            端口=取字段(上下文.webServer,'port')#已绑定端口
            后缀='' if 局域网候选 is None else ' (LAN: http://'+局域网候选+':'+str(端口)+')'#可选局域网
            print('dsh web: '+本地网页地址(上下文)+后缀)#打印
        加载器=上下文.get('loader')#Loader
        if 加载器 is None:#无 loader
            打印地址()#立刻打印
        else:#有 loader
            def 结算后():#结算成功
                """服务仍在才打印。"""
                if 上下文.get('webServer') is not None:#服务仍在
                    打印地址()#打印
            try:#等待结算
                等待=加载器.等待()#等待
                if hasattr(等待,'然后'):#承诺链式
                    等待.然后(结算后,lambda *_:None)#失败则不打印
                else:#同步已结算
                    结算后()#打印
            except Exception:#失败启动
                pass#保持安静
