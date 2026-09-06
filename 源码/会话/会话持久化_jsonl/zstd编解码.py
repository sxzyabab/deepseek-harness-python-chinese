"""Zstandard 帧编解码（对齐 upstream session-persistence-jsonl/zstd）。"""
from io import BytesIO#字节流
import zstandard as zstd#zstd

def 压缩zstd帧(明文):#压缩一帧
    """把 UTF-8 明文压成单 zstd 帧。每批追加各写一帧。"""
    压缩器=zstd.ZstdCompressor()#压缩器
    return 压缩器.compress(明文)#单帧

def 解压zstd帧(载荷):#解压全部帧
    """解压文件内全部 zstd 帧为明文 bytes；追加路径多帧拼接必须读尽。"""
    解压器=zstd.ZstdDecompressor()#解压器
    with 解压器.stream_reader(BytesIO(载荷)) as 阅读器:#多帧阅读器
        return 阅读器.read()#全部明文

__all__=['压缩zstd帧','解压zstd帧']#公开面
