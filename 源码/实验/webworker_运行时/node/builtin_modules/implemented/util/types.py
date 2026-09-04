"""`node:util/types` 表面：谓词子集，从 util shim 再导出，使两个说明符共享一份实现。
谓词在构建处对照 Node 检查，位于 `../util.py` 的 `types`。

对齐上游 `webworker-runtime/src/node/builtin_modules/implemented/util/types.ts`。
"""
from ..util import types#共享谓词实现

__all__=['isPromise','isDate','isRegExp','isTypedArray','__esModule','default']#Node面

isPromise=types['isPromise']#再导出谓词
isDate=types['isDate']#Date
isRegExp=types['isRegExp']#RegExp
isTypedArray=types['isTypedArray']#TypedArray
__esModule=True#CJS互操作
default=types#默认导出谓词集
