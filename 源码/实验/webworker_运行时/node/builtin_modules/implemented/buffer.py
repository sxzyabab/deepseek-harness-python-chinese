"""Worker 用的 `node:buffer`，由 `buffer` npm 包（feross）支撑，并安装匹配的
`globalThis.Buffer`。

对齐上游 `webworker-runtime/src/node/builtin_modules/implemented/buffer.ts`。
"""
from buffer import Buffer,kMaxLength#feross buffer包

__all__=['Buffer','kMaxLength','constants','__esModule','default']#Node面

globals()['Buffer']=Buffer#安装全局Buffer

constants={#大小常量
    'MAX_LENGTH':kMaxLength,#最大字节长度
    'MAX_STRING_LENGTH':536_870_888,#最大字符串长度
}#constants结束

__esModule=True#CJS互操作
default={'Buffer':Buffer,'constants':constants,'kMaxLength':kMaxLength}#默认导出
