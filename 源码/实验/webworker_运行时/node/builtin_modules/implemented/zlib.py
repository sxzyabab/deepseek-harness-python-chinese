from ...未实现失败 import 未实现失败#未实现桩

__all__=[#中文公开名与Node英文挂名
    '创建zstd解压',
    'constants','zstdCompressSync','zstdDecompressSync','zstdCompress','zstdDecompress',
    'createZstdDecompress','createZstdCompress','gzip','gzipSync','gunzip','gunzipSync',
    '__esModule','default',
]#公开结束

模块='node:zlib'#模块名

constants={#常量表
    'ZSTD_c_compressionLevel':100,#压缩级别参数
    'ZSTD_c_checksumFlag':201,#校验和标志
    'ZSTD_e_continue':0,#继续
    'ZSTD_e_flush':1,#刷新
    'ZSTD_e_end':2,#结束
    'ZSTD_CLEVEL_DEFAULT':3,#默认级别
    'Z_NO_FLUSH':0,#不刷新
    'Z_SYNC_FLUSH':2,#同步刷新
    'Z_FINISH':4,#完成
}#constants结束

zstdCompressSync=未实现失败(模块,'zstdCompressSync')#同步压缩桩
zstdDecompressSync=未实现失败(模块,'zstdDecompressSync')#同步解压桩
zstdCompress=未实现失败(模块,'zstdCompress')#回调压缩桩
zstdDecompress=未实现失败(模块,'zstdDecompress')#回调解压桩

def 创建zstd解压(*位置参数,**关键字参数):#流式解压占位
    """流式 Zstandard 解码器占位：返回对象故意缺少 Node 的私有
    `_handle`/`_writeState` 成员。
    """
    def 关闭():#无句柄占位
        """nothing was opened。"""
        pass#无操作
    return {'close':关闭}#无句柄占位

createZstdDecompress=创建zstd解压#Node面
createZstdCompress=未实现失败(模块,'createZstdCompress')#流式压缩桩
gzip=未实现失败(模块,'gzip')#gzip桩
gzipSync=未实现失败(模块,'gzipSync')#gzipSync桩
gunzip=未实现失败(模块,'gunzip')#gunzip桩
gunzipSync=未实现失败(模块,'gunzipSync')#gunzipSync桩
__esModule=True#CJS互操作

default={#默认导出
    'constants':constants,'zstdCompress':zstdCompress,'zstdCompressSync':zstdCompressSync,#zstd族
    'zstdDecompress':zstdDecompress,'zstdDecompressSync':zstdDecompressSync,#解压
    'createZstdCompress':createZstdCompress,'createZstdDecompress':创建zstd解压,#流
    'gzip':gzip,'gzipSync':gzipSync,'gunzip':gunzip,'gunzipSync':gunzipSync,#gzip
}#默认导出结束
