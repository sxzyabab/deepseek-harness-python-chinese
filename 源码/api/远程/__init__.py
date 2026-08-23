"""Remote 贡献组装的宿主 BFF 入口。

对齐上游 `api/remotes/src/index.ts`。公开面仅中文名。
各归属包 `类型` 侧效拉入，使转发事件键面与宿主声明同源（对齐上游 satisfies 前置导入）。
无 satisfies 关键字：用显式成员断言代替形态门禁。
"""
from ..指令 import 类型 as _命令类型#侧效：命令事件声明
from ...拓展.cordis_服务端 import 类型 as _动态类型#侧效：动态包转发事件
from ..凭据 import 类型 as _凭据类型#侧效：凭证事件声明
from ..llm import 类型 as _大模型类型#侧效：大模型事件声明
from ..智能体预设 import 类型 as _预设类型#侧效：智能体预设事件
from ..配置 import 类型 as _设置类型#侧效：设置事件声明
from .智能体查找 import (#智能体查找（含 agent-lookup 类型面）
    远程会话未找到,远程子智能体会话所有权,
    有远程子智能体所有者,远程子智能体所有权错误,
    查看远程会话,创建远程智能体解析器,
    远程查找错误码,远程查找错误,
    远程智能体结果成功,远程智能体结果失败,远程智能体结果,远程智能体选项,
)#查找
from .远程事件 import 远程转发事件,API_REMOTE_FORWARDED_EVENTS#转发事件
from .类型 import (#types.ts 白名单投影与席位
    远程转发事件名,远程事件选择席位,可订阅远程事件名,
)#类型
from . import 客户端 as 客户端面#客户端 Remote 组装

名称='api-remotes'#插件名（字面量）
注入=[]#宿主面空 apply；贡献由客户端清单注入

def 应用():#宿主插件体
    """被选中的贡献只在 Client 环境挂载。"""
    return#空实现

apply=应用#上游名

def _断言可转发白名单(白名单):#无 satisfies：显式列表成员门禁
    """断言白名单每条均为选择席位键，且与席位键集合一致。

    对齐上游 `API_REMOTE_FORWARDED_EVENTS satisfies readonly TypertForwardableEvent[]`：
    Python 无 satisfies，也无 Events 图上的 Forwardable 谓词；本组装以席位键为可运行成员集合做双向校验。
    """
    席位键=frozenset(远程事件选择席位.__annotations__)#TypedDict 席位键
    名单=tuple(白名单)#固化顺序
    if not isinstance(白名单,(tuple,list)):#必须是序列
        raise AssertionError('API_REMOTE_FORWARDED_EVENTS must be a sequence of event names')#形态
    for 名 in 名单:#逐条成员
        if 名 not in 席位键:#不在席位则失败（对齐 satisfies 成员门禁）
            raise AssertionError('forwarded event '+repr(名)+' is not a TypertRemoteEventSelection key')#点名
    if frozenset(名单)!=席位键:#双向：席位不得多出白名单未列键
        raise AssertionError('API_REMOTE_FORWARDED_EVENTS must match TypertRemoteEventSelection keys')#一致

_断言可转发白名单(API_REMOTE_FORWARDED_EVENTS)#导入时门禁（对齐宿主面 satisfies）

__all__=[#公开面：对齐 index.ts（查找 + 白名单类型 + apply；连接载体走客户端/载荷词汇）
    '远程会话未找到','远程子智能体会话所有权',
    '有远程子智能体所有者','远程子智能体所有权错误',
    '查看远程会话','创建远程智能体解析器',
    '远程查找错误码','远程查找错误',
    '远程智能体结果成功','远程智能体结果失败','远程智能体结果','远程智能体选项',
    '远程转发事件','API_REMOTE_FORWARDED_EVENTS','远程转发事件名',
    '远程事件选择席位','可订阅远程事件名',
    '名称','注入','应用','apply','客户端面',
]#结束
