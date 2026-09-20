from urllib.parse import urlparse as 解析URL
from .回环主机名 import 是否回环主机名#回环主机名判定
from .rpc import 连接错误#本包异常

__all__=['断言受信任权威','是否受信任接口请求']#仅中文公开名

def 取头(请求头表,名):#读单个头
    """从 dict 头映射读单个头；不要数组。"""
    if 请求头表 is None:#无头
        return None#缺席
    if 名 in 请求头表:#原名
        值=请求头表[名]#值
        if isinstance(值,str):#单字符串
            return 值#只要单字符串
    小写=名.lower()#Node 头常小写
    if 小写 in 请求头表:#小写名
        值=请求头表[小写]#值
        if isinstance(值,str):#单字符串
            return 值#返回
    return None#不要数组

def 解析权威(权威):#权威字符串 → 解析结果
    """Host 头权威的归一化；无法解析则为 None。"""
    解析=解析URL('http://'+权威)
    if not 解析.hostname:#无主机名
        return None#不当权威
    return 解析#解析结果

def 规范权威(条目,解析):#权威 → 规范 host 或 host:port
    """已解析权威的规范形态：没写端口时是 hostname，否则 hostname:port。"""
    端口=解析.port#显式或默认
    if 解析.port is None:#http 默认 80 时改用 https 看是否写了 443
        端口=解析URL('https://'+条目).port
    if 端口 is None:#无显式端口
        return 解析.hostname.lower() if 解析.hostname else ''#只有 hostname
    return (解析.hostname or '').lower()+':'+str(端口)#hostname:port

def 断言受信任权威(条目):#加载时校验 trustedHosts 条目
    """断言一条配置的 trustedHosts 条目是规范形态的裸权威（host 或 host:port）。"""
    解析=解析权威(条目)#尝试当权威解析
    if 解析 is not None and 规范权威(条目,解析)==条目.lower():#规范形态则通过
        return#通过
    raise 连接错误('client-connection: trustedHosts entry '+repr(条目)+' is not a bare host[:port] authority')#否则加载失败

def 是否受信任权威(主机解析,受信任表):#Host 是否在名单
    """请求权威是否匹配某条 trustedHosts 条目。"""
    for 条目 in 受信任表:#任一条匹配即可
        条目解析=解析权威(条目)#解析条目
        if 条目解析 is None:#加载期已拒绝畸形，这里防守
            continue#跳过
        规范=规范权威(条目,条目解析)#规范形态
        if 规范==条目解析.hostname:#无端口 → 只比 hostname
            if 条目解析.hostname==主机解析.hostname:#任意端口
                return True#匹配
        elif 规范==(主机解析.hostname or '')+(':'+str(主机解析.port) if 主机解析.port else ''):#有端口 → 精确
            if 条目解析.hostname==主机解析.hostname and 条目解析.port==主机解析.port:#精确
                return True#匹配
        elif 规范权威(条目,条目解析)==规范权威((主机解析.hostname or '')+(':'+str(主机解析.port) if 主机解析.port else ''),主机解析):#规范相等
            return True#匹配
    return False#无一匹配

def 是否受信任接口请求(请求,受信任表):#/api 信任判定
    """决定一条 /api 请求能否到达 RPC 桥。请求冻结为 dict。"""
    请求头表=请求['headers'] if 'headers' in 请求 else None#头
    主机=取头(请求头表,'host')#Host 头
    if 主机 is None:#没有 Host 拒绝
        return False#拒绝
    主机解析=解析权威(主机)#解析权威
    if 主机解析 is None:#解析失败拒绝
        return False#拒绝
    if (not 是否回环主机名(主机解析.hostname or '')) and (not 是否受信任权威(主机解析,受信任表)):#既非回环也不在名单
        return False#拒绝
    if 取头(请求头表,'sec-fetch-site')=='cross-site':#跨站 fetch 拒绝
        return False#拒绝
    源=取头(请求头表,'origin')#可选 Origin
    if 源 is None:#无 Origin：Host 围栏已够
        return True#通过
    源解析=解析URL(源)
    请求主机=(主机解析.hostname or '')+(':'+str(主机解析.port) if 主机解析.port else '')#请求 host
    源主机=(源解析.hostname or '')+(':'+str(源解析.port) if 源解析.port else '')#源 host
    return 源主机==请求主机 or ((源解析.hostname==主机解析.hostname) and (源解析.port==主机解析.port or (源解析.port is None and 主机解析.port is None)))#同源比较
