"""设置命名空间作用域约定（类型面；实现在 ui-settings）。

对齐上游 `runtime/src/client/contract/settings-scope.ts`。公开面仅中文名。
类型住在这里；实现及其宿主传输住在设置面，避免功能服务与绑定面闭环引用。

依赖未迁：泛型分区 T、宿主 SettingsScope 拥有者缝；
本叶以鸭式 object / 可调用表达分区值与解码器。
"""
from typing import Protocol,TypedDict,NotRequired,Literal,Any#协议与结构类型

__all__=[#仅中文公开名
    '设置作用域快照键',
    '设置作用域规格键',
    '设置作用域方法',
    '设置作用域快照',
    '设置作用域规格',
    '设置作用域',
]#公开面结束

#------------------------------ 方法名表（稳定动词清单） ------------------------------

设置作用域快照键=(#快照字段
    'status',#loading / ready / unavailable
    'value',#最近接受的分区
    'base',#组合基线
    'user',#用户层
    'revision',#修订号
    'writable',#是否可写
    'mode',#host / memory
)#快照键结束

设置作用域规格键=(#规格字段
    'namespace',#命名空间
    'decode',#可选解码
)#规格键结束

设置作用域方法=(#句柄方法
    'getSnapshot',#读快照
    'subscribe',#订阅
    'set',#写字段
    'unset',#清字段
)#方法结束

#------------------------------ TypedDict / Protocol（对齐接口体） ------------------------------

class 设置作用域快照(TypedDict):#SettingsScopeSnapshot
    """一个设置命名空间的客户端同步状态。"""

    status:Literal['loading','ready','unavailable']#同步状态
    value:Any#最近一次接受的分区；第一次接受前为 None
    base:Any#组合基线（字段清除后回退）
    user:Any#已存储的原始用户层（若有）
    revision:NotRequired[float]#命名空间修订；第一次宿主视图前可缺
    writable:bool#宿主文档是否接受写入
    mode:Literal['host','memory']#host 同步文档；memory 进程内

class 设置作用域规格(TypedDict):#SettingsScopeSpec
    """浏览器插件消费的、域拥有的一个设置命名空间描述。"""

    namespace:str#拥有方宿主插件登记的命名空间
    decode:NotRequired[Any]#可选解码器；(section) -> T | None

class 设置作用域(Protocol):#SettingsScope
    """一个命名空间持久化分区上的响应式拥有方句柄。"""

    def getSnapshot(自身):#读快照
        """当前同步快照（下次变更前引用稳定）。

        @returns 设置作用域快照。
        """
        ...#协议槽

    def subscribe(自身,监听器):#订阅
        """观察快照替换。

        @param 监听器 - 每次快照变更后调用。
        @returns 去掉本监听器的 disposer。
        """
        ...#协议槽

    async def set(自身,字段,值):#写字段
        """排队写一个字段。

        快速写入保持变更顺序，每条带着最新已知命名空间修订，只有最新落定可以发布；
        被拒或失败的最新写入改为重载宿主状态。
        @param 字段 - 分区内的标量字段。
        @param 值 - 用户选定的 JSON 形态值。
        @returns 写入以及任何最新写入恢复读取落定之后。
        """
        ...#协议槽

    async def unset(自身,字段):#清字段
        """排队清除一个字段，让该字段重新继承组合层。

        与 set 共享顺序、修订和恢复约定。
        @param 字段 - 分区内的标量字段。
        @returns 清除以及任何最新写入恢复读取落定之后。
        """
        ...#协议槽
