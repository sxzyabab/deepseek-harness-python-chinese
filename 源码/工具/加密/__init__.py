"""在各 JavaScript 运行时可用的 UUID 铸造。`crypto.randomUUID` 是安全上下文 Web API——局域网 HTTP 页面或 worker 没有该方法——而 `crypto.getRandomValues` 在各处都可用。本模块用 `secrets` 统一替代各调用方的 polyfill。"""
import secrets#密码学随机
from ...依赖.工具 import 二进制#base64 编解码
__all__=['字节转base64','随机uuid']#仅中文公开名

字节转base64=二进制.转base64#依赖版 base64 编码

def 随机uuid():#随机 v4 UUID
    """用密码学随机字节铸造 RFC 9562 v4 UUID 字符串。"""
    字节=secrets.token_bytes(16)#16 字节随机
    钉=[(字节[索引] if 索引 not in (6,8) else ((字节[6]&0x0f)|0x40) if 索引==6 else ((字节[8]&0x3f)|0x80)) for 索引 in range(16)]#版本 4 与变体位
    十六=[format(值,'02x') for 值 in 钉]#两位十六进制
    串=''.join(十六)#连续十六进制
    return 串[0:8]+'-'+串[8:12]+'-'+串[12:16]+'-'+串[16:20]+'-'+串[20:]#RFC 9562 连字符形
