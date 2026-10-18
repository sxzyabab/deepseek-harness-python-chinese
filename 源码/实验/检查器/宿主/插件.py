'跨 realm 检查器 Worker 与完整 fetch 采集的 Host 插件'
import os
import socket
import threading
import urllib.parse
from ....客户端.连接.http桥 import 连接响应
from ....客户端.连接.rpc import 编码json
from ..共享.网页 import 检查器引导路径,检查器客户端查询,读检查器客户端选择
from ..共享.服务 import 创建检查器服务
from ..共享.处置 import 处置检查器资源
from .桥接.控制器 import 解析检查器选项,启动检查器
from .检视.cordis import 发布cordis树

__all__=['应用','解析检查器选项','启动检查器']

诊断路径='/inspector/devtools'
平台不可用码='ERR_FEATURE_UNAVAILABLE_ON_PLATFORM'
媒体类型={
    '.html':'text/html; charset=utf-8',
    '.js':'text/javascript; charset=utf-8',
    '.css':'text/css; charset=utf-8',
    '.json':'application/json',
    '.map':'application/json',
    '.svg':'image/svg+xml',
    '.png':'image/png',
    '.wasm':'application/wasm',
    '.txt':'text/plain; charset=utf-8',
}


def 应用(上下文,配置):
    '启动 Worker 前先挂引导路由。平台不能跑 Worker 时只留这条路由并回答 503'
    def 效应():
        '插件效应。失败回滚后继续抛出'
        规格=解析检查器选项(配置)
        就绪={'值':None,'事件':threading.Event()}
        清理列表=[]
        工作者={'句柄':None}
        套接字集=set()
        套接字锁=threading.Lock()

        def 关闭源():
            '关闭已启动的 Worker。还没启动则什么也不做'
            句柄=工作者['句柄']
            if 句柄 is not None:
                句柄.关闭()

        def 拆除():
            '反序拆除登记，再关闭 Worker'
            处置检查器资源(清理列表,关闭源,'experimental-inspector: disposal failed')

        def 引导请求(请求):
            '等 Host 初始化结束，或等浏览器放弃这次请求'
            头={'cache-control':'no-store','content-type':'application/json'}
            信号=getattr(请求,'signal',None)
            放弃=threading.Event()

            def 中止():
                '请求中止后不再等待端点'
                放弃.set()

            if 信号 is not None and getattr(信号,'aborted',False):
                中止()
            elif 信号 is not None:
                信号.addEventListener('abort',中止,{'once':True})
            while not 就绪['事件'].is_set() and not 放弃.is_set():
                就绪['事件'].wait(0.05)
            if 信号 is not None:
                信号.removeEventListener('abort',中止)
            if 放弃.is_set() and not 就绪['事件'].is_set():
                return 连接响应(None,503,{'cache-control':'no-store'})
            if 就绪['值'] is None:
                return 连接响应(None,503,{'cache-control':'no-store'})
            return 连接响应(编码json(就绪['值']),200,头)

        try:
            清理列表.append(上下文.connection.fetch.register({
                'path':检查器引导路径,
                'methods':['GET'],
                'requestBody':'buffered',
                'fetch':引导请求,
            }))
            try:
                句柄=启动检查器(规格)
            except Exception as 错误:
                码=getattr(错误,'code',None)
                if not (isinstance(错误,BaseException) and 码==平台不可用码):
                    raise
                上下文.日志.警告(
                    'experimental-inspector: NodeJS Inspector is unavailable on this platform; Host inspection stays disabled',
                    错误,
                )
                句柄=None
            if 句柄 is None:
                就绪['事件'].set()
                return 拆除
            工作者['句柄']=句柄
            清理列表.append(发布cordis树(上下文,句柄.source,{
                'maxNodes':规格.maxCordisNodes,
                'maxBytes':规格.maxSourceFrameBytes-4096,
            }))
            清理列表.append(上下文.提供服务('inspector',创建检查器服务(句柄.source)))

            def 依赖(表):
                '把 Client 引导写入页面全局表'
                表.append({'kind':'global','name':'__DSH_INSPECTOR__','value':句柄.endpoint.client})

            清理列表.append(上下文.监听('webserver/index-inject',依赖))
            诊断目录=os.path.normpath(os.path.join(os.path.dirname(__file__),'..','devtools'))

            def 静态(请求,响应):
                '提供诊断前端。只接受 GET 与 HEAD，并先做索引认证'
                if 请求.method not in ('GET','HEAD'):
                    响应.writeHead(405,{'allow':'GET, HEAD'})
                    响应.end()
                    return
                if not 上下文.connection.authorizeIndex(请求,响应):
                    return
                网址=urllib.parse.urlsplit(urllib.parse.urljoin('http://inspector.invalid',请求.url or '/'))
                if 网址.path in (诊断路径,诊断路径+'/'):
                    位置=('devtools/' if 网址.path==诊断路径 else '')+'devtools_app.html'+('' if 网址.query=='' else '?'+网址.query)
                    响应.writeHead(302,{'location':位置})
                    响应.end()
                    return
                相对=urllib.parse.unquote(网址.path[len(诊断路径):])
                目标=os.path.abspath(os.path.normpath(诊断目录+os.sep+相对.lstrip('/').replace('/',os.sep)))
                if 目标!=诊断目录 and not 目标.startswith(诊断目录+os.sep):
                    响应.writeHead(403)
                    响应.end()
                    return
                try:
                    with open(目标,'rb') as 文件:
                        正文=文件.read()
                except OSError as 错误:
                    上下文.日志.警告('experimental-inspector: frontend asset request failed',错误)
                    if getattr(响应,'headersSent',False):
                        响应.destroy()
                    else:
                        响应.writeHead(404)
                        响应.end()
                    return
                扩展=os.path.splitext(目标)[1]
                类型=媒体类型.get(扩展,'application/octet-stream')
                响应.writeHead(200,{
                    'content-type':类型,
                    'X-Content-Type-Options':'nosniff',
                })
                if 请求.method!='HEAD':
                    响应.end(正文)
                else:
                    响应.end()

            清理列表.append(上下文.webServer.register({
                'kind':'prefix',
                'path':诊断路径,
                'handler':静态,
            }))

            def 跟踪(一端):
                '记下一端，关掉就从集合摘掉'
                with 套接字锁:
                    套接字集.add(一端)

                def 摘掉(事件=None):
                    '关闭后摘掉'
                    with 套接字锁:
                        套接字集.discard(一端)

                if hasattr(一端,'once'):
                    一端.once('close',摘掉)

            def 处理升级(请求,套接字,头字节):
                '把已认证的诊断 WebSocket 转到 Worker，并带上 Client 选择'
                拒收=上下文.connection.requestRejection(请求)
                if 拒收 is not None:
                    原因='Unauthorized' if 拒收==401 else 'Forbidden'
                    套接字.write('HTTP/1.1 '+str(拒收)+' '+原因+'\r\nConnection: close\r\nContent-Length: 0\r\n\r\n')
                    套接字.destroy()
                    return
                目标=urllib.parse.urlsplit(句柄.endpoint.webSocketDebuggerUrl)
                请求网址=urllib.parse.urlsplit(urllib.parse.urljoin('http://inspector.invalid',请求.url or '/'))
                try:
                    选中=读检查器客户端选择(请求网址)
                except Exception:
                    套接字.write('HTTP/1.1 400 Bad Request\r\nConnection: close\r\nContent-Length: 0\r\n\r\n')
                    套接字.destroy()
                    return
                查询=urllib.parse.parse_qsl(目标.query,keep_blank_values=True)
                if 选中 is not None:
                    查询.append((检查器客户端查询,选中))
                查询串=urllib.parse.urlencode(查询)
                路径查询=目标.path+(('?'+查询串) if 查询串!='' else '')
                try:
                    上游=socket.create_connection((目标.hostname,int(目标.port)))
                except Exception:
                    套接字.destroy()
                    return
                跟踪(套接字)
                跟踪(上游)
                报文='GET '+路径查询+' HTTP/1.1\r\nHost: '+目标.hostname+':'+str(目标.port)+'\r\nConnection: Upgrade\r\nUpgrade: websocket\r\n'
                for 键,值 in 请求.headers.items():
                    if 键.startswith('sec-websocket-') and 值 is not None:
                        报文+=键+': '+str(值)+'\r\n'
                报文+='\r\n'
                try:
                    上游.sendall(报文.encode('latin-1'))
                    if 头字节:
                        数据=头字节 if isinstance(头字节,(bytes,bytearray)) else bytes(头字节)
                        if len(数据)>0:
                            上游.sendall(数据)
                except Exception:
                    套接字.destroy()
                    try:
                        上游.close()
                    except OSError:
                        pass
                    return

                def 拷向下游():
                    'Worker 字节写回浏览器套接字'
                    try:
                        while True:
                            片=上游.recv(65536)
                            if not 片:
                                break
                            套接字.write(片)
                    except Exception:
                        pass
                    套接字.destroy()

                def 拷向上游():
                    '浏览器字节写到 Worker'
                    try:
                        while True:
                            片=套接字.原始.recv(65536)
                            if not 片:
                                break
                            上游.sendall(片)
                    except Exception:
                        pass
                    try:
                        上游.shutdown(socket.SHUT_RDWR)
                    except OSError:
                        pass
                    try:
                        上游.close()
                    except OSError:
                        pass

                threading.Thread(target=拷向下游,daemon=True).start()
                threading.Thread(target=拷向上游,daemon=True).start()

            def 拆套接字():
                '拆掉还活着的升级套接字'
                with 套接字锁:
                    待拆=list(套接字集)
                    套接字集.clear()
                for 一端 in 待拆:
                    try:
                        if hasattr(一端,'destroy'):
                            一端.destroy()
                        else:
                            一端.close()
                    except Exception:
                        pass

            清理列表.append(拆套接字)
            清理列表.append(上下文.webServer.registerUpgrade({
                'path':诊断路径+'/cdp',
                'handler':处理升级,
            }))
            print('dsh inspector: '+句柄.endpoint.devtoolsFrontendUrl)
            就绪['值']=句柄.endpoint.client
            就绪['事件'].set()
            参数服务=上下文.获取服务('cmdlineArgs',False)
            参数=[]
            if isinstance(参数服务,dict) and callable(参数服务.get('get')):
                参数=参数服务['get']() or []
            elif 参数服务 is not None and callable(getattr(参数服务,'get',None)):
                参数=参数服务.get() or []
            if '--inspect' in 参数:
                try:
                    import webbrowser
                    webbrowser.open(句柄.endpoint.devtoolsFrontendUrl)
                except Exception as 打开错误:
                    上下文.日志.错误('experimental-inspector: Chrome could not open DevTools',打开错误)
        except Exception as 错误:
            就绪['事件'].set()
            try:
                拆除()
            except Exception as 回滚错误:
                上下文.日志.错误('experimental-inspector: initialization rollback failed',回滚错误)
            raise 错误
        return 拆除

    上下文.副作用(效应,'experimental-inspector: Host Worker')


apply=应用
