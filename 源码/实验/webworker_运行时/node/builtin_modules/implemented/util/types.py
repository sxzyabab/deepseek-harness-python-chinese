from ..util import types#共享谓词实现

__all__=['isPromise','isDate','isRegExp','isTypedArray','__esModule','default']#Node面

isPromise=types['isPromise']#再导出谓词
isDate=types['isDate']#Date
isRegExp=types['isRegExp']#RegExp
isTypedArray=types['isTypedArray']#TypedArray
__esModule=True#CJS互操作
default=types#默认导出谓词集
