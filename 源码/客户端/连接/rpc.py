__all__=['连接错误','连接权威_受信任宿主','连接权威_回环','已中止','若已中止则抛出','Rpc标识','传输错误']#仅中文公开名

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
        raise 连接错误('已中止')#中止

def Rpc标识(标识):
    """把已校验字符串收成连接关联 id。"""
    return 标识#标识构造

def 传输错误(错误):#传输失败收成结果
    """把被拒绝的传输操作收成通用失败结果。"""
    return {'ok':False,'error':{'code':'gateway/internal','message':str(错误),'details':{}}}#内部失败
