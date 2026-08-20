"""共享 Typert Gateway 的宿主入口。

对齐上游 `api/gateway/src/index.ts` 导出面。公开面仅中文名。
"""
from .网关 import Typert网关服务,网关错误,TypertGatewayService,TypertGatewayError#网关实现
from .类型 import 调用远程请求,网关错误码,Typert网关#类型锚点
from . import 客户端 as 客户端面#客户端 Remote 投影

名称='typert-gateway'#插件名（字面量）
注入=['typert']#依赖 typert

def 应用(上下文):#安装网关
    """在宿主组合上挂载 Typert 网关服务。"""
    Typert网关服务(上下文)#构造并登记

apply=应用#上游名

__all__=[#公开面
    'Typert网关服务','网关错误','TypertGatewayService','TypertGatewayError',
    '调用远程请求','网关错误码','Typert网关',
    '名称','注入','应用','apply','客户端面',
]#结束
