from ...未实现失败 import 运行时错误
import re

__all__=['Socket','isIPv4','isIPv6','isIP','createServer','connect','__esModule','default']

IPV4=re.compile(r'^([0-9]{1,3}\.){3}[0-9]{1,3}\Z')
IPV6=re.compile(r'^[0-9a-f:]+\Z',re.I)

class Socket:
    """可构造占位：WebSocket 升级路径在 Worker 中从不运行。"""

    def write(自身,*位置参数,**关键字参数):
        """从不向套接字写入；到达此处意味着升级路径已激活。"""
        raise 运行时错误('web-preview: worker 宿主里没有 node:net Socket.write')

    def end(自身,*位置参数,**关键字参数):
        """write 的对应物。"""
        raise 运行时错误('web-preview: worker 宿主里没有 node:net Socket.end')

    def destroy(自身):
        """接受拆除，使拆除路径保持安静。"""
        pass

def isIPv4(value):
    """字符串是否为 IPv4 字面量。"""
    if not IPV4.match(value): return False
    return all(int(段)<=255 for 段 in value.split('.'))

def isIPv6(value):
    """字符串是否为 IPv6 字面量。"""
    return ':' in value and IPV6.match(value) is not None

def isIP(value):
    """字面量的 IP 族：4、6，或非 IP 字面量时为 0。"""
    if isIPv4(value): return 4
    if isIPv6(value): return 6
    return 0

def createServer(*位置参数,**关键字参数):
    """TCP 监听是假 HTTP 服务器的事；裸 net 服务器不可达。"""
    raise 运行时错误('web-preview: worker 宿主里没有 node:net.createServer')

def connect(*位置参数,**关键字参数):
    """出站连接在 Worker 中无载体。"""
    raise 运行时错误('web-preview: worker 宿主里没有 node:net.connect')

__esModule=True
default={'Socket':Socket,'isIP':isIP,'isIPv4':isIPv4,'isIPv6':isIPv6,'createServer':createServer,'connect':connect}
