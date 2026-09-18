"""共享 Typert Gateway 的宿主入口。

对齐上游 `api/gateway/src/index.ts` 导出面。公开面仅中文名。
"""
from .网关 import Typert网关服务,网关错误#网关实现
from .类型 import 调用远程请求,网关错误码,Typert网关#类型锚点
from . import 客户端 as 客户端面#客户端 Remote 投影
from .流载体 import 远程流载体错误#流载体错误
from .远程流 import 远程流,远程流项,取连接代际源#远程流
from .远程事件 import 客户端远程事件#远程事件
from .快照流 import 远程快照流#快照流
from .日志流 import 远程日志流#日志流

名称='typert-gateway'#插件名（字面量）
注入=['typert']#依赖 typert

__all__=[#公开面
    'Typert网关服务','网关错误',
    '调用远程请求','网关错误码','Typert网关',
    '名称','注入','应用','客户端面',
    '远程流载体错误','远程流','远程流项','取连接代际源',
    '客户端远程事件','远程快照流','远程日志流',
]#结束

def 应用(上下文):
    """在宿主组合上挂载 Typert 网关服务。"""
    Typert网关服务(上下文)#构造并登记

name=名称#框架槽
inject=注入#框架槽
apply=应用#框架槽
