"""浏览器拥有的时区采样，供提示词 RPC 溯源。

纯 React/DOM 不可用；用本机 IANA 区名等价 Intl.DateTimeFormat().resolvedOptions().timeZone。
"""
from datetime import datetime as 日期时间
from zoneinfo import ZoneInfo,ZoneInfoNotFoundError as 时区未找到

__all__=['解析客户端时区']#仅中文公开名

def 解析客户端时区():
    """解析一次出站操作的当前本机 IANA 时区。

    等价浏览器 Intl.DateTimeFormat().resolvedOptions().timeZone。
    运行时无法提供非空时区时抛出。
    """
    try:
        本地=日期时间.now(ZoneInfo('UTC')).astimezone().tzinfo#本机 tzinfo；禁止裸 now
        if isinstance(本地,ZoneInfo):#IANA
            时区=本地.key#规范键
        else:#偏移或其它
            时区=getattr(本地,'key',None) or getattr(本地,'zone',None)#尝试键
            if not isinstance(时区,str) or len(时区)==0:#不可用
                时区=str(本地) if 本地 is not None else ''#退化
    except (时区未找到,AttributeError,OSError,ValueError,TypeError) as 错误:
        raise RuntimeError('browser time zone is unavailable') from 错误#时报不可用
    if not isinstance(时区,str) or len(时区)==0:#空
        raise RuntimeError('browser time zone is unavailable')#时报不可用
    return 时区#返回
