'浏览器 HTTP 载体：路由登记、可选 gzip、索引注入、一个回退席。不认识 harness，也不直接发文件'
import gzip,http.client,http.server,re,socket,socketserver,threading,urllib.parse#传输
from ...依赖.cordis.服务 import 服务#服务基类
from ...依赖.schemastery import 复合类型字段,常量字段,整数字段,自然数字段#配置字段
from .注入 import 渲染索引注入#结构化索引行

__all__=['名称','配置','网页服务器','渲染索引注入']#仅中文公开名

名称='webserver'#插件名
默认压缩='none'#默认不压缩
默认压缩级别=1#默认 deflate 级别
默认压缩阈值=1024#已知长度低于此不压缩
配置={#监听与压缩
    'host':复合类型字段(常量字段('127.0.0.1'),常量字段('0.0.0.0')),#回环或全部接口
    'port':自然数字段(最大=65535),#0 表示由系统分配
    'compression':复合类型字段(常量字段('none'),常量字段('gzip'),默认值=默认压缩),#压缩
    'compressionLevel':整数字段(最小=0,最大=9,默认值=默认压缩级别),#级别
    'compressionThresholdBytes':自然数字段(默认值=默认压缩阈值),#阈值
}#配置结束

def 路径名(网址):#请求目标的路径
    '没有 url 时当作 /'
    return urllib.parse.urlparse(网址 if 网址 else '/').path#路径

def 接受gzip(头):#客户端是否接受 gzip
    'Accept-Encoding 里写了 gzip 才压'
    值=头.get('accept-encoding','')#头
    return 'gzip' in 值.lower()#含 gzip

class 监听表:#事件名到监听器
    'on / once / off'
    def __init__(自身):#空表
        '按事件名存放'
        自身.表={}#监听器

    def on(自身,事件,监听):#登记
        '追加'
        自身.表.setdefault(事件,[]).append(监听)#追加

    def off(自身,事件,监听):#摘掉
        '没有则忽略'
        列表=自身.表.get(事件)#该事件
        if 列表 is not None and 监听 in 列表:#在
            列表.remove(监听)#摘

    def once(自身,事件,监听):#只跑一次
        '跑完就摘'
        def 一次(*参数):#包装
            '摘掉后再调用'
            自身.off(事件,一次)#摘
            监听(*参数)#调用
        自身.on(事件,一次)#登记

    def 发出(自身,事件,*参数):#同步通知
        '拷贝后再调，监听器可以改表'
        for 监听 in list(自身.表.get(事件,[])):#逐个
            监听(*参数)#调用

class 套接字壳:#升级后的套接字
    'destroy / on / once / off'
    def __init__(自身,原始):#包装真实套接字
        '记下套接字'
        自身.原始=原始#套接字
        自身.监听=监听表()#事件

    def destroy(自身):#拆掉
        '关闭并发出 close'
        try:#先停收发
            自身.原始.shutdown(socket.SHUT_RDWR)#停
        except OSError:#已经关了
            pass#忽略
        自身.原始.close()#关
        自身.监听.发出('close')#close

    def on(自身,事件,监听):#登记
        '转发'
        自身.监听.on(事件,监听)#登记

    def off(自身,事件,监听):#摘掉
        '转发'
        自身.监听.off(事件,监听)#摘

    def once(自身,事件,监听):#一次
        '转发'
        自身.监听.once(事件,监听)#一次

class 服务器响应:#一条 HTTP 响应
    'writeHead / write / end / getHeader / on / destroy'
    def __init__(自身,处理,套接字):#绑定这次连接
        '头还没发'
        自身.处理=处理#处理器，结束时回调
        自身.socket=套接字#连接
        自身.头={}#小写头名
        自身.状态=200#默认
        自身.headersSent=False#头是否已写出
        自身.writableEnded=False#是否已 end
        自身.监听=监听表()#事件
        自身._头已写=False#是否已把状态行写进套接字

    def getHeader(自身,名):#读响应头
        '大小写不敏感'
        return 自身.头.get(名.lower())#值或 None

    def writeHead(自身,状态,头=None):#设状态与头
        '真正写出推迟到第一块正文'
        自身.状态=状态#状态
        if isinstance(头,dict):#有头
            for 键,值 in 头.items():#逐个
                自身.头[键.lower()]=值#收下
        自身.headersSent=True#调用方视为已发

    def _写头(自身):#把状态行和头写进套接字
        '只写一次'
        if 自身._头已写:#已写
            return#停
        自身._头已写=True#占住
        自身.headersSent=True#已发
        try:#原因短语
            原因=http.client.responses.get(自身.状态,'')#短语
        except Exception:#没有表
            原因=''#空
        行=['HTTP/1.1 '+str(自身.状态)+' '+原因]#状态行
        for 键,值 in 自身.头.items():#头
            行.append(键+': '+str(值))#一行
        数据=('\r\n'.join(行)+'\r\n\r\n').encode('latin1','replace')#头块
        自身.处理.wfile.write(数据)#写出

    def write(自身,块):#写一块正文
        '字符串按 utf-8'
        if 自身.writableEnded:#已经结束
            return#丢
        if isinstance(块,str):#文本
            块=块.encode('utf-8')#编码
        自身._写头()#先头
        自身.处理.wfile.write(块)#正文
        自身.处理.wfile.flush()#送出

    def end(自身,正文=None):#结束
        '可选最后一块'
        if 自身.writableEnded:#已经结束
            return#停
        if 正文 is not None:#还有正文
            if isinstance(正文,str):#文本
                正文=正文.encode('utf-8')#编码
            if not 自身._头已写 and 'content-length' not in 自身.头:#一次写完
                自身.头['content-length']=str(len(正文))#长度
            自身.write(正文)#写出
        else:#无正文
            自身._写头()#只发头
        自身.writableEnded=True#结束
        自身.监听.发出('close')#close
        自身.处理.完结()#连接可以结束

    def destroy(自身):#拆掉
        '关掉套接字'
        自身.writableEnded=True#结束
        try:#关
            自身.socket.close()#关
        except OSError:#已经关
            pass#忽略
        自身.监听.发出('close')#close
        自身.处理.完结()#放开连接线程

    def on(自身,事件,监听):#登记
        '转发'
        自身.监听.on(事件,监听)#登记

    def off(自身,事件,监听):#摘掉
        '转发'
        自身.监听.off(事件,监听)#摘

class 进入请求:#一条 HTTP 请求
    'method / url / headers / rfile / readBody / destroy / on'
    def __init__(自身,处理):#从处理器抄字段
        '头名小写'
        自身.method=处理.command#方法
        自身.url=处理.path#原始目标
        自身.headers={键.lower():值 for 键,值 in 处理.headers.items()}#小写
        自身.rfile=处理.rfile#正文流
        自身.socket=处理.connection#套接字
        自身._处理=处理#回指

    def readBody(自身):#按 Content-Length 读完
        '没有长度则空字节'
        声明=自身.headers.get('content-length')#长度
        if 声明 is None:#无
            return b''#空
        return 自身.rfile.read(int(声明))#读

    def destroy(自身):#拆掉请求
        '关掉连接'
        try:#关
            自身.socket.close()#关
        except OSError:#已经关
            pass#忽略

    def on(自身,事件,监听):#请求事件
        '目前只把 close 挂到连接关闭'
        if 事件=='close':#关闭
            自身._处理.请求关闭.append(监听)#记下

class 压缩响应:#在 end 时按规则 gzip
    '事件流、Content-Range 不压；未知长度在 end 时已经知道'
    def __init__(自身,内层,请求,级别,阈值):#包装真实响应
        '先攒正文'
        自身.内层=内层#真实响应
        自身.请求=请求#用来看 Accept-Encoding
        自身.级别=级别#deflate 级别
        自身.阈值=阈值#已知长度阈值
        自身.块=[]#正文
        自身.直通=False#已经决定不压
        自身.socket=内层.socket#给中间件看
        自身.headersSent=False#转发
        自身.writableEnded=False#转发

    def getHeader(自身,名):#读头
        '转发'
        return 自身.内层.getHeader(名)#转发

    def writeHead(自身,状态,头=None):#设头
        '事件流与区间请求直接透传'
        自身.内层.writeHead(状态,头)#转发
        自身.headersSent=自身.内层.headersSent#同步
        类型=自身.内层.getHeader('content-type')#类型
        if 自身.内层.getHeader('content-range') is not None:#区间
            自身.直通=True#不压
        elif isinstance(类型,str) and 类型.lower().startswith('text/event-stream'):#事件流
            自身.直通=True#不压

    def write(自身,块):#一块
        '直通则立刻写出'
        if isinstance(块,str):#文本
            块=块.encode('utf-8')#编码
        if 自身.直通:#不压
            自身.内层.write(块)#转发
            return#停
        自身.块.append(块)#攒

    def end(自身,正文=None):#结束
        '够大或类型要求时 gzip'
        if 正文 is not None:#最后一块
            自身.write(正文)#收下
        自身.writableEnded=True#结束
        if 自身.直通:#不压
            自身.内层.end()#转发
            return#停
        体=b''.join(自身.块)#合并
        类型=自身.内层.getHeader('content-type')#类型
        总是=isinstance(类型,str) and re.match(r'multipart/form-data(?:;|$)',类型,re.I) is not None#表单总是压
        要压=接受gzip(自身.请求.headers) and (总是 or len(体)>=自身.阈值)#是否压
        if not 要压:#不压
            自身.内层.end(体)#原样
            return#停
        压=gzip.compress(体,compresslevel=自身.级别)#gzip
        自身.内层.头['content-encoding']='gzip'#编码
        自身.内层.头.pop('content-length',None)#长度作废
        自身.内层.end(压)#压缩正文

    def destroy(自身):#拆掉
        '转发'
        自身.内层.destroy()#转发

    def on(自身,事件,监听):#事件
        '转发'
        自身.内层.on(事件,监听)#转发

    def off(自身,事件,监听):#摘掉
        '转发'
        自身.内层.off(事件,监听)#摘

class 处理器(http.server.BaseHTTPRequestHandler):#一条连接
    '解析请求后交给网页服务器。连接线程阻塞到响应 end'
    protocol_version='HTTP/1.1'#保持连接
    def handle(自身):#读请求直到连接结束或升级
        '升级请求把套接字交出去，不再读下一条'
        while True:#可能保持连接
            try:#一行请求
                自身.raw_requestline=自身.rfile.readline(65537)#请求行
                if len(自身.raw_requestline)>65536:#过长
                    自身.send_error(414)#URI 过长
                    return#停
                if not 自身.raw_requestline:#对端关掉
                    return#停
                if not 自身.parse_request():#畸形
                    return#基类已回答
            except Exception as 错误:#读失败
                自身.server.服务.记录(错误)#记
                return#停
            请求=进入请求(自身)#包装
            if 'upgrade' in 请求.headers:#升级
                自身.server.服务.派发升级(请求,套接字壳(自身.connection),b'')#升级
                return#套接字交给升级处理
            自身._结束=threading.Event()#响应结束门闩
            内层=服务器响应(自身,自身.connection)#响应
            响应=内层#交给路由的对象
            if 自身.server.服务.要压缩(请求):#gzip
                响应=压缩响应(内层,请求,自身.server.服务.压缩级别,自身.server.服务.压缩阈值)#包装
            try:#派发
                自身.server.服务.派发(请求,响应)#路由
            except Exception as 错误:#处理失败
                自身.server.服务.记录(错误)#记
                if not 内层.headersSent:#还没写头
                    内层.writeHead(400)#坏请求
                    内层.end()#结束
                else:#头已发
                    内层.destroy()#拆掉
            自身._结束.wait()#等到 end 或 destroy
            if 请求.headers.get('connection','').lower()=='close':#不保持
                return#停

    def 完结(自身):#响应 end 或 destroy
        '放开连接线程'
        门闩=getattr(自身,'_结束',None)#门闩
        if 门闩 is not None:#有
            门闩.set()#放开

    def log_message(自身,格式,*参数):#安静
        '不把访问日志打到 stderr'
        return#不打印

class 线程服务器(socketserver.ThreadingTCPServer):#每连接一线程
    '允许立刻重绑'
    allow_reuse_address=True#重绑
    daemon_threads=True#随进程退出
    def __init__(自身,地址,服务):#绑地址
        '处理器从 server.服务 取路由'
        自身.服务=服务#网页服务器
        super().__init__(地址,处理器)#绑定

class 网页服务器(服务):#ctx.webServer
    '启动即监听。同一种类加路径不能重复。回退席只能有一个主人'
    Config=配置#插件配置
    def __init__(自身,上下文,配置值=None):#构造
        '记下监听参数；真正 bind 在初始化'
        super().__init__(上下文,'webServer')#服务名
        if 配置值 is None:#无配置
            配置值={}#空
        自身.配置=配置值#原始配置
        自身.绑定主机=配置值['host']#主机
        自身.绑定端口=配置值['port']#端口
        自身.压缩=配置值['compression'] if 'compression' in 配置值 and 配置值['compression'] is not None else 默认压缩#压缩
        自身.压缩级别=配置值['compressionLevel'] if 'compressionLevel' in 配置值 and 配置值['compressionLevel'] is not None else 默认压缩级别#级别
        自身.压缩阈值=配置值['compressionThresholdBytes'] if 'compressionThresholdBytes' in 配置值 and 配置值['compressionThresholdBytes'] is not None else 默认压缩阈值#阈值
        自身.精确={}#精确路由
        自身.前缀={}#前缀路由
        自身.升级={}#升级路由
        自身.升级套接字=set()#仍活着的升级套接字
        自身.索引变换=[]#tapIndex
        自身.回退=None#回退处理
        自身.监听端口=None#bind 之后才有
        自身.锁=threading.Lock()#路由表
        自身.服务器=None#TCP 服务
        自身.线程=None#serve_forever 线程
        自身.__dict__[服务.初始化]=自身._初始化#依赖就绪后监听

    @property
    def port(自身):#正在听的端口
        '配置端口为 0 时这里是系统分配的值'
        return 自身.监听端口#端口

    @property
    def host(自身):#配置的绑定主机
        '127.0.0.1 或 0.0.0.0'
        return 自身.绑定主机#主机

    def 要压缩(自身,请求):#这条请求是否走 gzip 包装
        '无套接字的通道不压；这里每条都有套接字'
        return 自身.压缩=='gzip' and 请求.socket is not None#开关

    def 记录(自身,错误):#请求失败
        '记警告，不退出进程'
        if not isinstance(错误,Exception):#不是异常
            错误=RuntimeError(str(错误))#收成异常
        自身.所属上下文.日志.警告(错误)#警告

    def register(自身,路由):#登记具名路由
        '重复的种类加路径直接抛'
        表=自身.精确 if 路由['kind']=='exact' else 自身.前缀#目标表
        with 自身.锁:#改表
            if 路由['path'] in 表:#重复
                raise RuntimeError('webserver: duplicate '+路由['kind']+' route "'+路由['path']+'"')#冲突
            表[路由['path']]=路由#记下
        def 拆除():#摘掉
            '删掉这条路由'
            with 自身.锁:#改表
                if 表.get(路由['path']) is 路由:#还是这一条
                    del 表[路由['path']]#摘
        return 拆除#拆除器

    def registerUpgrade(自身,路由):#登记精确路径的升级
        '同一路径只能有一个协议主人'
        with 自身.锁:#改表
            if 路由['path'] in 自身.升级:#重复
                raise RuntimeError('webserver: duplicate upgrade route "'+路由['path']+'"')#冲突
            自身.升级[路由['path']]=路由#记下
        def 拆除():#摘掉
            '删掉这条升级'
            with 自身.锁:#改表
                if 自身.升级.get(路由['path']) is 路由:#还是这一条
                    del 自身.升级[路由['path']]#摘
        return 拆除#拆除器

    def registerFallback(自身,处理):#占住回退席
        '第二个登记直接抛'
        with 自身.锁:#改
            if 自身.回退 is not None:#已有
                raise RuntimeError('webserver: fallback already registered')#冲突
            自身.回退=处理#占住
        def 拆除():#让出席
            '清空回退'
            with 自身.锁:#改
                if 自身.回退 is 处理:#还是这个
                    自身.回退=None#清空
        return 拆除#拆除器

    def tapIndex(自身,变换):#登记原始 HTML 变换
        '按登记顺序，排在结构化行之后'
        自身.索引变换.append(变换)#追加
        def 拆除():#摘掉
            '按身份删除'
            if 变换 in 自身.索引变换:#还在
                自身.索引变换.remove(变换)#摘
        return 拆除#拆除器

    def 匹配(自身,路径):#先精确，再最长前缀
        '前缀要整段命中：p 或 p/...'
        with 自身.锁:#读表
            精确=自身.精确.get(路径)#精确
            if 精确 is not None:#命中
                return 精确#路由
            最好=None#最长前缀
            for 前缀,路由 in 自身.前缀.items():#逐个
                if 路径!=前缀 and not 路径.startswith(前缀+'/'):#不命中
                    continue#下一个
                if 最好 is None or len(前缀)>len(最好['path']):#更长
                    最好=路由#记下
            return 最好#可能没有

    def 派发(自身,请求,响应):#普通请求
        '没有具名路由时走回退；回退也没有则 404'
        try:#解析路径
            路由=自身.匹配(路径名(请求.url))#路由
        except Exception as 错误:#坏转义等
            自身.记录(错误)#记
            响应.writeHead(400)#坏请求
            响应.end()#结束
            return#停
        if 路由 is not None:#命中
            路由['handler'](请求,响应)#交给主人
            return#停
        回退=自身.回退#回退席
        if 回退 is None:#还没人占
            响应.writeHead(404)#未找到
            响应.end()#结束
            return#停
        回退(请求,响应)#回退

    def 派发升级(自身,请求,套接字,头):#升级
        '没有主人就拆掉套接字'
        def 出错(错误):#升级失败
            '记日志并拆套接字'
            自身.记录(错误)#记
            套接字.destroy()#拆
        套接字.on('error',出错)#错误
        套接字.once('close',lambda:自身.升级套接字.discard(套接字))#关掉就从表里摘
        try:#解析路径
            路由=自身.升级.get(路径名(请求.url))#精确
        except Exception as 错误:#坏目标
            出错(错误)#拆
            return#停
        if 路由 is None:#没有主人
            套接字.destroy()#拆
            return#停
        自身.升级套接字.add(套接字)#跟踪
        try:#交给主人
            路由['handler'](请求,套接字,头)#升级
        except Exception as 错误:#同步失败
            出错(错误)#拆

    def applyIndexTaps(自身,html):#按登记顺序跑裸变换
        '回退主人渲染索引时调用'
        输出=html#工作副本
        for 变换 in list(自身.索引变换):#逐个
            输出=变换(输出)#变换
        return 输出#结果

    def collectIndexInjections(自身):#收集结构化行
        '每次调用都新发一次 webserver/index-inject'
        表=[]#可变行表
        自身.所属上下文.emit('webserver/index-inject',表)#听众往里追加
        return 表#激活顺序

    def renderIndex(自身,html):#渲染一份 index.html
        '先行，再跑 tapIndex'
        return 自身.applyIndexTaps(渲染索引注入(html,自身.collectIndexInjections()))#结果

    def _初始化(自身):#监听
        'bind 失败则这条纤程失败'
        自身.服务器=线程服务器((自身.绑定主机,自身.绑定端口),自身)#绑定
        自身.监听端口=自身.服务器.server_address[1]#实际端口
        自身.线程=threading.Thread(target=自身.服务器.serve_forever,daemon=True)#服务线程
        自身.线程.start()#开始接
        def 关闭():#拆除
            '关掉监听、普通连接和升级套接字'
            自身.服务器.shutdown()#停 accept
            自身.服务器.server_close()#关监听套接字
            for 套接字 in list(自身.升级套接字):#升级连接
                套接字.destroy()#拆
        yield 关闭#拆除器

name=名称#框架槽
inject=[]#无硬依赖
Config=配置#框架槽
default=网页服务器#类插件
