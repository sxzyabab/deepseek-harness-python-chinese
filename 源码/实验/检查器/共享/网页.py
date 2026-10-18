'已认证的浏览器引导路由。调试地址留在宿主'
from urllib.parse import parse_qsl, urlsplit
from ..异常 import 检查器错误
from .身份 import 检查器id

__all__=['检查器引导路径','检查器引导路由','检查器客户端查询','读检查器客户端选择']

检查器引导路径='/api/experimental-inspector/bootstrap'
检查器引导路由=检查器引导路径[1:]
检查器客户端查询='clientSourceId'


def 读检查器客户端选择(网址):
    '从 DevTools WebSocket 网址读取可选的 Client 选择。重复或非法标识则抛出'
    if hasattr(网址,'query'):
        查询文本=网址.query
    else:
        查询文本=urlsplit(str(网址)).query
    值表=[值 for 键,值 in parse_qsl(查询文本,keep_blank_values=True) if 键==检查器客户端查询]
    if len(值表)==0:
        return None
    if len(值表)!=1:
        raise 检查器错误('Inspector Client selection must occur once')
    return 检查器id(值表[0],检查器客户端查询)
