"""Zstandard 帧编解码（对齐 upstream session-persistence-jsonl/zstd）。"""
try:#可选依赖
    import zstandard as zstd#zstd
    _有zstd=True#可用
except ImportError:#缺失
    _有zstd=False#不可用

def 压缩zstd帧(明文):#压缩一帧
    """把 UTF-8 明文压成单 zstd 帧。"""
    if not _有zstd:#缺库
        raise Exception('session-persistence-jsonl: zstandard package is required for zstd compression')#阻塞
    压缩器=zstd.ZstdCompressor()#压缩器
    return 压缩器.compress(明文)#帧

def 解压zstd帧(载荷):#解压一帧
    """解压单 zstd 帧为 bytes。"""
    if not _有zstd:#缺库
        raise Exception('session-persistence-jsonl: zstandard package is required for zstd decompression')#阻塞
    解压器=zstd.ZstdDecompressor()#解压器
    return 解压器.decompress(载荷)#明文

__all__=['压缩zstd帧','解压zstd帧']#公开面
