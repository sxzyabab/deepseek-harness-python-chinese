from readable_stream import Stream

__all__=[
    'Duplex','PassThrough','Readable','Stream','Transform','Writable',
    'addAbortSignal','compose','destroy','finished','getDefaultHighWaterMark',
    '_isArrayBufferView','isDestroyed','isDisturbed','isErrored','isReadable',
    'isWritable','pipeline','promises','setDefaultHighWaterMark','__esModule','default',
]

#readable-stream 的命名空间静态不读 this；直接取成员。
Duplex=Stream.Duplex
PassThrough=Stream.PassThrough
Readable=Stream.Readable
StreamBase=Stream.Stream
Transform=Stream.Transform
Writable=Stream.Writable
addAbortSignal=Stream.addAbortSignal
compose=Stream.compose
destroy=Stream.destroy
finished=Stream.finished
isDisturbed=Stream.isDisturbed
isErrored=Stream.isErrored
isReadable=Stream.isReadable
pipeline=Stream.pipeline
promises=Stream.promises
getDefaultHighWaterMark=StreamBase.getDefaultHighWaterMark
isDestroyed=StreamBase.isDestroyed
isWritable=StreamBase.isWritable
setDefaultHighWaterMark=StreamBase.setDefaultHighWaterMark

#readable-stream 跟踪 Node 18 的 16 KiB 字节默认；本仓库运行 Node 22+，
#其通用与文件流使用 64 KiB。
if getDefaultHighWaterMark(False)!=64*1024: setDefaultHighWaterMark(False,64*1024)

def 是否数组缓冲视图(值):
    """测试值是否为 ArrayBuffer 视图。"""
    if 'ArrayBuffer' not in globals():
        return False
    是视图=getattr(globals()['ArrayBuffer'],'isView',None)
    return callable(是视图) and 是视图(值)

_isArrayBufferView=是否数组缓冲视图
streamDefault=StreamBase
streamDefault._isArrayBufferView=是否数组缓冲视图
streamDefault.getDefaultHighWaterMark=getDefaultHighWaterMark
streamDefault.isDestroyed=isDestroyed
streamDefault.isWritable=isWritable
streamDefault.setDefaultHighWaterMark=setDefaultHighWaterMark

Stream=StreamBase
__esModule=True
default=streamDefault
