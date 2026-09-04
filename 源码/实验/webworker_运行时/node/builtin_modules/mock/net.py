"""Worker 用的 `node:net`。此处无任何东西接受或拨出套接字：假 HTTP
服务器从不发出 `upgrade`，因此只有地址谓词与可构造但大声的 Socket 可达。

对齐上游 `webworker-runtime/src/node/builtin_modules/mock/net.ts`。
"""
import re#字面量模式

__all__=['Socket','isIPv4','isIPv6','isIP','createServer','connect','__esModule','default']#Node面

IPV4=re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')#IPv4字面量模式
IPV6=re.compile(r'^[0-9a-f:]+$',re.I)#IPv6字面量模式

class Socket:#套接字占位类
    """可构造占位：WebSocket 升级路径在 Worker 中从不运行。"""

    def write(自身,*位置参数,**关键字参数):#写入拒绝
        """从不向套接字写入；到达此处意味着升级路径已激活。"""
        raise Exception('web-preview: node:net Socket.write is not available in the worker host')#抛不可用

    def end(自身,*位置参数,**关键字参数):#结束拒绝
        """write 的对应物。"""
        raise Exception('web-preview: node:net Socket.end is not available in the worker host')#抛不可用

    def destroy(自身):#安静拆除
        """接受拆除，使处置路径保持安静。"""
        pass#从未持有任何资源

def isIPv4(value):#判定IPv4字面量
    """字符串是否为 IPv4 字面量。"""
    if not IPV4.match(value): return False#模式不符
    return all(int(段)<=255 for 段 in value.split('.'))#各段≤255

def isIPv6(value):#判定IPv6字面量
    """字符串是否为 IPv6 字面量。"""
    return ':' in value and IPV6.match(value) is not None#含冒号且匹配模式

def isIP(value):#返回IP族
    """字面量的 IP 族：4、6，或非 IP 字面量时为 0。"""
    if isIPv4(value): return 4#IPv4
    if isIPv6(value): return 6#IPv6
    return 0#非IP

def createServer(*位置参数,**关键字参数):#创建服务器拒绝
    """TCP 监听是假 HTTP 服务器的事；裸 net 服务器不可达。"""
    raise Exception('web-preview: node:net.createServer is not available in the worker host')#抛不可用

def connect(*位置参数,**关键字参数):#出站连接拒绝
    """出站连接在 Worker 中无载体。"""
    raise Exception('web-preview: node:net.connect is not available in the worker host')#抛不可用

__esModule=True#CJS互操作标记
default={'Socket':Socket,'isIP':isIP,'isIPv4':isIPv4,'isIPv6':isIPv6,'createServer':createServer,'connect':connect}#默认导出
