from ..未实现失败 import 未实现失败,运行时错误

__all__=['WebSocket','WebSocketServer','Server','__esModule','default']

模块='ws'
__esModule=True

class WebSocket:
    """客户端套接字（不可用；页面侧用隧道而非 WebSocket）。"""
    CONNECTING=0
    OPEN=1
    CLOSING=2
    CLOSED=3

    def __init__(自身):
        """构造即抛不可用。"""
        raise 运行时错误(f'web-preview: {模块} client sockets are not available in the worker host')

class WebSocketServer:
    """构造必须成功、方法不可达的服务器。"""

    def __init__(自身):
        """空客户端集与桩方法。"""
        自身.clients=set()
        自身.handleUpgrade=未实现失败(模块,'WebSocketServer.handleUpgrade')
        自身.emit=未实现失败(模块,'WebSocketServer.emit')

    def on(自身,*位置参数,**关键字参数):
        """注册监听器；从不发出任何事件。"""
        return 自身

    def close(自身,callback=None):
        """关闭服务器；完成回调立即调用。"""
        if callback is not None: callback()

Server=WebSocketServer
default=WebSocket
