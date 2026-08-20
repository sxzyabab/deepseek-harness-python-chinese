"""Composer 提交策略：忙碌-Enter 偏好与键盘手势解析。

对齐上游 `ui-conversation/src/client/input/submission-policy.ts`。
实现落在包根 `提交策略.py`；本模块再导出。
"""
from ..提交策略 import 快照仓库,提交策略,默认忙碌回车行为#实现

__all__=['快照仓库','提交策略','默认忙碌回车行为']#仅中文公开名
