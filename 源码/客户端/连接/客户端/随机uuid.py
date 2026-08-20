"""浏览器安全的 UUID 生成，用于客户端线关联。

对齐上游 `connection/src/client/random-uuid.ts`。公开面仅中文名。
"""
import os#熵源

__all__=['随机uuid']#仅中文公开名

def 随机uuid():#生成 UUID v4
    """由 os.urandom 支撑的 RFC 4122 第 4 版 UUID。"""
    字节=bytearray(os.urandom(16))#16 个随机字节
    字节[6]=(字节[6]&0x0f)|0x40#版本 4
    字节[8]=(字节[8]&0x3f)|0x80#RFC 4122 变体
    十六=''.join(f'{一:02x}' for 一 in 字节)#转成 32 位十六进制
    return f'{十六[0:8]}-{十六[8:12]}-{十六[12:16]}-{十六[16:20]}-{十六[20:]}'#插连字符
