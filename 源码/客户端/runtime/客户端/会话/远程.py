"""Session 簇会调用的 Remote 命名空间。一个概念一个参数：
Session 及其管理器经此 generated 面到达 Host。

对齐上游 `runtime/src/client/sessions/remotes.ts`。公开面仅中文名；
协议命名空间键 `commands` 保持上游英文。

上游靠 `import type {} from '@deepseek-ai/dsh-api-remotes/client'` 拉入 Remote 面声明合并，
好让 Context['remote'] 带上 generated 命名空间；再 Pick 出 `'commands'`。
Python 无 declare module：本叶用协议钉住「目前只要 commands」的消费面。

依赖未迁：完整 Cordis Context['remote'] 生成面（api-remotes/client 席位合并）；
命令命名空间上的完整方法图以交互/commands 远程贡献为准，本叶只表达会话簇实际触达的面。
"""
from typing import Protocol#协议钉住鸭子面

__all__=[#仅中文公开名
    '会话远程键',
    '命令命名空间键',
    '命令远程命名空间',
    '会话远程',
]#公开面结束

# 上游：Pick<Context['remote'], 'commands'> — 目前只要 commands
会话远程键=('commands',)#SessionRemotes 从 Context.remote 挑出的键元组
命令命名空间键='commands'#协议命名空间键（与 Host 登记名一致）

class 命令远程命名空间(Protocol):#Context.remote.commands 的会话触达面
    """命令包 Remote 命名空间：会话簇经此调用 Host 命令面。

    对齐交互/commands 远程贡献的 `list` / `execute`；
    会话对象层实际调用的是 execute（斜杠命令准入）。
    """

    async def list(自身,智能体):#列出命令
        """列出智能体可见命令描述符。

        @param 智能体 - agent lookup 解析到的在线智能体。
        @returns 只读命令描述符序列。
        """
        ...#协议槽

    async def execute(自身,智能体,行):#执行命令行
        """对本会话智能体执行一行斜杠命令。

        @param 智能体 - 会话 id（agent lookup 键；客户端会话与智能体 1:1）。
        @param 行 - 完整命令行，含前导斜杠。
        @returns 命令执行结果；未匹配时可为 None（会话层折成 matched 布尔）。
        """
        ...#协议槽

class 会话远程(Protocol):#SessionRemotes
    """Session 及其管理器会调用的 generated Remote 命名空间。

    上游：`export type SessionRemotes = Pick<Context['remote'], 'commands'>`。
    目前只要 `commands`；后续若 Session 簇再触达其它命名空间，在此扩键，勿另起叶。
    """

    commands:命令远程命名空间#命令 Remote 命名空间（键名 commands）

# 构造入参说明：会话运行时 / 管理器 / 会话对象层共用同一会话远程实例。
# 运行时传入的对象须满足 会话远程（至少暴露 .commands.execute）。
