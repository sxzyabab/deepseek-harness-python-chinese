"""浏览器拥有的时区采样，供提示词 RPC 溯源。

对齐上游 `session-controller/src/client/time-zone.ts`。公开面仅中文名。
纯 React/DOM 不可用；用本机 IANA 区名等价 Intl.DateTimeFormat().resolvedOptions().timeZone。
"""
from datetime import datetime#本机时区
from zoneinfo import ZoneInfo#IANA

__all__=['解析客户端时区']#仅中文公开名

def 解析客户端时区():
    """解析一次出站操作的当前本机 IANA 时区。

    对齐浏览器 `Intl.DateTimeFormat().resolvedOptions().timeZone`。
    运行时无法提供非空时区时抛出。
    """
    try:
        本地=datetime.now().astimezone().tzinfo#本机 tzinfo
        if isinstance(本地,ZoneInfo):#IANA
            时区=本地.key#规范键
        else:#偏移或其它
            时区=getattr(本地,'key',None) or getattr(本地,'zone',None)#尝试键
            if not isinstance(时区,str) or len(时区)==0:#不可用
                时区=str(本地) if 本地 is not None else ''#退化
    except Exception as 错误:
        raise RuntimeError('browser time zone is unavailable') from 错误#时报不可用
    if not isinstance(时区,str) or len(时区)==0:#空
        raise RuntimeError('browser time zone is unavailable')#时报不可用
    return 时区#返回
