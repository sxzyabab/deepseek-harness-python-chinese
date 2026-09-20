import threading
from ...未实现失败 import 运行时错误

__all__=[
    'requestListener','whenRequestListener','ServerResponse','createServer','request','get',
    'STATUS_CODES','Server','__esModule','default',
]

虚拟端口=3080
_已捕获=None
_就绪=threading.Event()

def 请求监听器():
    """webserver 的请求监听器，一旦 `[Service.init]` 安装完毕。"""
    return _已捕获

def 当请求监听器():
    """阻塞到请求监听器已捕获。"""
    if _已捕获 is not None:
        return _已捕获
    _就绪.wait()
    return _已捕获

class 假服务器:
    """假 Server：事件注册被存储且从不发射。"""

    def __init__(自身):
        """空监听表。"""
        自身._监听表={}

    def 监听(自身,事件,监听器):
        """注册事件监听器（`upgrade`、`error`）；从不发射。"""
        if 事件 not in 自身._监听表:
            自身._监听表[事件]=set()
        自身._监听表[事件].add(监听器)
        return 自身

    def 一次(自身,事件,监听器):
        """on 的一次性注册对应物。"""
        return 自身.监听(事件,监听器)

    def 取消监听(自身,事件,监听器):
        """移除监听器。"""
        if 事件 in 自身._监听表:
            自身._监听表[事件].discard(监听器)
        return 自身

    def 听端口(自身,*参数):
        """绑定：立即成功。回调必须运行。"""
        回调=参数[-1] if len(参数)>0 else None
        if callable(回调):
            if 'queueMicrotask' in globals() and callable(globals()['queueMicrotask']):
                globals()['queueMicrotask'](回调)
            else:
                回调()
        return 自身

    def 地址(自身):
        """隧道合成的回环权威。"""
        return {'address':'127.0.0.1','family':'IPv4','port':虚拟端口}

    def 关闭(自身,回调=None):
        """关闭：无套接字可释放。"""
        if 回调 is not None:
            if 'queueMicrotask' in globals() and callable(globals()['queueMicrotask']):
                globals()['queueMicrotask'](回调)
            else:
                回调()
        return 自身

    def 关闭全部连接(自身):
        """从未接受过连接。"""
        pass

    def 关闭空闲连接(自身):
        """也不存在空闲连接。"""
        pass

    on=监听
    once=一次
    off=取消监听
    listen=听端口
    address=地址
    close=关闭
    closeAllConnections=关闭全部连接
    closeIdleConnections=关闭空闲连接

class 服务器响应:
    """中间件特性检测时读取的构造器标记。"""
    pass

def 创建服务器(监听器=None):
    """创建假服务器并为其保留请求监听器供隧道使用。"""
    global _已捕获
    if 监听器 is not None:
        _已捕获=监听器
        _就绪.set()
    return 假服务器()

def 请求(*位置参数,**关键字参数):
    """出站 HTTP 在 worker 中只有一个载体：`fetch`。"""
    raise 运行时错误('web-preview: worker 宿主里没有 node:http.request，请用 fetch')

def 获取(*位置参数,**关键字参数):
    """同 request。"""
    raise 运行时错误('web-preview: worker 宿主里没有 node:http.get，请用 fetch')

状态码表={
    200:'OK',204:'No Content',304:'Not Modified',400:'Bad Request',
    403:'Forbidden',404:'Not Found',405:'Method Not Allowed',413:'Payload Too Large',
    415:'Unsupported Media Type',426:'Upgrade Required',500:'Internal Server Error',503:'Service Unavailable',
}

requestListener=请求监听器
whenRequestListener=当请求监听器
ServerResponse=服务器响应
createServer=创建服务器
request=请求
get=获取
STATUS_CODES=状态码表
Server=假服务器
__esModule=True
default={'createServer':创建服务器,'request':请求,'get':获取,'STATUS_CODES':状态码表,'Server':假服务器,'ServerResponse':服务器响应}
