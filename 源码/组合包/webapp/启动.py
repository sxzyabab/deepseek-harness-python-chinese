'Web 应用的命令行提供方：解析 dsh --profile web 的旗标并提供 webStartup'
import json,re
from ...启动.命令行 import 命令,解析命令行#命令程序与启动器参数
from ...宿主.web服务器 import 是通配主机#通配绑定地址
from .公开网址 import 解析公开网址#公告根校验

__all__=['名称','依赖','网页启动服务键','应用']#本文件公开名

名称='web-startup'#插件名
依赖=['cmdlineArgs']#解析旗标前需要命令行参数
网页启动服务键='webStartup'#旗标行注入的服务名

def 应用(上下文,配置值=None):
    '把 Web 调用解析并作为普通 Cordis 服务提供。无效旗标、未配对的 TLS 是用法错误；拒绝和 --help 不提供服务'
    #本插件没有配置。纤程仍会把配置传进来
    程序=(命令()
        .name('dsh --profile web')#程序名
        .description('提供 DeepSeek Harness 浏览器界面。')#描述
        .helpOption('-h, --help','显示此帮助')#帮助旗标
        .option('--host <host>','绑定地址：本机接口的一个具体 IPv4 或 IPv6 字面量；通配地址会被拒绝')#主机
        .option('--no-open','不在默认浏览器中打开网页界面')#不打开
        .option('--port <port>','监听端口；传 0 由操作系统选空闲端口')#端口
        .option('--public-url <url>','在打印、打开、运行时上下文和 DSH_WEB_URL 里公告这个 HTTP(S) 根；不授予信任')#公告根
        .option('--trusted-host <authority...>','/api 浏览器信任围栏额外接受的权威（主机或主机:端口；可重复）')#额外权威
        .option('--tls-cert <file>','PEM 服务器证书链；需要同时提供 --tls-key')#证书
        .option('--tls-key <file>','无加密的 PEM 私钥；需要同时提供 --tls-cert')#私钥
        .addHelpText('after','''
示例:
  dsh --profile web                          按组合后的主机与端口提供服务
  dsh --profile web --no-open                提供服务但不打开浏览器
  dsh --profile web --port 8080              使用另一端口
  dsh --profile web --host 10.0.0.7          绑定一个本机接口地址
  dsh --profile web --public-url https://app.example/ui/ --trusted-host app.example
                                             公告剥前缀的 HTTPS 代理入口，并接纳该权威
  dsh --profile web --tls-cert ./server-chain.pem --tls-key ./server-key.pem
                                             用已有证书和密钥提供 HTTPS
''')#帮助尾注
    )#程序结束

    def 动作():
        '发布这次调用点名的旗标'
        选项=程序.opts()#已解析选项
        主机=选项['host'] if 'host' in 选项 else None#--host
        if 主机 is not None and 是通配主机(主机):#通配地址
            消息='error: --host '+主机+' 是未指定（通配）地址，不支持：绑定全部接口会把远程代码执行暴露到网络；请改为绑定一个具体的 IPv4 或 IPv6 地址'#用法错误
            程序.error(消息)#拒绝
        端口=选项['port'] if 'port' in 选项 else None#--port
        if 端口 is not None and re.fullmatch(r'[0-9]+',str(端口)) is None:#不是十进制数字
            程序.error('error: --port 必须是数字，实际为 '+json.dumps(端口))#拒绝
        证书=选项['tlsCert'] if 'tlsCert' in 选项 else None#--tls-cert
        密钥=选项['tlsKey'] if 'tlsKey' in 选项 else None#--tls-key
        传输安全=None#未成对则不提供
        if 证书 is not None and 密钥 is not None:#证书和私钥一起给
            传输安全={'certFile':证书,'keyFile':密钥}#材料路径
        elif 证书 is not None or 密钥 is not None:#只给了其中一个
            程序.error('error: --tls-cert 与 --tls-key 必须同时提供')#拒绝
        if 'publicUrl' in 选项 and 选项['publicUrl'] is not None:#点了公告根
            try:#校验，服务里仍保存原文
                解析公开网址(选项['publicUrl'],'--public-url')#按旗标名报错
            except Exception as 错误:#解析失败
                程序.error('error: '+str(错误))#用法错误
        开浏览器=True#--no-open 才关掉
        if 'noOpen' in 选项 and 选项['noOpen'] is True:#点了 --no-open
            开浏览器=False#不打开
        受信=选项['trustedHost'] if 'trustedHost' in 选项 else []#额外权威
        载荷={'openBrowser':开浏览器,'trustedHosts':list(受信)}#总是带这两项
        if 主机 is not None:#点了主机
            载荷['host']=主机#原文
        if 端口 is not None:#点了端口
            载荷['port']=int(端口)#数字
        if 'publicUrl' in 选项 and 选项['publicUrl'] is not None:#点了公告根
            载荷['publicUrl']=选项['publicUrl']#原文，归一化留给 web-app 配置
        if 传输安全 is not None:#成对的证书
            载荷['tls']=传输安全#路径
        上下文.提供服务(网页启动服务键,载荷)#webStartup

    程序.action(动作)#解析成功后发布
    解析命令行(上下文,程序)#用启动器的参数快照

name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
