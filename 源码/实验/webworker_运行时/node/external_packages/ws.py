"""`ws` 桩。`WebSocketDownlinks` 在 Connection 一出现就在字段初始化器里
构造 `WebSocketServer`，因此类必须可构造；
假 HTTP 服务器从不发出 `upgrade`，故任何方法都到不了
（隧道改经 SSE 分支承载下行事件）。

对齐上游 `webworker-runtime/src/node/external_packages/ws.ts`。
"""
from ..未实现失败 import 未实现失败#未实现桩

__all__=['WebSocket','WebSocketServer','Server','__esModule','default']#Node面

模块='ws'#模块名
__esModule=True#CJS互操作

class WebSocket:#客户端套接字类
    """客户端套接字（不可用；页面侧用隧道而非 WebSocket）。"""
    CONNECTING=0#连接中
    OPEN=1#已打开
    CLOSING=2#关闭中
    CLOSED=3#已关闭

    def __init__(自身):#构造即拒
        """构造即抛不可用。"""
        raise Exception(f'web-preview: {模块} client sockets are not available in the worker host')#不可用

class WebSocketServer:#服务器类
    """构造必须成功、方法不可达的服务器。"""

    def __init__(自身):#构造
        """空客户端集与桩方法。"""
        自身.clients=set()#空客户端集
        自身.handleUpgrade=未实现失败(模块,'WebSocketServer.handleUpgrade')#升级桩
        自身.emit=未实现失败(模块,'WebSocketServer.emit')#emit桩

    def on(自身,*位置参数,**关键字参数):#注册监听器
        """注册监听器；从不发出任何事件。"""
        return 自身#链式自身

    def close(自身,callback=None):#关闭
        """关闭服务器；完成回调立即调用。"""
        if callback is not None: callback()#立即回调

Server=WebSocketServer#Server别名
default=WebSocket#默认导出客户端类
