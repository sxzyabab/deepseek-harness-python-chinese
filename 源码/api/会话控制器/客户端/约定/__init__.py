"""会话客户端约定包。

对齐上游 `session-controller/src/client/contract/`。公开面仅中文名。
"""
from .事件 import 可变会话事件源#事件源
from .快照 import 会话快照字段,打开状态,排队放置#快照
from .会话 import 会话面动词#会话面
from .会话集 import 会话集面动词#会话集

__all__=[#仅中文公开名
    '可变会话事件源',
    '会话快照字段','打开状态','排队放置',
    '会话面动词','会话集面动词',
]#公开面结束
