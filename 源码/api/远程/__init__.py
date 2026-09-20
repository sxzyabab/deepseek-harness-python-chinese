"""远程贡献组装的宿主入口。

各归属包类型模块侧效拉入，使转发事件键面与宿主声明同源。
用显式成员断言代替形态门禁。
"""
from ...交互.命令 import 类型 as _命令类型#侧效：命令事件声明
from ...拓展.cordis服务端 import 类型 as _动态类型#侧效：动态包转发事件
from ...凭据.凭据 import 类型 as _凭据类型#侧效：凭证事件声明
from ...目标.目标 import 类型 as _目标类型#侧效：目标事件声明
from ...模型后端.llm import 类型 as _大模型类型#侧效：大模型事件声明
from ...预设.智能体预设 import 类型 as _预设类型#侧效：智能体预设事件
from ...配置.配置 import 类型 as _设置类型#侧效：设置事件声明
from ...交互.用户审批 import 类型 as _审批类型#侧效：用户审批事件声明
from ...交互.用户提问 import 类型 as _提问类型#侧效：用户提问事件声明
from .智能体查找 import (
    远程会话未找到,远程子智能体会话所有权,
    有远程子智能体所有者,远程子智能体所有权错误,
    查看远程会话,创建远程智能体解析器,
    远程查找错误码,远程查找错误,
    远程智能体结果成功,远程智能体结果失败,远程智能体结果,远程智能体选项,
)
from .远程事件 import 远程转发事件
from .类型 import (
    远程转发事件名,远程事件选择席位,可订阅远程事件名,
)
from . import 客户端 as 客户端面

包名='@deepseek-ai/dsh-api-remotes'
名称='api-remotes'
依赖=[]

__all__=[
    '远程会话未找到','远程子智能体会话所有权',
    '有远程子智能体所有者','远程子智能体所有权错误',
    '查看远程会话','创建远程智能体解析器',
    '远程查找错误码','远程查找错误',
    '远程智能体结果成功','远程智能体结果失败','远程智能体结果','远程智能体选项',
    '远程转发事件','远程转发事件名',
    '远程事件选择席位','可订阅远程事件名',
    '包名','名称','依赖','应用','默认','客户端面',
]

def 应用():
    """被选中的贡献只在 Client 环境挂载。"""
    return

def _断言可转发白名单(白名单):
    """断言白名单每条均为选择席位键，且与席位键集合一致。"""
    席位键=frozenset(远程事件选择席位.__annotations__)
    名单=tuple(白名单)
    if not isinstance(白名单,(tuple,list)):
        raise AssertionError('API_REMOTE_FORWARDED_EVENTS must be a sequence of event names')
    for 名 in 名单:
        if 名 not in 席位键:
            raise AssertionError('forwarded event '+repr(名)+' is not a TypertRemoteEventSelection key')
    if frozenset(名单)!=席位键:
        raise AssertionError('API_REMOTE_FORWARDED_EVENTS must match TypertRemoteEventSelection keys')

_断言可转发白名单(远程转发事件)#导入时门禁

默认=应用
name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
default=默认#框架槽
