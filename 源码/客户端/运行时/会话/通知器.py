"""再导出路B通知器（本路径不保留第二份实现）。

对齐上游 `runtime/src/client/sessions/notifier.ts`。公开面仅中文名。
"""
from ..客户端.会话.通知器 import 通知器#路B权威

__all__=['通知器']#仅中文公开名
