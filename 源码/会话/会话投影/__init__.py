"""会话投影能力缝 Service Definition（`ctx.sessionProjections`）。

对齐上游 `@deepseek-ai/dsh-session-projection`。整值事件规则：带状态的日志事件必须携带变更后的完整状态。
"""
from .注册表 import 会话投影注册表#注册表实现
from .类型 import 会话投影映射,会话投影状态映射#类型表
__all__=[#仅中文公开名
    '会话投影注册表','会话投影映射','会话投影状态映射','默认',
]#公开面结束
默认=会话投影注册表#中文默认导出
default=会话投影注册表#Cordis 默认导出
