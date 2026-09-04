"""Worker 拥有的 HTTP 发现、DevTools CDP 与 Client 摄入端点。

对齐上游 `worker/bridge/endpoint.ts`。公开面仅中文名。
"""
import json,socket,threading#HTTP与套接字
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer#HTTP服务
from urllib.parse import urlparse as 解析网址#路径解析
from ..cdp.会话 import Cdp会话#CDP会话

__all__=['检查器端点']#仅中文公开名

class 检查器端点:#检查器端点
    """Worker 拥有的网络端点。"""
    def __init__(自身,配置,源们,网络,realms,cordisDom,cordis树,查询们):#构造
        """保存依赖。"""
        自身._配置=配置#配置
        自身._源们=源们#源注册表
        自身._网络=网络#网络域
        自身._realms=realms#realm注册表
        自身._cordisDom=cordisDom#Cordis DOM
        自身._cordis树=cordis树#Cordis树读取
        自身._查询们=查询们#查询路由
        自身._服务器=None#HTTP服务器
        自身._cdp会话={}#CDP会话表
        自身._摄入连接={}#摄入连接表
        自身._升级处理器={}#升级路径→处理器

    def 启动(自身):#启动
        """绑定回环端点。"""
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
                    raise Exception(f'inspector: no available port from {_配置字段(自身._配置,"startPort")} through 65535') from 错误#无可用端口
                候选+=1#下一端口

    def 关闭(自身):#关闭
        """停止准入、释放 CDP 会话、终止套接字并等待服务器关闭。"""
        服务器=自身._要求服务器()#要求已启动
        for 套接字,会话 in list(自身._cdp会话.items()):#扫CDP
            会话.关闭()#关会话
            try:#终止
                套接字.close()#关套接字
            except Exception:#忽略
                pass#忽略
        自身._cdp会话.clear()#清空
        for 套接字,连接 in list(自身._摄入连接.items()):#扫摄入
            自身._源们.断开(连接,'Client ingest endpoint stopped')#断开源
            try:#终止
                套接字.close()#关套接字
            except Exception:#忽略
                pass#忽略
        自身._摄入连接.clear()#清空
        服务器.shutdown()#关HTTP
        服务器.server_close()#关套接字
        自身._服务器=None#清空

    def _处理http(自身,处理器):#处理HTTP
        """处理发现端点。"""
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

    def _处理升级(自身,路径,请求头,套接字):#处理升级
        """处理 WebSocket 升级路径登记。"""
        目标id=_配置字段(自身._配置,'targetId')#目标id
        if 路径==f'/devtools/page/{目标id}':#CDP路径
            自身._接受cdp(套接字,请求头)#接受CDP
            return True#已处理
        if 路径=='/ingest':#摄入路径
            if not 自身._已授权客户端(请求头):#未授权
                套接字.sendall(b'HTTP/1.1 403 Forbidden\r\nConnection: close\r\nContent-Length: 0\r\n\r\n')#403
                套接字.close()#关闭
                return True#已处理
            自身._接受摄入(套接字,请求头)#接受摄入
            return True#已处理
        return False#未知路径

    def _接受cdp(自身,套接字,请求头):#接受CDP
        """接受 CDP WebSocket（由外部升级层投递已握手套接字）。"""
        class _传输:#CDP传输
            def 发送(传,载荷):#发送
                """发送 JSON 载荷。"""
                数据=json.dumps(载荷,ensure_ascii=False).encode('utf-8')#编码
                try:#发送
                    套接字.sendall(数据)#发
                except Exception:#忽略
                    pass#忽略
            def 关闭(传):#关闭
                """关闭套接字。"""
                try:#关
                    套接字.close()#关
                except Exception:#忽略
                    pass#忽略
        会话=Cdp会话(_传输(),{'targetId':_配置字段(自身._配置,'targetId'),'title':'DeepSeek Harness Host'},自身._源们,自身._网络,自身._realms,自身._cordisDom,自身._cordis树)#CDP会话
        自身._cdp会话[套接字]=会话#登记
        def 收消息(文本):#消息
            """解析并交给会话。"""
            try:#解析
                会话.接收(json.loads(文本))#交给会话
            except Exception:#非JSON
                套接字.close()#关闭
        自身._升级处理器[套接字]={'onmessage':收消息,'onsession':会话,'kind':'cdp'}#登记处理器

    def _接受摄入(自身,套接字,请求头):#接受摄入
        """接受 Client 摄入 WebSocket。"""
        class _查询传输:#查询传输
            def __init__(传):#构造
                """占位。"""
                pass#无状态
            def send(传,帧):#发送
                """发送查询帧。"""
                try:#发送
                    套接字.sendall(json.dumps(帧,ensure_ascii=False).encode('utf-8'))#发
                except Exception:#忽略
                    pass#忽略
            def close(传,码=1000,原因=''):#关闭
                """关闭套接字。"""
                try:#关
                    套接字.close()#关
                except Exception:#忽略
                    pass#忽略
        查询对端=自身._查询们.打开(_查询传输())#查询对端
        def 发送(帧):#发送
            """发往 Client。"""
            try:#发送
                套接字.sendall(json.dumps(帧,ensure_ascii=False).encode('utf-8'))#发
            except Exception:#忽略
                return#未开
            if 帧.get('t')=='source/accepted':#接受后登记
                查询对端.接受(帧['sourceId'],帧['generation'])#登记
        def 关闭(码=1000,原因=''):#关闭
            """关闭截断原因。"""
            try:#关
                套接字.close()#关
            except Exception:#忽略
                pass#忽略
        连接={'kind':'client','send':发送,'close':关闭}#源连接
        自身._摄入连接[套接字]=连接#登记
        def 收消息(文本):#消息
            """查询未吃则交源。"""
            try:#解析
                值=json.loads(文本)#解码
                if not 查询对端.接收(值):#查询未吃
                    自身._源们.接收(连接,值)#交源
            except Exception:#非JSON
                连接['close'](1008,'source frame must be JSON')#关闭
        def 收关闭():#关闭
            """清理。"""
            自身._摄入连接.pop(套接字,None)#移除
            查询对端.关闭()#关查询
            自身._源们.断开(连接,'Client source disconnected')#断源
        自身._升级处理器[套接字]={'onmessage':收消息,'onclose':收关闭,'kind':'ingest'}#登记

    def _已授权客户端(自身,请求头):#Client是否授权
        """校验子协议与 Origin。"""
        协议头=请求头.get('Sec-WebSocket-Protocol') or 请求头.get('sec-websocket-protocol') or ''#子协议头
        协议们=[项.strip() for 项 in 协议头.split(',')]#分割
        if _配置字段(自身._配置,'clientToken') not in 协议们:#无令牌
            return False#拒绝
        来源=请求头.get('Origin') or 请求头.get('origin')#Origin
        if 来源 is None:#无Origin放行
            return True#放行
        允许=_配置字段(自身._配置,'clientOrigins')#白名单
        if 来源 in 允许:#白名单
            return True#放行
        try:#解析hostname
            主机名=解析网址(来源).hostname#主机名
            return 主机名 in ('localhost','127.0.0.1','[::1]','::1')#本机
        except Exception:#解析失败
            return False#拒绝

    def _目标(自身):#目标描述
        """目标对象。"""
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
        """拼 CDP URL。"""
        return f"ws://{_配置字段(自身._配置,'host')}:{自身._已绑定端口()}/devtools/page/{_配置字段(自身._配置,'targetId')}"#拼URL

    def _已绑定端口(自身):#已绑定端口
        """已绑定端口。"""
        return 自身._要求服务器().server_address[1]#端口

    def _要求服务器(自身):#要求已启动
        """要求已启动。"""
        if 自身._服务器 is None:#未启动
            raise Exception('inspector: endpoint is not started')#未启动
        return 自身._服务器#返回

    def _写json(自身,处理器,值):#写JSON响应
        """写 JSON 响应。"""
        体=json.dumps(值,ensure_ascii=False).encode('utf-8')#体
        处理器.send_response(200)#头
        处理器.send_header('content-type','application/json; charset=utf-8')#类型
        处理器.send_header('content-length',str(len(体)))#长度
        处理器.end_headers()#头结束
        处理器.wfile.write(体)#体

def _配置字段(配置,名):#读配置字段
    """支持映射或属性配置。"""
    return 配置[名] if isinstance(配置,dict) else getattr(配置,名)#字段

def _创建服务器(端点,端口,主机):#创建HTTP服务器
    """创建线程化 HTTP 服务器。"""
    class _处理器(BaseHTTPRequestHandler):#请求处理器
        def do_GET(自身):#GET
            """发现端点。"""
            端点._处理http(自身)#委托
        def log_message(自身,*位置参数):#禁用默认日志
            """静默。"""
            return#静默
    服务器=ThreadingHTTPServer((主机,端口),_处理器)#HTTP
    服务器.端点=端点#挂回
    return 服务器#返回

def 地址占用(错误):#是否地址占用
    """是否 EADDRINUSE。"""
    return isinstance(错误,OSError) and getattr(错误,'errno',None) in (getattr(socket,'EADDRINUSE',98),10048)#EADDRINUSE
