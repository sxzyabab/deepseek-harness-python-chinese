"""apiproxy 约定层桶文件。零 Node 依赖，浏览器可导入。对齐上游 `host/apiproxy/src/api/index.ts` 再导出面。"""

from .rpc模式 import Rpc标识,传输错误,服务端响应模式,服务端请求模式#消息层
from .会话检索 import 会话搜索结果上限#检索常量
from . import 事件模式#帧模式子模块

__all__=[#公开面
    'Rpc标识',
    '传输错误',
    '会话搜索结果上限',
    '服务端响应模式',
    '服务端请求模式',
    '事件模式',
]#结束
