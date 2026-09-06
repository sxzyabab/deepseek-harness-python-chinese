"""宿主与客户端 Connection 两半边共用的一元 RPC 约定。

对齐上游 `connection/src/rpc.ts`。公开面仅中文名。本模块只承载权威常量与文档形约定；实现住在宿主连接服务。
"""

__all__=['连接错误','连接权威_受信任宿主','连接权威_回环','已中止','若已中止则抛出']#仅中文公开名

class 连接错误(Exception):#本包失败
    """连接包内的本地失败。"""

连接权威_受信任宿主='trusted-host'#受信任 Host
连接权威_回环='loopback'#仅回环

def 已中止(信号):#读 threading.Event
    """无信号视为未中止；已置位则已中止。"""
    if 信号 is None:#无
        return False#未中止
    return 信号.is_set()#置位即中止

def 若已中止则抛出(信号):#已取消则抛
    """已中止则抛连接错误。"""
    if 已中止(信号):#已取消
        raise 连接错误('aborted')#中止
