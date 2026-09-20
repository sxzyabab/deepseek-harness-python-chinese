"""平台无关的已生成宿主 Remote 贡献组装（客户端面）。

本地已有远程贡献的挂载序；插件装载 / 办公转 PDF 等尚无本地远程模块时不入表。
"""
from ...预设.智能体预设.远程 import 远程贡献表 as 智能体预设远程#agent-presets
from ...交互.命令.远程 import 远程贡献表 as 命令远程#commands
from ...api.设置控制器.远程 import 远程贡献表 as 设置控制器远程#settings-controller
from ...目标.目标.远程 import 远程贡献表 as 目标远程#goals
from ...模型后端.llm.远程 import 远程贡献表 as 大模型远程#llm
from ...拓展.cordis服务端.远程 import 远程贡献表 as 动态远程#dynamic
from ...宿主.插件清单.远程 import 远程贡献表 as 插件清单远程#plugin-inventory
from ...反馈.消息反馈.远程 import 远程贡献表 as 消息反馈远程#message-feedback
from ...反馈.命令_反馈.远程 import 远程贡献表 as 会话反馈远程#command-feedback
from ...客户端.文件上传.远程 import 远程贡献表 as 文件上传远程#file-upload
from ...上下文.会话引用.远程 import 远程贡献表 as 会话引用远程#session-reference
from ...子智能体.子智能体.远程 import 远程贡献表 as 子智能体远程#subagent
from ...api.会话控制器.远程 import 远程贡献表 as 会话远程#session-controller
from ...api.工作区控制器.远程 import 远程贡献表 as 工作区远程#workspace-controller
from ...api.工作区文件.远程 import 远程贡献表 as 工作区文件远程#workspace-files
from ...交互.命令 import 类型 as _命令类型#侧效：commands 事件声明
from ...拓展.cordis服务端 import 类型 as _动态类型#侧效：动态包转发事件
from ...目标.目标 import 类型 as _目标类型#侧效：goals 事件声明
from ...模型后端.llm import 类型 as _大模型类型#侧效：大模型事件声明
from ...预设.智能体预设 import 类型 as _预设类型#侧效：agent-preset
from ...配置.配置 import 类型 as _设置类型#侧效：设置事件声明
from .类型 import 远程转发事件名#转发事件名类型出处
from .远程事件 import 远程转发事件#白名单
from .远程方法目录 import 所选远程目录,包名元组,导出名元组,所选远程贡献#目录与贡献
from . import 载荷词汇#载荷词表再导出面

客户端远程=dict#TypertClientRemote / ClientRemote：$mount / $on / 命名空间面
上下文远程槽名='remote'#Cordis Context 上的 Remote 服务槽名

__all__=[#仅中文公开名
    '依赖','应用','所选贡献','所选远程目录','包名元组','导出名元组','所选远程贡献',
    '远程转发事件名','远程转发事件',
    '客户端远程','上下文远程槽名',
    '载荷词汇',
]#公开面结束

依赖=['remote']

def 所选贡献():
    """返回本组装选中的 Remote 贡献。"""
    return (#追踪挂载序
        智能体预设远程,命令远程,设置控制器远程,目标远程,大模型远程,动态远程,
        插件清单远程,消息反馈远程,会话反馈远程,文件上传远程,会话引用远程,
        子智能体远程,会话远程,工作区远程,工作区文件远程,
    )#结束

def 应用(上下文):
    """挂载本客户端组装明确选中的宿主能力；返回拆除函数。"""
    拆除列表=[]#已挂载贡献的拆除函数
    try:
        for 贡献 in 所选贡献():#本组装选中的列表
            拆除列表.append(上下文.remote.mount(贡献))#挂载并记下
    except BaseException:
        for 拆除 in reversed(拆除列表):#反向
            拆除()#拆除
        raise#继续抛
    def 整拆():
        """按挂载的相反顺序拆除。"""
        for 拆除 in reversed(拆除列表):#反向
            拆除()#拆除
    return 整拆#拆除函数

inject=依赖#框架槽
apply=应用#框架槽
