'浏览器 HTTP 载体：具名路由、可选 gzip、索引注入、一个回退席。配置了证书就听 HTTPS。不认识 harness，也不直接发文件'
import errno,http.client,ipaddress,json,os,re,socketserver,ssl,sys,threading#地址、套接字、监听
import urllib.parse,zlib#路径与 gzip
from socket import (
    AF_INET as 四版族,#IPv4
    AF_INET6 as 六版族,#IPv6
    SHUT_RDWR as 关闭读写,#停收发
    SOCK_STREAM as 流式套接字,#TCP
    getaddrinfo as 取地址信息,#含区号的绑定地址
)
from socketserver import TCPServer as 传输控制服务器,ThreadingMixIn as 线程混入#监听与每连接一线程
from threading import Event as 事件门闩,Lock as 锁,Thread as 线程#响应结束、路由表、服务线程
from ...依赖.cordis.服务 import 服务#服务基类
from ...依赖.工具 import 设置内部数据#纤程初始化槽
from .异常 import 网页服务器错误,拒绝非字面地址#失败
from .注入 import 渲染索引注入#结构化索引行
from . import 异常,注入#导入即执行同目录顶层

__all__=[#包根导出同目录模块，以及本文件的公开名
    '异常','注入',#同目录模块
    '名称','依赖','配置','网页服务器',#插件槽
    '渲染索引注入','是通配主机','是回环主机','规范化绑定地址','绑定网址主机',#公开函数
]#结束

地址解析=ipaddress.ip_address#解析一个地址
四版地址=ipaddress.IPv4Address#IPv4
六版地址=ipaddress.IPv6Address#IPv6
绝对路径=os.path.abspath#相对工作目录
地址占用码=errno.EADDRINUSE#端口已被占用
安全上下文类=ssl.SSLContext#TLS 上下文
服务端协议=ssl.PROTOCOL_TLS_SERVER#服务端协议
压缩对象=zlib.compressobj#gzip 流
压缩算法=zlib.DEFLATED#deflate
窗口位数=zlib.MAX_WBITS#gzip 窗口
状态短语=http.client.responses#状态码短语
拆分网址=urllib.parse.urlsplit#路径

名称='webserver'#插件名
依赖=[]#无硬依赖
默认压缩='none'#默认不压缩
默认压缩级别=1#默认 deflate 级别
默认压缩阈值=1024#已知长度低于此不压缩

def 取配置(配置值,键,缺省):
    '缺席或空值用缺省。0 这样的值留着'
    if not isinstance(配置值,dict) or 键 not in 配置值 or 配置值[键] is None:#没给
        return 缺省#缺省
    return 配置值[键]#原值

def 地址种类(主机):
    '4、6 或 0。区号只出现在 IPv6 上'
    if not isinstance(主机,str) or 主机=='':#不是文本
        return 0#不是地址
    裸=主机#去掉区号前
    if '%' in 主机:#带区号
        裸,区号=主机.split('%',1)#拆开
        if 区号=='' or '%' in 区号 or ':' not in 裸:#区号不合法，或这不是 IPv6
            return 0#拒绝
    try:#解析
        地址=地址解析(裸)#地址
    except ValueError:#不是字面量
        return 0#拒绝
    if isinstance(地址,四版地址):#IPv4
        return 4#四
    return 6#六

def 解析地址字面量(主机):
    '具体 IP。点分尾巴按地址自己的低 32 位，IPv4 映射收成 IPv4。区号先拿掉'
    if 地址种类(主机)==0:#不是字面量
        return None#没有
    区号位置=主机.find('%')#区号
    裸=主机 if 区号位置<0 else 主机[:区号位置]#区号不是地址正文
    匹配=re.match(r'^(.*:)(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$',裸)#点分尾巴
    if 匹配 is not None:#改成两段十六进制，避免被当成映射地址
        高=(int(匹配.group(2))<<8)|int(匹配.group(3))#高 16 位
        低=(int(匹配.group(4))<<8)|int(匹配.group(5))#低 16 位
        裸=匹配.group(1)+format(高,'x')+':'+format(低,'x')#重写
    try:#再解析
        地址=地址解析(裸)#地址
    except ValueError:#重写后仍不合法
        return None#没有
    if isinstance(地址,六版地址) and 地址.ipv4_mapped is not None:#映射地址
        return 地址.ipv4_mapped#收成 IPv4
    return 地址#原地址

def 是通配地址(地址):
    '只有全零地址才算通配，0/8 里的其它地址不是'
    return bool(地址.is_unspecified)#全零

def 是通配主机(主机):
    'IPv4 全零、IPv6 全零，以及 IPv4 全零的映射写法'
    地址=解析地址字面量(主机)#地址
    if 地址 is None:#不是字面量
        return False#不是
    return 是通配地址(地址)#全零

def 是回环主机(主机):
    '127/8、::1，以及它们的映射写法和区号写法'
    地址=解析地址字面量(主机)#地址
    if 地址 is None:#不是字面量
        return False#不是
    return bool(地址.is_loopback)#回环

def 规范化绑定地址(主机):
    'IPv4 和映射地址写成点分四段，其余写成压缩 IPv6。区号不出现'
    地址=解析地址字面量(主机)#地址
    if 地址 is None:#不是字面量
        拒绝非字面地址(主机)#抛出
    return str(地址)#规范文本

def 绑定网址主机(主机):
    '回环用规范文本。其它地址保留原文。IPv6 加方括号。非回环区号写不进网址'
    区号位置=主机.find('%')#区号
    裸=主机 if 区号位置<0 else 主机[:区号位置]#去掉区号
    if (not 是回环主机(裸)) and 区号位置>=0:#非回环的区号
        return None#网址表达不了
    if 是回环主机(裸):#回环用规范文本
        文本=规范化绑定地址(裸)#规范
    else:#其余保留原文
        文本=主机#原文
    if 地址种类(文本)==6:#IPv6
        return '['+文本+']'#加括号
    return 文本#IPv4 或原文

def 路径名(网址):
    '查询不进路径。没有目标时当作 /'
    文本=网址 if isinstance(网址,str) and 网址!='' else '/'#目标
    路径=拆分网址(文本).path#路径
    if 路径=='':#空路径
        return '/'#根
    return 路径#路径

def 读取传输材料(字段,路径):
    '读一份 PEM。读不到或空文件都失败，避免听上一个完不成握手的端口'
    try:#读文本
        with open(路径,'r',encoding='utf-8') as 文件:#打开
            内容=文件.read()#全文
    except OSError as 错误:#读不到
        raise 网页服务器错误('webserver: cannot read tls.'+字段+' '+路径+': '+str(错误)) from 错误#带上字段和路径
    if 内容.strip()=='':#空文件
        raise 网页服务器错误('webserver: tls.'+字段+' '+路径+' is empty')#拒绝
    return 内容#PEM 文本


class 配置模式:
    '监听地址、端口、TLS 和压缩。通配地址在这里拒绝'
    def 校验数据(自身,数据=None):
        '补上压缩缺省。主机必须是具体 IP 字面量。显式 tls 空值保持空值'
        if 数据 is None:#加载器没给
            数据={}#空
        if not isinstance(数据,dict):#不是对象
            raise 网页服务器错误('webserver: config must be an object')#拒绝
        if 'host' not in 数据:#缺主机
            raise 网页服务器错误('webserver: host is required')#拒绝
        主机=数据['host']#原文
        地址=解析地址字面量(主机) if isinstance(主机,str) else None#地址
        if 地址 is None:#不是字面量
            拒绝非字面地址(主机)#抛出
        if 是通配地址(地址):#全零
            raise 网页服务器错误('webserver: host '+json.dumps(主机)+' is an unspecified (wildcard) address, which is not supported: binding every interface would expose remote code execution to the network; bind one concrete IPv4 or IPv6 address of a local interface instead')#拒绝通配
        if 'port' not in 数据:#缺端口
            raise 网页服务器错误('webserver: port is required')#拒绝
        端口=数据['port']#端口
        if isinstance(端口,bool) or not isinstance(端口,int) or 端口<0 or 端口>65535:#不是 0 到 65535
            raise 网页服务器错误('webserver: port must be a natural number up to 65535')#拒绝
        压缩=数据['compression'] if 'compression' in 数据 and 数据['compression'] is not None else 默认压缩#压缩
        if 压缩 not in ('none','gzip'):#只认这两种
            raise 网页服务器错误('webserver: compression must be none or gzip')#拒绝
        级别=数据['compressionLevel'] if 'compressionLevel' in 数据 and 数据['compressionLevel'] is not None else 默认压缩级别#级别
        if isinstance(级别,bool) or not isinstance(级别,int) or 级别<0 or 级别>9:#超出 0 到 9
            raise 网页服务器错误('webserver: compressionLevel must be an integer from 0 through 9')#拒绝
        阈值=数据['compressionThresholdBytes'] if 'compressionThresholdBytes' in 数据 and 数据['compressionThresholdBytes'] is not None else 默认压缩阈值#阈值
        if isinstance(阈值,bool) or not isinstance(阈值,int) or 阈值<0:#不是自然数
            raise 网页服务器错误('webserver: compressionThresholdBytes must be a natural number')#拒绝
        结果={'host':主机,'port':端口,'compression':压缩,'compressionLevel':级别,'compressionThresholdBytes':阈值}#解析结果
        if 'tls' in 数据:#写了 tls
            传输安全=数据['tls']#材料或空
            if 传输安全 is None:#显式空值
                结果['tls']=None#不当成缺省对象
            else:#必须是证书和私钥
                if not isinstance(传输安全,dict):#不是对象
                    raise 网页服务器错误('webserver: tls must be an object')#拒绝
                if 'certFile' not in 传输安全 or not isinstance(传输安全.get('certFile'),str):#缺证书
                    raise 网页服务器错误('missing required tls.certFile')#拒绝
                if 'keyFile' not in 传输安全 or not isinstance(传输安全.get('keyFile'),str):#缺私钥
                    raise 网页服务器错误('missing required tls.keyFile')#拒绝
                结果['tls']={'certFile':传输安全['certFile'],'keyFile':传输安全['keyFile']}#一对
        return 结果#交给构造

    def __call__(自身,数据=None):
        '直接调用时同样解析'
        return 自身.校验数据(数据)#解析

配置=配置模式()#插件 Config


class 事件表:
    'on / once / off'
    def __init__(自身):
        '按事件名存放'
        自身.表={}#监听器

    def on(自身,事件,监听):
        '追加'
        自身.表.setdefault(事件,[]).append(监听)#追加

    def off(自身,事件,监听):
        '没有则忽略'
        列表=自身.表.get(事件)#该事件
        if 列表 is not None and 监听 in 列表:#在
            列表.remove(监听)#摘

    def once(自身,事件,监听):
        '跑完就摘'
        def 一次(*参数):
            '摘掉后再调用'
            自身.off(事件,一次)#摘
            监听(*参数)#调用
        自身.on(事件,一次)#登记

    def 发出(自身,事件,*参数):
        '拷贝后再调，监听器可以改表'
        for 监听 in list(自身.表.get(事件,())):#逐个
            监听(*参数)#调用


class 套接字壳:
    '升级和原始连接上的 write / destroy / on / once / off'
    def __init__(自身,原始):
        '记下套接字'
        自身.原始=原始#套接字
        自身.destroyed=False#是否已拆
        自身.事件=事件表()#事件

    def write(自身,数据):
        '字符串按 utf-8 写出'
        if isinstance(数据,str):#文本
            数据=数据.encode('utf-8')#编码
        elif not isinstance(数据,(bytes,bytearray)):#其它
            数据=bytes(数据)#收成字节
        自身.原始.sendall(数据)#写出

    def destroy(自身,错误=None):
        '关掉并发出 close。带错误时先发出 error'
        if 自身.destroyed:#已经拆过
            return#停
        自身.destroyed=True#占住
        if 错误 is not None:#有错误
            自身.事件.发出('error',错误)#error
        try:#先停收发
            自身.原始.shutdown(关闭读写)#停
        except OSError as 已关闭:#套接字已经关了，再关一次不是新的失败
            已关闭=已关闭#留下这次错误，不往外抛
        try:#关
            自身.原始.close()#关
        except OSError as 已关闭:#套接字已经关了，再关一次不是新的失败
            已关闭=已关闭#留下这次错误，不往外抛
        自身.事件.发出('close')#close

    def on(自身,事件,监听):
        '登记'
        自身.事件.on(事件,监听)#登记

    def off(自身,事件,监听):
        '摘掉'
        自身.事件.off(事件,监听)#摘

    def once(自身,事件,监听):
        '只跑一次'
        自身.事件.once(事件,监听)#一次


class 字节读口:
    '从套接字读。多读进缓冲的字节留给正文或升级头'
    def __init__(自身,套接字):
        '缓冲开始是空的'
        自身.套接字=套接字#套接字
        自身.缓冲=b''#已读未取

    def 读到行(自身):
        '读到换行。对端关掉时把缓冲里剩下的交出来'
        while b'\n' not in 自身.缓冲:#还没换行
            片=自身.套接字.recv(4096)#再读
            if not 片:#对端关掉
                行=自身.缓冲#剩下的
                自身.缓冲=b''#清空
                return 行#可能没有换行
            自身.缓冲+=片#接上
        位置=自身.缓冲.index(b'\n')+1#含换行
        行=自身.缓冲[:位置]#这一行
        自身.缓冲=自身.缓冲[位置:]#留下
        return 行#一行

    def 读(自身,大小):
        '读出至多这么多字节'
        while len(自身.缓冲)<大小:#不够
            片=自身.套接字.recv(大小-len(自身.缓冲) if 大小-len(自身.缓冲)>4096 else 4096)#再读
            if not 片:#对端关掉
                break#有多少给多少
            自身.缓冲+=片#接上
        结果=自身.缓冲[:大小]#这一段
        自身.缓冲=自身.缓冲[大小:]#留下
        return 结果#字节


class 进入请求:
    'method / url / headers。正文用 read 或按块迭代，不先收成一整段'
    def __init__(自身,方法,网址,头,读口,套接字):
        '按 Content-Length 或分块记下还剩多少。两者都没有则正文是空的'
        自身.method=方法#方法
        自身.url=网址#原始目标，含查询
        自身.headers=头#小写头名
        自身.socket=套接字#连接
        自身._读口=读口#字节读口
        自身.readableEnded=False#正文是否读完
        自身.destroyed=False#是否已拆
        自身.事件=事件表()#事件
        自身._块剩余=None#当前分块还剩多少
        编码=头.get('transfer-encoding','')#传输编码
        if isinstance(编码,str) and 'chunked' in 编码.lower():#分块
            自身._分块=True#按块
            自身._剩余=0#不用长度
        else:#按长度
            自身._分块=False#不分块
            声明=头.get('content-length')#长度
            if 声明 is None:#没有正文
                自身._剩余=0#空
            else:#有长度
                自身._剩余=int(str(声明))#字节数

    def read(自身,大小=65536):
        '读下一块正文'
        if 自身.readableEnded:#已经读完
            return b''#空
        if 大小 is None or 大小<0:#没给大小
            大小=65536#一块
        if 自身._分块:#分块
            return 自身._读分块(大小)#一块
        if 自身._剩余<=0:#没有正文
            自身.readableEnded=True#读完
            return b''#空
        要读=大小 if 大小<自身._剩余 else 自身._剩余#不超过剩余
        块=自身._读口.读(要读)#读
        if not 块:#对端关掉
            自身.readableEnded=True#读完
            自身._剩余=0#清空
            return b''#空
        自身._剩余-=len(块)#扣掉
        if 自身._剩余<=0:#读完
            自身.readableEnded=True#标记
        return 块#这一块

    def _读分块(自身,大小):
        '读一块分块正文里的一段'
        if 自身._块剩余 is None:#需要下一块的长度
            行=自身._读口.读到行()#长度行
            文本=行.decode('latin-1').strip()#文本
            if 文本=='':#没有了
                自身.readableEnded=True#读完
                return b''#空
            try:#十六进制长度
                块长=int(文本.split(';',1)[0],16)#长度
            except ValueError:#不是长度
                自身.readableEnded=True#停
                return b''#空
            if 块长==0:#最后一块
                自身.readableEnded=True#读完
                while True:#丢掉尾头
                    尾=自身._读口.读到行()#一行
                    if 尾 in (b'',b'\r\n',b'\n'):#尾头结束
                        break#停
                return b''#空
            自身._块剩余=块长#这一块的长度
        要读=大小 if 大小<自身._块剩余 else 自身._块剩余#不超过这块
        数据=自身._读口.读(要读)#数据
        if not 数据:#对端关掉
            自身.readableEnded=True#停
            自身._块剩余=0#清空
            return b''#空
        自身._块剩余-=len(数据)#扣掉
        if 自身._块剩余<=0:#这块读完
            自身._读口.读(2)#块后面的 CRLF
            自身._块剩余=None#下一块
        return 数据#这一段

    def 排空剩余(自身):
        '响应结束后把没读的正文读掉，连接才能接下一条'
        while not 自身.readableEnded:#还有
            if not 自身.read(65536):#再读
                return#没有了

    def __iter__(自身):
        '按块交出正文'
        while True:#直到读完
            块=自身.read(65536)#一块
            if not 块:#没有了
                return#停
            yield 块#这一块

    def destroy(自身):
        '关掉这条连接'
        if 自身.destroyed:#已经拆过
            return#停
        自身.destroyed=True#占住
        自身.readableEnded=True#不再读
        try:#停
            自身.socket.shutdown(关闭读写)#停
        except OSError as 已关闭:#套接字已经关了，再关一次不是新的失败
            已关闭=已关闭#留下这次错误，不往外抛
        try:#关
            自身.socket.close()#关
        except OSError as 已关闭:#套接字已经关了，再关一次不是新的失败
            已关闭=已关闭#留下这次错误，不往外抛
        自身.事件.发出('close')#close

    def on(自身,事件,监听):
        '登记'
        自身.事件.on(事件,监听)#登记


class 服务器响应:
    'writeHead / write / end / getHeader / on / destroy。头在第一块正文时才写出'
    def __init__(自身,服务对象,套接字,结束回调):
        '头还没发'
        自身.服务=服务对象#网页服务器
        自身.socket=套接字#连接
        自身.结束回调=结束回调#放开连接线程
        自身.头={}#小写头名
        自身.状态=200#默认
        自身.headersSent=False#调用方是否已要求发头
        自身.writableEnded=False#是否已 end
        自身.destroyed=False#是否已拆
        自身._头已写=False#状态行是否已进套接字
        自身._分块=False#是否用分块
        自身._已收尾=False#close 与结束回调只走一次
        自身._已通知关闭=False#close 只发一次
        自身.事件=事件表()#事件
        with 服务对象.锁:#登记在途响应
            服务对象.在途响应.add(自身)#拆除时要叫醒

    def getHeader(自身,名):
        '大小写不敏感'
        if not isinstance(名,str):#不是字符串
            return None#没有
        return 自身.头.get(名.lower())#值或 None

    def writeHead(自身,状态,头=None):
        '真正写出推迟到第一块正文'
        自身.状态=状态#状态
        if isinstance(头,dict):#有头
            for 键,值 in 头.items():#逐个
                自身.头[str(键).lower()]=值#收下
        自身.headersSent=True#调用方视为已发

    def _写头(自身,分块):
        '把状态行和头写进套接字。未知长度用分块'
        if 自身._头已写:#已写
            return#停
        自身._头已写=True#占住
        自身.headersSent=True#已发
        if 分块 and 'content-length' not in 自身.头 and 'transfer-encoding' not in 自身.头:#长度未知
            自身.头['transfer-encoding']='chunked'#分块
            自身._分块=True#标记
        原因=状态短语.get(自身.状态,'OK')#短语
        行=['HTTP/1.1 '+str(自身.状态)+' '+原因]#状态行
        for 键,值 in 自身.头.items():#头
            行.append(键+': '+str(值))#一行
        数据=('\r\n'.join(行)+'\r\n\r\n').encode('latin-1','replace')#头块
        自身.socket.sendall(数据)#写出

    def write(自身,块):
        '字符串按 utf-8。写失败就拆掉连接'
        if 自身.writableEnded or 自身.destroyed:#已经结束
            return False#不能再写
        if isinstance(块,str):#文本
            块=块.encode('utf-8')#编码
        elif not isinstance(块,(bytes,bytearray)):#其它
            块=bytes(块)#收成字节
        if not 块:#空块
            return True#没有要写的
        try:#写出
            自身._写头(True)#先头
            if 自身._分块:#分块
                自身.socket.sendall(format(len(块),'x').encode('ascii')+b'\r\n'+块+b'\r\n')#一块
            else:#定长或调用方自己算好了
                自身.socket.sendall(块)#正文
        except OSError:#连接断了
            自身.destroy()#拆
            return False#失败
        return True#写进了

    def end(自身,正文=None):
        '可选最后一块。还没写头时补上长度'
        if 自身.writableEnded or 自身.destroyed:#已经结束
            return#停
        if isinstance(正文,str):#文本
            正文=正文.encode('utf-8')#编码
        elif 正文 is not None and not isinstance(正文,(bytes,bytearray)):#其它
            正文=bytes(正文)#收成字节
        try:#写出
            if not 自身._头已写:#头还在内存里
                if 正文 is not None and 'content-length' not in 自身.头:#一次写完
                    自身.头['content-length']=str(len(正文))#长度
                elif 正文 is None and 'content-length' not in 自身.头 and 'transfer-encoding' not in 自身.头 and 'content-encoding' not in 自身.头:#空正文
                    自身.头['content-length']='0'#零长度
                自身._写头(False)#头
                if 正文:#有正文
                    自身.socket.sendall(正文)#一次写出
            else:#头已经出去了
                if 正文:#还有正文
                    自身.write(正文)#一块
                if 自身._分块 and not 自身.destroyed:#结束分块
                    自身.socket.sendall(b'0\r\n\r\n')#结尾
        except OSError:#连接断了
            自身.destroy()#拆
            return#停
        if not 自身.destroyed:#还活着
            自身.writableEnded=True#结束
            自身._收尾()#close

    def _收尾(自身):
        '发出 close，并放开等这条响应的连接线程'
        if 自身._已收尾:#已经收过
            return#停
        自身._已收尾=True#占住
        自身.writableEnded=True#结束
        with 自身.服务.锁:#摘掉在途
            自身.服务.在途响应.discard(自身)#摘
        if not 自身._已通知关闭:#close 只发一次
            自身._已通知关闭=True#占住
            自身.事件.发出('close')#close
        自身.结束回调()#放开

    def destroy(自身):
        '关掉套接字'
        if 自身.destroyed:#已经拆过
            return#停
        自身.destroyed=True#占住
        自身.writableEnded=True#结束
        try:#停
            自身.socket.shutdown(关闭读写)#停
        except OSError as 已关闭:#套接字已经关了，再关一次不是新的失败
            已关闭=已关闭#留下这次错误，不往外抛
        try:#关
            自身.socket.close()#关
        except OSError as 已关闭:#套接字已经关了，再关一次不是新的失败
            已关闭=已关闭#留下这次错误，不往外抛
        自身._收尾()#close

    def on(自身,事件,监听):
        '登记'
        自身.事件.on(事件,监听)#登记

    def off(自身,事件,监听):
        '摘掉'
        自身.事件.off(事件,监听)#摘

    def once(自身,事件,监听):
        '只跑一次'
        自身.事件.once(事件,监听)#一次


class 压缩响应:
    '套在真实响应外面。事件流和区间不压。已知长度低于阈值不压'
    def __init__(自身,内层,请求,级别,阈值):
        '先按 Accept-Encoding 在 gzip 和 identity 里选一个'
        自身.内层=内层#真实响应
        自身.请求=请求#方法与头
        自身.级别=级别#deflate 级别
        自身.阈值=阈值#已知长度阈值
        自身.socket=内层.socket#给中间件看
        自身.headersSent=False#转发
        自身.writableEnded=False#转发
        自身.destroyed=False#转发
        自身.已决定=False#还没看类型
        自身.直通=True#默认不压
        自身.压缩器=None#要压时才建
        头值=请求.headers.get('accept-encoding') if isinstance(请求.headers,dict) else None#客户端编码
        选择='identity'#默认不压
        if isinstance(头值,str) and 头值.strip()!='':#有头
            项列表=[]#名字、质量、顺序
            最低=1.0#已出现项里最低的质量
            有标识=False#是否写了 identity
            序号=0#顺序
            for 片段 in 头值.split(','):#逐项
                片段=片段.strip()#去掉空白
                if 片段=='':#空项
                    continue#下一项
                部分=片段.split(';')#名字和参数
                名=部分[0].strip().lower()#编码名
                质量=1.0#默认质量
                for 参数 in 部分[1:]:#参数
                    参数=参数.strip()#去掉空白
                    if 参数.lower().startswith('q='):#质量
                        try:#转数字
                            质量=float(参数[2:])#质量
                        except ValueError:#不是数字
                            质量=0.0#当作不接受
                if 名=='identity':#显式 identity
                    有标识=True#记下
                if 质量<最低:#更低
                    最低=质量#记下
                项列表.append((名,质量,序号))#一项
                序号+=1#下一项
            if not 有标识:#没写 identity 时用最低质量补上
                项列表.append(('identity',最低,序号))#补上
            候选=[编码项 for 编码项 in 项列表 if 编码项[0] in ('gzip','identity') and 编码项[1]>0]#还能选的
            if 候选:#有候选
                def 编码排序(编码项):
                    '质量高的在前，同质量保持出现顺序'
                    return (-编码项[1],编码项[2])#质量、顺序
                候选.sort(key=编码排序)#函数对象交给排序，函数本身留着
                选择=候选[0][0]#选中
        自身.要gzip=选择=='gzip'#是否压

    def getHeader(自身,名):
        '转发'
        return 自身.内层.getHeader(名)#转发

    def _决定(自身,收尾块):
        '头还没进套接字时决定压不压，并写上 Vary'
        if 自身.已决定:#已经决定
            return#停
        自身.已决定=True#占住
        类型=自身.内层.getHeader('content-type')#类型
        if 自身.内层.getHeader('content-range') is not None:#区间
            自身.直通=True#不压
            return#停
        if isinstance(类型,str) and 类型.lower().startswith('text/event-stream'):#事件流
            自身.直通=True#不压
            return#停
        可压=False#默认可不压
        if isinstance(类型,str) and re.match(r'multipart/form-data(?:;|$)',类型,re.I) is not None:#表单
            可压=True#总是可以压
        elif isinstance(类型,str):#按媒体类型
            媒体=类型.split(';',1)[0].strip().lower()#去掉参数
            if 媒体.startswith('text/') or 媒体.endswith('+json') or 媒体.endswith('+xml'):#文本和结构化文本
                可压=True#可压
            elif 媒体 in ('application/json','application/javascript','application/xml','application/xhtml+xml','image/svg+xml','application/rss+xml','application/atom+xml'):#常见可压类型
                可压=True#可压
        if not 可压:#不可压
            自身.直通=True#不压
            return#停
        已有=自身.内层.getHeader('vary')#已有 Vary
        if 已有 is None:#没有
            自身.内层.头['vary']='Accept-Encoding'#加上
        elif 'accept-encoding' not in str(已有).lower():#还没写这项
            自身.内层.头['vary']=str(已有)+', Accept-Encoding'#接上
        长度=None#已知长度
        声明=自身.内层.getHeader('content-length')#声明长度
        if isinstance(声明,bool):#布尔不是长度
            长度=None#未知
        elif isinstance(声明,int):#数字
            长度=声明#长度
        elif isinstance(声明,str) and 声明.isdigit():#十进制
            长度=int(声明)#长度
        elif 收尾块 is not None:#一次 end 的正文可以当已知长度
            if isinstance(收尾块,str):#文本
                长度=len(收尾块.encode('utf-8'))#字节
            else:#字节
                长度=len(bytes(收尾块))#字节
        if 长度 is not None and 长度<自身.阈值:#低于阈值
            自身.直通=True#不压
            return#停
        编码=自身.内层.getHeader('content-encoding') or 'identity'#已有编码
        if 编码!='identity':#已经编码过
            自身.直通=True#不再压
            return#停
        if 自身.请求.method=='HEAD':#没有正文
            自身.直通=True#不压
            return#停
        if not 自身.要gzip:#客户端不要 gzip
            自身.直通=True#不压
            return#停
        自身.内层.头.pop('content-length',None)#压缩后长度作废
        自身.内层.头['content-encoding']='gzip'#编码
        自身.压缩器=压缩对象(自身.级别,压缩算法,16+窗口位数)#gzip
        自身.直通=False#要压

    def writeHead(自身,状态,头=None):
        '先让内层记下头，再决定压不压'
        自身.内层.writeHead(状态,头)#转发
        自身.headersSent=自身.内层.headersSent#同步
        自身._决定(None)#这时还不知道后续正文的总长

    def write(自身,块):
        '直通则立刻转发。要压就交给压缩器'
        if not 自身.已决定:#还没决定
            自身._决定(None)#按当前头决定
        if isinstance(块,str):#文本
            块=块.encode('utf-8')#编码
        elif not isinstance(块,(bytes,bytearray)):#其它
            块=bytes(块)#收成字节
        if 自身.直通:#不压
            写下=自身.内层.write(块)#转发
            自身.destroyed=自身.内层.destroyed#同步
            return 写下#结果
        if not 块:#空块
            return True#没有要写的
        压缩后=自身.压缩器.compress(块)#压缩
        if not 压缩后:#还留在压缩器里
            return True#稍后 flush
        写下=自身.内层.write(压缩后)#写出
        自身.destroyed=自身.内层.destroyed#同步
        return 写下#结果

    def end(自身,正文=None):
        '结束时把压缩器里剩下的吐出来'
        if 自身.writableEnded:#已经结束
            return#停
        if not 自身.已决定:#还没决定
            自身._决定(正文)#一次写完时正文长度参与阈值
        if 自身.直通:#不压
            自身.内层.end(正文)#转发
            自身.writableEnded=True#结束
            自身.destroyed=自身.内层.destroyed#同步
            自身.headersSent=自身.内层.headersSent#同步
            return#停
        if 正文 is not None:#最后一块
            自身.write(正文)#压进去
        尾=自身.压缩器.flush()#收尾
        if 尾:#还有尾字节
            自身.内层.write(尾)#写出
        自身.内层.end()#结束分块
        自身.writableEnded=True#结束
        自身.destroyed=自身.内层.destroyed#同步

    def destroy(自身):
        '转发'
        自身.内层.destroy()#转发
        自身.destroyed=True#同步
        自身.writableEnded=True#结束

    def on(自身,事件,监听):
        '转发'
        自身.内层.on(事件,监听)#转发

    def off(自身,事件,监听):
        '转发'
        自身.内层.off(事件,监听)#转发

    def once(自身,事件,监听):
        '转发'
        自身.内层.once(事件,监听)#转发


class 处理器(socketserver.BaseRequestHandler):
    '一条连接。正文留在读口里，路由处理时才按块读'
    def handle(自身):
        '普通请求走路由。Upgrade 把套接字交出去'
        服务对象=自身.server.服务#网页服务器
        原始=自身.request#接受时的套接字
        套接字=原始#可能再包一层 TLS
        升级了=False#升级后不能在这里关套接字
        try:#连接结束时再决定关不关
            if 自身.server.安全上下文 is not None:#HTTPS
                try:#握手
                    套接字=自身.server.安全上下文.wrap_socket(套接字,server_side=True)#握手
                except Exception as 错误:#握手失败
                    服务对象.记录(错误)#记
                    return#停
            读口=字节读口(套接字)#这一条连接的读口
            while True:#可能保持连接
                try:#读请求行
                    请求行=读口.读到行()#请求行
                except OSError:#连接断了
                    break#停
                if 请求行==b'':#对端关掉
                    break#停
                文本=请求行.decode('latin-1').rstrip('\r\n')#请求行文本
                部分=文本.split(' ')#方法、目标、版本
                if len(部分)<2:#畸形
                    try:#回 400
                        套接字.sendall(b'HTTP/1.1 400 Bad Request\r\ncontent-length: 0\r\nconnection: close\r\n\r\n')#坏请求
                    except OSError as 写失败:#连接已经没了
                        写失败=写失败#回 400 失败就直接停
                    break#停
                方法=部分[0]#方法
                目标=部分[1]#原始目标
                版本=部分[2] if len(部分)>2 else 'HTTP/1.1'#版本
                头={}#小写头名
                头坏了=False#头是否畸形
                while True:#读头
                    try:#一行
                        行=读口.读到行()#头行
                    except OSError:#连接断了
                        头坏了=True#停
                        break#停
                    if 行 in (b'',b'\r\n',b'\n'):#头结束
                        break#停
                    头文本=行.decode('latin-1').rstrip('\r\n')#文本
                    冒号=头文本.find(':')#冒号
                    if 冒号<=0:#畸形
                        头坏了=True#停
                        break#停
                    名=头文本[:冒号].strip().lower()#小写名
                    值=头文本[冒号+1:].strip()#值
                    if 名 in 头:#重复
                        头[名]=头[名]+', '+值#按逗号接上
                    else:#第一次
                        头[名]=值#收下
                if 头坏了:#头没读完
                    try:#回 400
                        套接字.sendall(b'HTTP/1.1 400 Bad Request\r\ncontent-length: 0\r\nconnection: close\r\n\r\n')#坏请求
                    except OSError as 写失败:#连接已经没了
                        写失败=写失败#回 400 失败就直接停
                    break#停
                if 'upgrade' in 头:#升级
                    壳=套接字壳(套接字)#交给升级处理的套接字
                    头字节=读口.缓冲#头读完后多读到的字节
                    读口.缓冲=b''#从读口拿走
                    def 出错(错误):
                        '升级失败就记日志并拆套接字'
                        服务对象.记录(错误)#记
                        壳.destroy()#拆
                    def 关掉():
                        '关掉就摘掉错误监听，并拆掉原始连接跟踪'
                        壳.off('error',出错)#摘
                        with 服务对象.锁:#改表
                            服务对象.升级套接字.discard(壳)#摘
                            跟踪=服务对象.按套接字.get(id(原始))#原始连接
                        if 跟踪 is not None and not 跟踪.destroyed:#还在跟踪
                            跟踪.destroy()#拆掉
                    壳.on('error',出错)#错误
                    壳.once('close',关掉)#关闭
                    try:#找精确路径
                        路径=路径名(目标)#路径
                        with 服务对象.锁:#读表
                            路由=服务对象.升级.get(路径)#路由
                    except Exception as 错误:#坏目标
                        服务对象.记录(错误)#记
                        壳.destroy()#拆
                        升级了=True#套接字已经交给壳
                        return#停
                    if 路由 is None:#没有主人
                        壳.destroy()#拆
                        升级了=True#套接字已经交给壳
                        return#停
                    with 服务对象.锁:#跟踪
                        服务对象.升级套接字.add(壳)#记下
                    try:#交给主人
                        路由['handler'](进入请求(方法,目标,头,读口,套接字),壳,头字节)#升级
                    except Exception as 错误:#同步失败
                        服务对象.记录(错误)#记
                        壳.destroy()#拆
                    升级了=True#连接线程不再读下一条
                    return#套接字留给升级处理
                try:#普通请求
                    请求=进入请求(方法,目标,头,读口,套接字)#请求
                except Exception as 错误:#长度坏了
                    服务对象.记录(错误)#记
                    break#停
                结束=事件门闩()#响应结束
                内层=服务器响应(服务对象,套接字,结束.set)#响应
                响应=内层#交给路由的对象
                if 服务对象.压缩名=='gzip' and 内层.socket is not None:#gzip，且这条响应有套接字
                    响应=压缩响应(内层,请求,服务对象.压缩级别,服务对象.压缩阈值)#包装
                try:#派发
                    路径=路径名(请求.url)#路径
                    with 服务对象.锁:#读表
                        路由=服务对象.精确.get(路径)#精确
                        if 路由 is None:#再看前缀
                            最好=None#最长前缀
                            最好长度=-1#长度
                            for 前缀,候选 in 服务对象.前缀.items():#逐个
                                if 路径!=前缀 and not 路径.startswith(前缀+'/'):#不命中
                                    continue#下一个
                                if 最好 is None or len(前缀)>最好长度:#更长
                                    最好=候选#记下
                                    最好长度=len(前缀)#长度
                            路由=最好#可能没有
                        回退=服务对象.回退#回退席
                    if 路由 is not None:#命中
                        路由['handler'](请求,响应)#交给主人
                    elif 回退 is not None:#回退
                        回退(请求,响应)#回退
                    else:#没有人接
                        响应.writeHead(404)#未找到
                        响应.end()#结束
                except Exception as 错误:#处理失败
                    服务对象.记录(错误)#记
                    if not 内层.headersSent:#还没写头
                        内层.writeHead(400)#坏请求
                        内层.end()#结束
                    else:#头已发
                        内层.destroy()#拆掉
                结束.wait()#等到 end 或 destroy
                try:#没读完的正文读掉
                    请求.排空剩余()#排空
                except OSError:#连接断了
                    break#停
                请求连接=请求.headers.get('connection','')#请求要求
                响应连接=内层.getHeader('connection')#响应要求
                if isinstance(请求连接,str) and 请求连接.lower()=='close':#不保持
                    break#停
                if isinstance(响应连接,str) and 响应连接.lower()=='close':#不保持
                    break#停
                if 版本=='HTTP/1.0' and str(请求.headers.get('connection','')).lower()!='keep-alive':#1.0 默认关闭
                    break#停
        finally:#非升级连接在线程退出时拆掉跟踪
            if not 升级了:#还归这条连接管
                with 服务对象.锁:#取出壳
                    壳=服务对象.按套接字.get(id(原始))#原始连接
                if 壳 is not None and not 壳.destroyed:#还活着
                    壳.destroy()#拆


class 线程服务器(线程混入,传输控制服务器):
    '每条连接一个线程。绑定失败由调用方收成端口占用'
    daemon_threads=True#随进程退出
    allow_reuse_address=False#第二个人绑定同一端口要失败
    def __init__(自身,地址,服务对象,安全上下文):
        '按地址族绑定。端口 0 由系统分配'
        自身.服务=服务对象#网页服务器
        自身.安全上下文=安全上下文#没有则为空
        主机=地址[0]#主机
        端口=地址[1]#端口
        裸=主机.split('%',1)[0]#区号不参与判断地址族
        自身.address_family=六版族 if ':' in 裸 else 四版族#地址族
        自身.allow_reuse_address=False#不复用
        信息=取地址信息(主机,端口,自身.address_family,流式套接字)#系统地址
        传输控制服务器.__init__(自身,信息[0][4],处理器)#绑定

    def get_request(自身):
        '接受后立刻跟踪原始套接字，握手还没完成也能在拆除时关掉'
        原始,地址=传输控制服务器.get_request(自身)#接受
        壳=套接字壳(原始)#跟踪壳
        with 自身.服务.锁:#登记
            自身.服务.传输连接.add(壳)#跟踪
            自身.服务.按套接字[id(原始)]=壳#给连接线程收尾
        def 摘掉():
            '关闭后不再跟踪'
            with 自身.服务.锁:#摘
                自身.服务.传输连接.discard(壳)#摘
                if 自身.服务.按套接字.get(id(原始)) is 壳:#还是这一只
                    自身.服务.按套接字.pop(id(原始),None)#摘
        壳.once('close',摘掉)#关闭
        return 原始,地址#交给连接线程

    def handle_error(自身,请求,客户地址):
        '连接线程里没接住的错误只记日志'
        信息=sys.exc_info()[1]#当前错误
        if 信息 is not None:#有错误
            自身.服务.记录(信息)#警告


class 网页服务器(服务):
    '启动即监听。同一种类加路径不能重复。回退席只能有一个主人'
    name=名称#插件名
    inject=依赖#无硬依赖
    Config=配置#配置模式
    def __init__(自身,上下文,配置值=None):
        '只记下配置。读证书和 bind 在初始化'
        super().__init__(上下文,'webServer')#服务名
        if 配置值 is None:#无配置
            配置值={}#空
        自身.配置主机=配置值['host']#绑定主机原文
        自身.配置端口=配置值['port']#端口
        if 'tls' in 配置值 and 配置值['tls'] is not None:#有证书配置
            自身.传输安全=配置值['tls']#证书和私钥路径
        else:#明文
            自身.传输安全=None#不启用 TLS
        自身.压缩名=取配置(配置值,'compression',默认压缩)#none 或 gzip
        自身.压缩级别=取配置(配置值,'compressionLevel',默认压缩级别)#级别
        自身.压缩阈值=取配置(配置值,'compressionThresholdBytes',默认压缩阈值)#阈值
        自身.精确={}#精确路由
        自身.前缀={}#前缀路由
        自身.升级={}#升级路由
        自身.升级套接字=set()#仍活着的升级套接字
        自身.传输连接=set()#原始连接，含还在握手的
        自身.按套接字={}#原始套接字身份到跟踪壳
        自身.在途响应=set()#还没 end 的响应
        自身.索引变换=[]#tapIndex
        自身.回退=None#回退处理
        自身.监听端口=None#bind 之后才有
        自身.锁=锁()#路由表和连接表
        自身.服务器=None#监听套接字
        自身.线程=None#serve_forever 线程
        自身.安全上下文=None#初始化时才装证书
        设置内部数据(自身,服务.初始化,自身._初始化)#依赖就绪后监听

    @property
    def port(自身):
        '配置端口为 0 时这里是系统分配的值。还没 bind 则是空'
        return 自身.监听端口#端口

    @property
    def host(自身):
        '配置里的绑定地址，区号也留着'
        return 自身.配置主机#主机

    @property
    def protocol(自身):
        '配置了 TLS 就是 https:。看配置，不看某条请求的头'
        if 自身.传输安全 is None:#明文
            return 'http:'#http
        return 'https:'#https

    def getOrigin(自身):
        '本机客户端访问这个监听器的根网址'
        主机=绑定网址主机(自身.配置主机)#网址里的主机
        if 主机 is None:#区号写不进网址
            raise 网页服务器错误('webserver: bind address '+json.dumps(自身.配置主机)+' carries an interface zone id, which no URL can express')#拒绝
        if 自身.监听端口 is None:#还没 bind
            raise 网页服务器错误('webserver: origin read before the listener bound a port')#拒绝
        return 自身.protocol+'//'+主机+':'+str(自身.监听端口)#源

    def register(自身,路由):
        '重复的种类加路径直接抛'
        表=自身.精确 if 路由['kind']=='exact' else 自身.前缀#目标表
        with 自身.锁:#改表
            if 路由['path'] in 表:#重复
                raise 网页服务器错误('webserver: duplicate '+路由['kind']+' route "'+路由['path']+'"')#冲突
            表[路由['path']]=路由#记下
        def 拆除():
            '删掉这条路由'
            with 自身.锁:#改表
                if 表.get(路由['path']) is 路由:#还是这一条
                    del 表[路由['path']]#摘
        return 拆除#拆除器

    def registerUpgrade(自身,路由):
        '同一路径只能有一个协议主人'
        with 自身.锁:#改表
            if 路由['path'] in 自身.升级:#重复
                raise 网页服务器错误('webserver: duplicate upgrade route "'+路由['path']+'"')#冲突
            自身.升级[路由['path']]=路由#记下
        def 拆除():
            '删掉这条升级'
            with 自身.锁:#改表
                if 自身.升级.get(路由['path']) is 路由:#还是这一条
                    del 自身.升级[路由['path']]#摘
        return 拆除#拆除器

    def registerFallback(自身,处理):
        '第二个登记直接抛'
        with 自身.锁:#改
            if 自身.回退 is not None:#已有
                raise 网页服务器错误('webserver: fallback already registered')#冲突
            自身.回退=处理#占住
        def 拆除():
            '清空回退'
            with 自身.锁:#改
                if 自身.回退 is 处理:#还是这个
                    自身.回退=None#清空
        return 拆除#拆除器

    def tapIndex(自身,变换):
        '按登记顺序，排在结构化行之后'
        自身.索引变换.append(变换)#追加
        def 拆除():
            '按身份删除'
            if 变换 in 自身.索引变换:#还在
                自身.索引变换.remove(变换)#摘
        return 拆除#拆除器

    def applyIndexTaps(自身,页面):
        '按登记顺序跑裸变换'
        输出=页面#工作副本
        for 变换 in 自身.索引变换:#逐个
            输出=变换(输出)#变换
        return 输出#结果

    def collectIndexInjections(自身):
        '每次调用都新发一次 webserver/index-inject'
        表=[]#可变行表
        自身.所属上下文.广播('webserver/index-inject',表)#听众往里追加
        return 表#激活顺序

    def renderIndex(自身,页面):
        '先行，再跑 tapIndex'
        已渲染=渲染索引注入(页面,自身.collectIndexInjections())#结构化行
        return 自身.applyIndexTaps(已渲染)#裸变换

    def 记录(自身,错误):
        '记警告，不退出进程'
        if not isinstance(错误,Exception):#不是异常
            错误=网页服务器错误(str(错误))#收成异常
        自身.所属上下文.日志.警告(错误)#警告

    def _初始化(自身):
        '读 TLS，然后 bind。失败则这条纤程失败'
        安全上下文=None#默认明文
        if 自身.传输安全 is not None:#要 HTTPS
            证书路径=绝对路径(自身.传输安全['certFile'])#证书绝对路径
            密钥路径=绝对路径(自身.传输安全['keyFile'])#私钥绝对路径
            读取传输材料('certFile',证书路径)#空文件或读不到就失败
            读取传输材料('keyFile',密钥路径)#空文件或读不到就失败
            安全上下文=安全上下文类(服务端协议)#TLS
            try:#装上这一对
                安全上下文.load_cert_chain(certfile=证书路径,keyfile=密钥路径)#证书和私钥
            except Exception as 错误:#配不上或 PEM 坏了
                raise 网页服务器错误('webserver: tls.certFile '+证书路径+' and tls.keyFile '+密钥路径+' are not a usable certificate and key pair: '+str(错误)) from 错误#在 bind 之前失败
        自身.安全上下文=安全上下文#连接线程用它握手
        try:#绑定
            自身.服务器=线程服务器((自身.配置主机,自身.配置端口),自身,安全上下文)#监听
            自身.监听端口=自身.服务器.server_address[1]#实际端口
            服务线程=线程(target=自身.服务器.serve_forever,daemon=True)#服务线程
            服务线程.start()#开始接
            自身.线程=服务线程#记下
        except OSError as 错误:#绑定失败
            if 自身.服务器 is not None:#已经建出来了
                try:#把监听套接字关掉
                    自身.服务器.server_close()#关
                except OSError as 已关闭:#监听套接字已经关了，再关一次不是新的失败
                    已关闭=已关闭#留下这次错误，不往外抛
                自身.服务器=None#清掉
            码=getattr(错误,'winerror',None)#Windows 错误码
            if 码 is None:#其它系统
                码=getattr(错误,'errno',None)#errno
            if 码 in (地址占用码,10048):#端口占用
                raise 网页服务器错误('listen EADDRINUSE: address already in use '+自身.配置主机+':'+str(自身.配置端口)) from 错误#跟监听失败同一句
            raise#其它错误原样抛
        def 关闭():
            '关掉监听、在途响应、原始连接和升级套接字'
            服务器=自身.服务器#监听器
            if 服务器 is not None:#有监听
                try:#先停接受
                    服务器.shutdown()#停 accept
                finally:#再关监听套接字
                    服务器.server_close()#关
            with 自身.锁:#抄出再拆，拆的时候会改这些表
                升级=list(自身.升级套接字)#升级
                连接=list(自身.传输连接)#原始连接
                响应=list(自身.在途响应)#还开着的响应
            for 套接字 in 升级:#升级连接
                套接字.destroy()#拆
            for 套接字 in 连接:#原始连接，含还在握手的
                套接字.destroy()#拆
            for 一条 in 响应:#还没 end 的响应
                一条.destroy()#拆
            if 自身.线程 is not None:#服务线程
                自身.线程.join()#等它退出
        yield 关闭#拆除器

default=网页服务器#类插件
name=名称#框架槽
inject=依赖#框架槽
Config=配置#框架槽
