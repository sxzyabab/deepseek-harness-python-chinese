from . import (
    依赖快照 as vendor,
    客户端,
    异常,
    api,
    )
cordis=vendor.cordis

from . import 源码

def 注入内置():
    import builtins
    builtins.cordis=cordis