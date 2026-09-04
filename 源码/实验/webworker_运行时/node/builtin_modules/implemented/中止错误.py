"""构建可中止内置 API 共用的 Node 风格取消错误。

对齐上游 `webworker-runtime/src/node/builtin_modules/implemented/abort-error.ts`。
公开面仅中文名。自 `abort_error` 再导出，避免双份实现。
"""
from .abort_error import 中止错误#权威实现

__all__=['中止错误']#仅中文公开名
