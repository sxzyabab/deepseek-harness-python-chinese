"""端点具名的 Typert Remote 流量 mock：按 `<namespace>/<method>` 索引的一元应答与流脚本表、脚本流控制、载体日志，以及 `connection` 插件经 `__DSH_TRANSPORT__.rpc` 接受的 Connection 载体面。

对齐上游 `remote-mock/src/index.ts`。公开面仅中文名。
"""
from .端点模拟 import 远程模拟,成功信封#模拟类与成功信封
from .流脚本 import 帧脚本,打开流脚本,远程模拟错误#流脚本与异常基类

__all__=[#仅中文公开名
    '远程模拟','成功信封','帧脚本','打开流脚本','远程模拟错误',
]#公开面结束
