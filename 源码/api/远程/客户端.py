"""平台无关的已生成宿主 Remote 贡献组装（客户端面）。

对齐上游 `api/remotes/src/client/index.ts`。公开面仅中文名。
挂载本客户端组装明确选中的宿主能力：commands、goals、dynamic、plugin-inventory、message-feedback。
各叶包父目录（交互/目标/拓展/host/反馈）需在导入路径上，与现有 `goal`/`commands` 等叶包导入约定一致。

加厚面：再导出动态包/清单载荷词表与转发事件白名单，使业务包只点名本组装。
侧效拉入各归属包 `类型` 模块，使转发事件键面与宿主声明同源。
"""
from ...依赖 import cordis#外部依赖胶水
from ...交互.指令.远程 import TYPERT_REMOTE as 命令远程#commands ./remote
from ...目标.目标.远程 import TYPERT_REMOTE as 目标远程#goals ./remote
from ...拓展.cordis_服务端.远程 import TYPERT_REMOTE as 动态远程#dynamic ./remote
from ...host.plugin_inventory.远程 import TYPERT_REMOTE as 插件清单远程#plugin-inventory ./remote
from ...反馈.消息反馈.远程 import TYPERT_REMOTE as 消息反馈远程#message-feedback ./remote
from ...交互.指令 import 类型 as _命令类型#侧效：commands 事件声明
from ...目标.目标 import 类型 as _目标类型#侧效：goals 事件声明
from ...拓展.cordis_服务端 import 类型 as _动态类型#侧效：动态包转发事件
from ...凭据.凭据 import 类型 as _凭据类型#侧效：凭证事件声明
from ...模型后端.llm import 类型 as _大模型类型#侧效：大模型事件声明
from ...预设.智能体预设 import 类型 as _预设类型#侧效：agent-preset/selected
from ...配置.配置 import 类型 as _设置类型#侧效：设置事件声明
from .类型 import 远程转发事件名#转发事件名类型出处
from .远程事件 import 远程转发事件,API_REMOTE_FORWARDED_EVENTS#白名单
from .远程方法目录 import 所选远程目录,包名们,导出名们,所选远程贡献#五包目录与贡献
from . import 载荷词汇#载荷词表再导出面

# Cordis Context.remote 席位（对齐 client/index.ts declare module；非 types.ts）
客户端远程=dict#TypertClientRemote / ClientRemote：$mount / $on / 命名空间面
上下文远程槽名='remote'#Cordis Context 上的 Remote 服务槽名
ClientRemote=客户端远程#上游名

__all__=[#仅中文公开名
    '注入','应用','所选贡献','所选远程目录','包名们','导出名们','所选远程贡献',
    '远程转发事件名','远程转发事件','API_REMOTE_FORWARDED_EVENTS',
    '客户端远程','上下文远程槽名',
    '载荷词汇','inject','apply',
]#公开面结束

注入=['remote']#依赖 remote 服务
inject=注入#上游名

def 解开(值):#承诺则等待
    """承诺则等待，否则原样。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待
    return 值#同步

def 所选贡献():#本组装选中的 Remote 贡献列表
    """返回本组装选中的 Remote 贡献（commands/goals/dynamic/plugin-inventory/message-feedback）。

    对齐上游 client/index.ts 挂载顺序；各包 `远程.py` 为手写 TYPERT_REMOTE（无 typert 生成器时的等价面）。
    """
    return (命令远程,目标远程,动态远程,插件清单远程,消息反馈远程)#五份贡献

def 应用(上下文):#应用客户端 Remote 组装
    """挂载本客户端组装明确选中的宿主能力；返回拆除函数。"""
    拆除们=[]#已挂载贡献的拆除函数
    try:#依次挂载
        for 贡献 in 所选贡献():#本组装选中的列表
            拆除们.append(解开(上下文.remote.mount(贡献)))#挂载并记下
    except Exception:#任一失败则按相反顺序拆掉已成功的
        for 拆除 in reversed(拆除们):#反向
            解开(拆除())#拆除
        raise#继续抛
    def 整拆():#组装拆除函数
        """按挂载的相反顺序拆除。"""
        for 拆除 in reversed(拆除们):#反向
            解开(拆除())#拆除
    return 整拆#拆除函数

apply=应用#上游名
