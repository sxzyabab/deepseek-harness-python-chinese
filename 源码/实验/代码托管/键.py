'变更请求的规范身份'
from ...工具.标识构造 import 标识构造

__all__=['变更请求键']

def 变更请求键(引用):
    """拼出不区分大小写的规范身份。
    引用为 dict，含 repository 与 number。
    返回 forge:host/owner/name#number 的小写文本"""
    仓库=引用['repository']#代码托管仓库
    return 标识构造(
        f"{仓库['forge']}:{仓库['host']}/{仓库['owner']}/{仓库['name']}#{引用['number']}".lower()
    )#宿主比较时忽略大小写
