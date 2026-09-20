from ...未实现失败 import 未实现失败

__all__=[
    'constants','zstdCompressSync','zstdDecompressSync','zstdCompress','zstdDecompress',
    'createZstdDecompress','createZstdCompress','gzip','gzipSync','gunzip','gunzipSync',
    '__esModule','default',
]

模块='node:zlib'

constants={
    'ZSTD_c_compressionLevel':100,
    'ZSTD_c_checksumFlag':201,
    'ZSTD_e_continue':0,
    'ZSTD_e_flush':1,
    'ZSTD_e_end':2,
    'ZSTD_CLEVEL_DEFAULT':3,
    'Z_NO_FLUSH':0,
    'Z_SYNC_FLUSH':2,
    'Z_FINISH':4,
}

zstdCompressSync=未实现失败(模块,'zstdCompressSync')
zstdDecompressSync=未实现失败(模块,'zstdDecompressSync')
zstdCompress=未实现失败(模块,'zstdCompress')
zstdDecompress=未实现失败(模块,'zstdDecompress')

def 创建zstd解压(*位置参数,**关键字参数):
    """流式 Zstandard 解码器占位：返回对象故意缺少 Node 的私有
    `_handle`/`_writeState` 成员。
    """
    def 关闭():
        """尚未打开任何句柄。"""
        pass
    return {'close':关闭}

createZstdDecompress=创建zstd解压
createZstdCompress=未实现失败(模块,'createZstdCompress')
gzip=未实现失败(模块,'gzip')
gzipSync=未实现失败(模块,'gzipSync')
gunzip=未实现失败(模块,'gunzip')
gunzipSync=未实现失败(模块,'gunzipSync')
__esModule=True

default={
    'constants':constants,'zstdCompress':zstdCompress,'zstdCompressSync':zstdCompressSync,
    'zstdDecompress':zstdDecompress,'zstdDecompressSync':zstdDecompressSync,
    'createZstdCompress':createZstdCompress,'createZstdDecompress':创建zstd解压,
    'gzip':gzip,'gzipSync':gzipSync,'gunzip':gunzip,'gunzipSync':gunzipSync,
}
