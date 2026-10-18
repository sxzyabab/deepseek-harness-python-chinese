import base64,hashlib,json,socket,threading#握手、HTTP与套接字
from .....基础设施.通用工具.序列化编码 import 紧凑json编码
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer#HTTP服务
from urllib.parse import urlparse as 解析网址#路径解析
from ..cdp.会话 import Cdp会话#CDP会话
from ...异常 import 检查器错误#本包错误
from ...共享.网页 import 读检查器客户端选择#Client 选择

__all__=['检查器端点']#仅中文公开名

握手魔数='258EAFA5-E914-47DA-95CA-C5AB0DC85B11'#RFC6455


def 编码网页套接字帧(操作码,载荷):
    '服务端帧不打掩码，FIN 置位'
    长度=len(载荷)#载荷长度
    if 长度<126:#短帧
        头=bytes([0x80|操作码,长度])#7 位长度
    elif 长度<65536:#中帧
        头=bytes([0x80|操作码,126])+长度.to_bytes(2,'big')#16 位长度
    else:#长帧
        头=bytes([0x80|操作码,127])+长度.to_bytes(8,'big')#64 位长度
    return 头+载荷#完整帧


class 检查器套接字:
    '升级完成之后的一条 WebSocket。readyState 1 表示已开'
    def __init__(自身,套接字,读流,最大载荷):
        '先不读，等 message 监听挂上'
        自身.原始=套接字#原始 TCP
        自身._读流=读流#已经吃进 HTTP 头的缓冲
        自身._最大载荷=最大载荷#与上游 maxPayload 相同
        自身.readyState=0#尚未 101
        自身._监听={}#事件名到监听
        自身._写锁=threading.Lock()#写帧串行

    def on(自身,事件,监听):
        '登记监听'
        自身._监听.setdefault(事件,[]).append(监听)#追加

    def once(自身,事件,监听):
        '只调用一次'
        def 一次(*参数):
            '摘掉自己再调用'
            自身.off(事件,一次)#摘
            监听(*参数)#调用
        自身.on(事件,一次)#登记

    def off(自身,事件,监听):
        '按身份摘掉'
        表=自身._监听.get(事件)#这一类
        if 表 is not None and 监听 in 表:#还在
            表.remove(监听)#摘

    def _发出(自身,事件,*参数):
        '同步通知当前监听'
        for 监听 in list(自身._监听.get(事件,())):#拷贝
            监听(*参数)#调用

    def 握手(自身,请求头):
        '写出 101。缺 Key 或版本不是 13 则 400，返回是否已升级'
        键=请求头.get('Sec-WebSocket-Key')#客户端键
        版本=str(请求头.get('Sec-WebSocket-Version') or '')#必须 13
        if not isinstance(键,str) or 键=='' or 版本!='13':#不能升级
            自身.原始.sendall(b'HTTP/1.1 400 Bad Request\r\nConnection: close\r\nContent-Length: 0\r\n\r\n')#400
            try:#关掉
                自身.原始.close()#关
            except OSError:#已经关了
                pass#忽略
            return False#未占有
        摘要=hashlib.sha1((键+握手魔数).encode('ascii')).digest()#接受摘要
        接受=base64.b64encode(摘要).decode('ascii')#接受键
        响应=(#101
            'HTTP/1.1 101 Switching Protocols\r\n'
            'Upgrade: websocket\r\n'
            'Connection: Upgrade\r\n'
            'Sec-WebSocket-Accept: '+接受+'\r\n\r\n'
        )#响应结束
        自身.原始.sendall(响应.encode('ascii'))#发出
        自身.readyState=1#已开
        return True#调用方占有套接字

    def 开始读(自身):
        '监听挂好之后再读，避免丢第一帧'
        threading.Thread(target=自身._读循环,daemon=True).start()#读线程

    def send(自身,文本):
        '未开不写。文本按 UTF-8 成一帧'
        if 自身.readyState!=1:#未开
            return#不写
        数据=文本.encode('utf-8') if isinstance(文本,str) else bytes(文本)#字节
        with 自身._写锁:#串行
            自身.原始.sendall(编码网页套接字帧(1,数据))#文本帧

    def close(自身,码=1000,原因=''):
        '先送关闭帧再拆。原因截到 123 字节'
        if 自身.readyState>=2:#已经在关
            return#停
        自身.readyState=2#关闭中
        if isinstance(原因,str):#文本原因
            原因字节=原因.encode('utf-8')[:123]#截断
        else:#已经是字节
            原因字节=bytes(原因)[:123]#截断
        载荷=int(码).to_bytes(2,'big')+原因字节#关闭载荷
        try:#对方可能已经没了
            with 自身._写锁:#串行
                自身.原始.sendall(编码网页套接字帧(8,载荷))#关闭帧
        except OSError:#写不出去
            pass#接着拆
        自身.terminate()#拆

    def terminate(自身):
        '不再读写，发出 close'
        if 自身.readyState==3:#已经关
            return#停
        自身.readyState=3#已关
        try:#先停收发
            自身.原始.shutdown(socket.SHUT_RDWR)#停
        except OSError:#已经停了
            pass#忽略
        try:#关
            自身.原始.close()#关
        except OSError:#已经关了
            pass#忽略
        自身._发出('close')#close

    def _读确切(自身,数量):
        '从升级后的缓冲读满'
        块=b''#已读
        while len(块)<数量:#还不够
            片=自身._读流.read(数量-len(块))#再读
            if not 片:#对端关了
                raise EOFError('socket closed')#结束
            块+=片#拼上
        return 块#满

    def _读一帧(自身):
        '读一帧并解开客户端掩码。超限或没掩码用 ValueError 告诉读循环'
        头=自身._读确切(2)#基本头
        操作码=头[0] & 0x0f#操作码
        终帧=(头[0] & 0x80)!=0#是否最后一帧
        长度=头[1] & 0x7f#长度
        有掩码=(头[1] & 0x80)!=0#客户端必须打掩码
        if 长度==126:#两字节长度
            长度=int.from_bytes(自身._读确切(2),'big')#长度
        elif 长度==127:#八字节长度
            长度=int.from_bytes(自身._读确切(8),'big')#长度
        if 长度>自身._最大载荷:#超过 maxPayload
            raise ValueError('too-big')#不把巨大载荷读进来
        if not 有掩码:#客户端帧必须有掩码
            raise ValueError('unmasked')#协议错误
        if 操作码 in (8,9,10) and not 终帧:#控制帧不能分片
            raise ValueError('fragmented-control')#协议错误
        掩码=自身._读确切(4)#掩码
        载荷=自身._读确切(长度) if 长度 else b''#载荷
        解开=bytes(载荷[下标]^掩码[下标%4] for 下标 in range(len(载荷)))#逐字节
        return 终帧,操作码,解开#一帧

    def _读循环(自身):
        '读到关闭或出错。ping 回 pong'
        缓冲=b''#分片
        操作=None#数据操作码
        try:#读
            while 自身.readyState==1:#还开着
                终帧,码,载荷=自身._读一帧()#一帧
                if 码==8:#关闭
                    自身.close(1000,'')#回关闭帧并拆
                    return#停
                if 码==9:#ping
                    if 自身.readyState==1:#还开着
                        with 自身._写锁:#串行
                            自身.原始.sendall(编码网页套接字帧(10,载荷))#pong
                    continue#下一帧
                if 码==10:#pong
                    自身._发出('pong')#活动
                    continue#下一帧
                if 码 in (1,2):#新的数据消息
                    操作=码#记下
                    缓冲=载荷#起
                elif 码==0:#续片
                    缓冲+=载荷#拼
                else:#不认识
                    continue#丢
                if len(缓冲)>自身._最大载荷:#拼起来超限
                    自身.close(1009,'Message Too Big')#1009
                    return#停
                if 终帧 and 操作 is not None:#消息齐了
                    if 操作==1:#文本
                        自身._发出('message',缓冲.decode('utf-8'))#文本
                    else:#二进制
                        自身._发出('message',缓冲)#字节
                    缓冲=b''#清空
                    操作=None#清空
        except ValueError as 错误:#帧不合法
            文本=str(错误)#哪一种
            if 自身.readyState==1 and 文本=='too-big':#单帧超限
                自身.close(1009,'Message Too Big')#1009
            elif 自身.readyState==1:#掩码或控制帧
                自身.close(1002,'protocol error')#1002
        except Exception:#读失败
            if 自身.readyState==1:#还以为开着
                自身._发出('error')#出错
                自身.terminate()#拆


class 检查器端点:#检查器端点
    'Worker 拥有的网络端点'
    def __init__(自身,配置,源注册表,网络,realms,cordisDom,cordis树,查询路由):#构造
        '保存依赖'
        自身._配置=配置#配置
        自身._源注册表=源注册表#源注册表
        自身._网络=网络#网络域
        自身._realms=realms#realm注册表
        自身._cordisDom=cordisDom#Cordis DOM
        自身._cordis树=cordis树#Cordis树读取
        自身._查询路由=查询路由#查询路由
        自身._服务器=None#HTTP服务器
        自身._cdp会话={}#CDP会话表
        自身._摄入连接={}#摄入连接表

    def 启动(自身):#启动
        '绑定回环端点'
        候选=_配置字段(自身._配置,'startPort')#候选端口
        主机=_配置字段(自身._配置,'host')#主机
        while True:#找可用端口
            try:#尝试监听
                服务器=_创建服务器(自身,候选,主机)#创建服务器
                自身._服务器=服务器#保存
                线程=threading.Thread(target=服务器.serve_forever,daemon=True)#服务线程
                线程.start()#启动
                return {'host':主机,'port':服务器.server_address[1],'targetId':_配置字段(自身._配置,'targetId')}#返回信息
            except OSError as 错误:#监听失败
                自身._服务器=None#清空
                if not 地址占用(错误) or 候选==0:#非占用或随机端口
                    raise#抛
                if 候选==65535:#端口耗尽
                    raise 检查器错误(f'inspector: no available port from {_配置字段(自身._配置,"startPort")} through 65535') from 错误#无可用端口
                候选+=1#下一端口

    def 关闭(自身):#关闭
        '停止准入、释放 CDP 会话、终止套接字并等待服务器关闭'
        服务器=自身._要求服务器()#要求已启动
        for 套接字,会话 in list(自身._cdp会话.items()):#扫CDP
            自身._cdp会话.pop(套接字,None)#先摘，关闭事件里不再关第二次
            会话.关闭()#关会话
            套接字.terminate()#拆套接字
        自身._cdp会话.clear()#清空
        for 套接字,连接 in list(自身._摄入连接.items()):#扫摄入
            自身._摄入连接.pop(套接字,None)#先摘
            自身._源注册表.断开(连接,'Client ingest endpoint stopped')#断开源
            套接字.terminate()#拆套接字
        自身._摄入连接.clear()#清空
        服务器.shutdown()#关HTTP
        服务器.server_close()#关套接字
        自身._服务器=None#清空

    def _处理http(自身,处理器):#处理HTTP
        '处理发现端点'
        路径=解析网址(处理器.path).path#路径
        if 路径 in ('/json','/json/list'):#列表
            自身._写json(处理器,[自身._目标()])#返回目标
            return#返回
        if 路径=='/json/version':#版本
            自身._写json(处理器,{'Browser':'dsh-experimental-inspector/0','Protocol-Version':'1.3','webSocketDebuggerUrl':自身._cdp网址()})#版本对象
            return#返回
        处理器.send_response(404)#404
        处理器.send_header('content-type','text/plain; charset=utf-8')#类型
        处理器.end_headers()#头结束
        处理器.wfile.write(b'not found')#结束

    def _处理升级(自身,路径,请求头,套接字,读流):#处理升级
        '升级路径。Client 选择在 101 之前校验。返回真表示套接字已交给 WebSocket'
        try:#解析升级网址
            网址=解析网址(路径)#含查询
        except ValueError:#坏网址
            try:#拆掉
                套接字.close()#关
            except OSError:#已经关了
                pass#忽略
            return False#未占有
        路径名=网址.path#路径
        目标id=_配置字段(自身._配置,'targetId')#目标id
        最大载荷=_配置字段(自身._配置,'maxSourceFrameBytes')#帧上限
        if 路径名==f'/devtools/page/{目标id}':#CDP路径
            try:#读选择
                选中=读检查器客户端选择(网址)#可选 Client
            except Exception:#重复或非法标识
                套接字.sendall(b'HTTP/1.1 400 Bad Request\r\nConnection: close\r\nContent-Length: 0\r\n\r\n')#400
                try:#关掉
                    套接字.close()#关
                except OSError:#已经关了
                    pass#忽略
                return False#不打开未过滤连接
            网页套接字=检查器套接字(套接字,读流,最大载荷)#升级对象
            if not 网页套接字.握手(请求头):#101 没写成
                return False#未占有
            try:#挂上 CDP
                自身._接受cdp(网页套接字,选中)#接受
            except Exception:#会话装配失败
                网页套接字.terminate()#拆
                raise#继续抛
            return True#已占有
        if 路径名=='/ingest':#摄入路径
            if not 自身._已授权客户端(请求头):#未授权
                套接字.sendall(b'HTTP/1.1 403 Forbidden\r\nConnection: close\r\nContent-Length: 0\r\n\r\n')#403
                try:#关掉
                    套接字.close()#关
                except OSError:#已经关了
                    pass#忽略
                return False#未占有
            网页套接字=检查器套接字(套接字,读流,最大载荷)#升级对象
            if not 网页套接字.握手(请求头):#101 没写成
                return False#未占有
            try:#挂上摄入
                自身._接受摄入(网页套接字)#接受
            except Exception:#装配失败
                网页套接字.terminate()#拆
                raise#继续抛
            return True#已占有
        try:#未知路径
            套接字.close()#拆掉
        except OSError:#已经关了
            pass#忽略
        return False#未占有

    def _接受cdp(自身,套接字,客户端源标识=None):#接受CDP
        '101 之后把文本帧交给 CDP 会话'
        class _传输:#CDP传输
            def 发送(传,载荷):#发送
                '已开才送一条文本帧'
                if 套接字.readyState!=1:#未开
                    return#不写
                套接字.send(紧凑json编码(载荷))#文本帧
            def 关闭(传):#关闭
                '非法 CDP 请求'
                套接字.close(1008,'invalid CDP request')#1008
        会话=Cdp会话(_传输(),{'targetId':_配置字段(自身._配置,'targetId'),'title':'DeepSeek Harness Host'},自身._源注册表,自身._网络,自身._realms,自身._cordisDom,自身._cordis树,客户端源标识)#CDP会话
        自身._cdp会话[套接字]=会话#登记
        def 收消息(文本):#消息
            '解析并交给会话'
            if not isinstance(文本,str):#只要文本
                套接字.close(1008,'CDP frame must be JSON')#非文本
                return#停
            try:#解析
                会话.接收(json.loads(文本))#交给会话
            except (json.JSONDecodeError,ValueError,检查器错误):#畸形帧或会话拒绝
                套接字.close(1008,'CDP frame must be JSON')#关闭
        def 收关闭():#关闭
            '还在表里才关会话'
            已有=自身._cdp会话.pop(套接字,None)#摘
            if 已有 is not None:#这一次负责关
                已有.关闭()#关会话
        def 忽略错误(*参数):#错误
            '关闭事件负责连接自己的清理'
            return#不在这里拆
        套接字.on('message',收消息)#消息
        套接字.once('close',收关闭)#关闭
        套接字.on('error',忽略错误)#错误交给 close
        套接字.开始读()#开始读

    def _接受摄入(自身,套接字):#接受摄入
        '101 之后把文本帧交给查询路由和源注册表'
        class _查询传输:#查询传输
            def __init__(传):#构造
                '占位'
                pass#无状态
            def send(传,帧):#发送
                '已开才送查询帧'
                if 套接字.readyState!=1:#未开
                    return#不写
                套接字.send(紧凑json编码(帧))#文本帧
            def close(传,码=1000,原因=''):#关闭
                '关闭套接字'
                套接字.close(码,原因)#关闭帧
        查询对端=自身._查询路由.打开(_查询传输())#查询对端
        def 发送(帧):#发送
            '发往 Client'
            if 套接字.readyState!=1:#未开
                return#不写
            套接字.send(紧凑json编码(帧))#文本帧
            if 帧.get('t')=='source/accepted':#接受后登记
                查询对端.接受(帧['sourceId'],帧['generation'])#登记
        def 关闭(码=1000,原因=''):#关闭
            '关闭截断原因'
            套接字.close(码,原因)#原因在套接字里截到 123 字节
        连接={'kind':'client','send':发送,'close':关闭}#源连接
        自身._摄入连接[套接字]=连接#登记
        def 收消息(文本):#消息
            '查询未吃则交源'
            if not isinstance(文本,str):#只要文本
                连接['close'](1008,'source frame must be JSON')#非文本
                return#停
            try:#解析
                值=json.loads(文本)#解码
                if not 查询对端.接收(值):#查询未吃
                    自身._源注册表.接收(连接,值)#交源
            except (json.JSONDecodeError,ValueError,检查器错误):#畸形帧或会话拒绝
                连接['close'](1008,'source frame must be JSON')#关闭
        def 收关闭():#关闭
            '还在表里才断源'
            已有=自身._摄入连接.pop(套接字,None)#摘
            if 已有 is None:#端点关闭已经断过
                return#停
            查询对端.关闭()#关查询
            自身._源注册表.断开(已有,'Client source disconnected')#断源
        def 忽略错误(*参数):#错误
            '关闭事件负责连接自己的清理'
            return#不在这里拆
        套接字.on('message',收消息)#消息
        套接字.once('close',收关闭)#关闭
        套接字.on('error',忽略错误)#错误交给 close
        套接字.开始读()#开始读

    def _已授权客户端(自身,请求头):#Client是否授权
        '校验子协议与 Origin'
        协议头=请求头.get('Sec-WebSocket-Protocol') or ''#子协议
        协议列表=[项.strip() for 项 in 协议头.split(',')]#分割
        if _配置字段(自身._配置,'clientToken') not in 协议列表:#无令牌
            return False#拒绝
        if 请求头.get('Origin') is None:#无Origin放行
            return True#放行
        来源=请求头.get('Origin')#Origin
        允许=_配置字段(自身._配置,'clientOrigins')#白名单
        if 来源 in 允许:#白名单
            return True#放行
        try:#解析hostname
            主机名=解析网址(来源).hostname#主机名
            return 主机名 in ('localhost','127.0.0.1','[::1]','::1')#本机
        except ValueError:#Origin 非法
            return False#拒绝

    def _目标(自身):#目标描述
        '目标对象'
        主机=_配置字段(自身._配置,'host')#主机
        目标id=_配置字段(自身._配置,'targetId')#id
        端口=自身._已绑定端口()#端口
        return {#目标对象
            'id':目标id,#id
            'type':'page',#类型
            'title':'DeepSeek Harness Host',#标题
            'description':'Experimental cross-realm Inspector target',#描述
            'url':'dsh://host',#URL
            'webSocketDebuggerUrl':自身._cdp网址(),#CDP URL
            'devtoolsFrontendUrl':f'devtools://devtools/bundled/devtools_app.html?ws={主机}:{端口}/devtools/page/{目标id}&panel=elements&noJavaScriptCompletion=true',#前端URL
        }#return结束

    def _cdp网址(自身):#CDP WebSocket URL
        '拼 CDP URL'
        return f"ws://{_配置字段(自身._配置,'host')}:{自身._已绑定端口()}/devtools/page/{_配置字段(自身._配置,'targetId')}"#拼URL

    def _已绑定端口(自身):#已绑定端口
        '已绑定端口'
        return 自身._要求服务器().server_address[1]#端口

    def _要求服务器(自身):#要求已启动
        '要求已启动'
        if 自身._服务器 is None:#未启动
            raise 检查器错误('inspector: endpoint is not started')#未启动
        return 自身._服务器#返回

    def _写json(自身,处理器,值):#写JSON响应
        '写 JSON 响应'
        体=紧凑json编码(值).encode('utf-8')#体
        处理器.send_response(200)#头
        处理器.send_header('content-type','application/json; charset=utf-8')#类型
        处理器.send_header('content-length',str(len(体)))#长度
        处理器.end_headers()#头结束
        处理器.wfile.write(体)#体

def _配置字段(配置,名):#读配置字段
    '配置是 dict'
    return 配置[名]#字段

def _创建服务器(端点,端口,主机):#创建HTTP服务器
    '创建线程化 HTTP 服务器。Upgrade 走端点升级，成功后不再由 HTTP 服务器关套接字'
    class _服务器(ThreadingHTTPServer):#可留下已升级的套接字
        def shutdown_request(自身,请求):#请求线程结束
            '升级占有的套接字留给 WebSocket 读线程'
            if getattr(请求,'_检查器升级占有',False):#已经 101
                return#不关
            ThreadingHTTPServer.shutdown_request(自身,请求)#普通请求照关

    class _处理器(BaseHTTPRequestHandler):#请求处理器
        def handle_one_request(自身):#一条请求
            '普通请求走发现端点。Upgrade: websocket 在回 101 之前跑升级'
            try:#读一条请求
                自身.raw_requestline=自身.rfile.readline(65537)#请求行
                if len(自身.raw_requestline)>65536:#过长
                    自身.requestline=''#空
                    自身.request_version=''#空
                    自身.command=''#空
                    自身.send_error(414)#URI 过长
                    return#停
                if not 自身.raw_requestline:#对端关掉
                    自身.close_connection=True#结束
                    return#停
                if not 自身.parse_request():#头不合法，parse 自己回了响应
                    return#停
                升级=自身.headers.get('Upgrade')#升级头
                if isinstance(升级,str) and 'websocket' in 升级.lower():#WebSocket
                    占有=端点._处理升级(自身.path,自身.headers,自身.connection,自身.rfile)#校验并 101
                    if 占有:#读线程还要用这条套接字
                        自身.connection._检查器升级占有=True#服务器别关
                    自身.close_connection=True#这条连接不再当 HTTP
                    return#停
                端点._处理http(自身)#发现端点
            except (TimeoutError,socket.timeout):#读超时
                自身.close_connection=True#结束

        def finish(自身):#处理结束
            '升级占有时不关读缓冲，读线程还在用'
            if getattr(自身.connection,'_检查器升级占有',False):#已升级
                return#留下
            BaseHTTPRequestHandler.finish(自身)#普通请求

        def log_message(自身,*位置参数):#禁用默认日志
            '静默'
            return#静默
    服务器=_服务器((主机,端口),_处理器)#HTTP
    服务器.端点=端点#挂回
    return 服务器#返回

def 地址占用(错误):#是否地址占用
    '是否 EADDRINUSE'
    return isinstance(错误,OSError) and getattr(错误,'errno',None) in (getattr(socket,'EADDRINUSE',98),10048)#EADDRINUSE
