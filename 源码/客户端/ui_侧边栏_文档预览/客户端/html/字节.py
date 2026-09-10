"""UTF-8 解码用于文件字节；编码仅用于 iframe 脚本载荷。

对齐上游 `ui-sidebar-documentpreview/src/client/html/bytes.ts`。公开面仅中文名。
"""
import base64#base64

__all__=['解码文本','编码文本']#仅中文公开名

_分块字节=0x8000#分块


def 解码文本(数据):
    """解码完整 UTF-8 文本，拒绝无效字节序列。"""
    return 数据.decode('utf-8')#严格默认；畸形抛 UnicodeDecodeError


def 编码文本(文本):
    """为 iframe 的 base64 载荷编码 Unicode 文本。"""
    字节=文本.encode('utf-8')#UTF-8
    return base64.b64encode(字节).decode('ascii')#base64
