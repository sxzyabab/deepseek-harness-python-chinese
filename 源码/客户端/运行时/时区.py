"""浏览器拥有的时区采样，供提示 RPC 出处使用。

对齐上游 `runtime/src/client/time-zone.ts`。公开面仅中文名。
"""
from datetime import datetime as 日期时间#本地时区探测

__all__=['解析客户端时区']#仅中文公开名

def 解析客户端时区():#解析当前 IANA 时区
    """为一次出站操作解析当前宿主 IANA 时区。

    @returns 宿主提供的规范时区。
    @raises 运行时给不出非空时区时抛错。
    """
    本地=日期时间.now().astimezone()#带本地偏移的当前时间
    信息=本地.tzinfo#时区对象
    键=getattr(信息,'key',None) if 信息 is not None else None#zoneinfo 的 IANA 键
    if not isinstance(键,str) or 键=='':#空或非字符串
        raise Exception('browser time zone is unavailable')#大声失败
    return 键#规范时区
