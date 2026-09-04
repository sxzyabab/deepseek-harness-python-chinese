"""由 readable-stream 浏览器构建支撑的 `node:stream` 兼容层。

readable-stream 是 Node 流实现的用户态副本。worker 只拥有如 VFS 文件流等
平台适配器；流状态、背压、异步迭代、中止处理与事件顺序留在该维护实现中。

对齐上游 `webworker-runtime/src/node/builtin_modules/implemented/stream.ts`。
公开面中文名；Node 面经别名与 default 暴露英文名。
"""
from readable_stream import Stream#readable-stream包

__all__=[#中文公开名与Node英文挂名
    '是否数组缓冲视图',
    'Duplex','PassThrough','Readable','Stream','Transform','Writable',
    'addAbortSignal','compose','destroy','finished','getDefaultHighWaterMark',
    '_isArrayBufferView','isDestroyed','isDisturbed','isErrored','isReadable',
    'isWritable','pipeline','promises','setDefaultHighWaterMark','__esModule','default',
]#公开结束

#readable-stream 的命名空间静态不读 this；直接取成员。
Duplex=Stream.Duplex#双工
PassThrough=Stream.PassThrough#直通
Readable=Stream.Readable#可读
StreamBase=Stream.Stream#基类
Transform=Stream.Transform#变换
Writable=Stream.Writable#可写
addAbortSignal=Stream.addAbortSignal#中止信号
compose=Stream.compose#组合
destroy=Stream.destroy#销毁
finished=Stream.finished#完成
isDisturbed=Stream.isDisturbed#扰动谓词
isErrored=Stream.isErrored#错误谓词
isReadable=Stream.isReadable#可读谓词
pipeline=Stream.pipeline#管道
promises=Stream.promises#Promise面
getDefaultHighWaterMark=StreamBase.getDefaultHighWaterMark#读高水位
isDestroyed=StreamBase.isDestroyed#销毁谓词
isWritable=StreamBase.isWritable#可写谓词
setDefaultHighWaterMark=StreamBase.setDefaultHighWaterMark#写高水位

#readable-stream 跟踪 Node 18 的 16 KiB 字节默认；本仓库运行 Node 22+，
#其通用与文件流使用 64 KiB。
if getDefaultHighWaterMark(False)!=64*1024: setDefaultHighWaterMark(False,64*1024)#对齐64KiB

def 是否数组缓冲视图(值):#视图谓词
    """测试值是否为 ArrayBuffer 视图。"""
    缓冲=globals().get('ArrayBuffer')#ArrayBuffer
    if 缓冲 is None: return False#无
    是视图=getattr(缓冲,'isView',None)#isView
    return callable(是视图) and 是视图(值)#视图谓词

_isArrayBufferView=是否数组缓冲视图#Node私有面
streamDefault=StreamBase#默认命名空间起点
streamDefault._isArrayBufferView=是否数组缓冲视图#视图谓词
streamDefault.getDefaultHighWaterMark=getDefaultHighWaterMark#读高水位
streamDefault.isDestroyed=isDestroyed#销毁谓词
streamDefault.isWritable=isWritable#可写谓词
streamDefault.setDefaultHighWaterMark=setDefaultHighWaterMark#写高水位

Stream=StreamBase#基类导出名
__esModule=True#CJS互操作
default=streamDefault#默认导出
