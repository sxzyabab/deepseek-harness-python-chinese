"""共享 Typert Gateway 的宿主入口。"""
from .网关 import Typert网关服务,网关错误
from .类型 import 调用远程请求,网关错误码,Typert网关
from . import 客户端 as 客户端面
from .流载体 import 远程流载体错误
from .远程流 import 远程流,远程流项,取连接代际源
from .远程事件 import 客户端远程事件
from .快照流 import 远程快照流
from .日志流 import 远程日志流

包名='@deepseek-ai/dsh-api-gateway'
名称='typert-gateway'
依赖=['typert']

__all__=[
    'Typert网关服务','网关错误',
    '调用远程请求','网关错误码','Typert网关',
    '包名','名称','依赖','应用','默认','客户端面',
    '远程流载体错误','远程流','远程流项','取连接代际源',
    '客户端远程事件','远程快照流','远程日志流',
]

def 应用(上下文):
    """在宿主组合上挂载 Typert 网关服务。"""
    Typert网关服务(上下文)

默认=应用
name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
default=默认#框架槽
