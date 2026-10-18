'网页服务器的失败。业务文件只抛，不自己定义异常类'
import json#主机文本

class 网页服务器错误(Exception):
    '绑定、路由、源地址或 TLS 材料失败'

def 拒绝非字面地址(值):
    '绑定地址不是具体的 IPv4 或 IPv6 字面量'
    raise 网页服务器错误('webserver: host '+json.dumps(值)+' is not a concrete IPv4 or IPv6 address literal')
