from . import (
    客户端,
    异常,
    api,
    )

from . import 源码
packages=源码
vendor=源码.依赖
cordis=vendor.cordis
def 注入内置():
    import builtins
    builtins.cordis=cordis