"""对外的会话服务面 — `ctx.sessions` 暴露内容。

对齐上游 `runtime/src/client/contract/sessions.ts`。公开面仅中文名。
跨域消费方继续用更窄的会话端口；线泵入口留在具体类上。
加宽本面就是显式加宽功能对会话域能做什么。

依赖未迁：SessionBinding / SessionListState / SessionProvideDescriptor（sessions/service）、
HostObservable / SessionMaybeProvideInfo（ui-slots）、完整 RpcResult 图；
本叶以鸭式 object / dict / 可调用表达上述类型能承载的通道行为。
智能体上下文类型见 `客户端/智能体/作用域`（本叶不重导，避免跨叶耦合）。
"""
from typing import Protocol#协议钉住鸭子面

__all__=[#仅中文公开名
    '会话集面方法',
    '会话集面',
]#公开面结束

#------------------------------ 方法名表（稳定动词清单） ------------------------------

会话集面方法=(#ISessions 方法名
    'list',#列表快照
    'currentProvideInfo',#当前 provide 信息
    'searchResultLimit',#搜索结果上限
    'open',#打开会话
    'openSubagent',#打开子智能体
    'subagentAddress',#读子智能体地址
    'setSubagentCatalogOpen',#设置名册开闭
    'refreshSubagents',#刷新子智能体
    'noteAgentPreset',#记下预设
    'clear',#清除选择
    'search',#搜索消息
    'fork',#分叉会话
    'provide',#登记 provide
    'scope',#解析作用域
    'scopeOf',#读作用域标签
    'sessionOf',#取会话面
    'binding',#取会话绑定
)#方法结束

#------------------------------ Protocol（对齐 ISessions） ------------------------------

class 会话集面(Protocol):#ISessions
    """作为 `ctx.sessions` 注入的会话服务面。"""

    @property
    def list(自身):#列表快照
        """useSessions 标准源（列表行 + 当前选择；只读面 — 写入留在域内）。"""
        ...#协议槽

    @property
    def currentProvideInfo(自身):#当前 provide
        """原子的当前会话 provide 投影（渲染器宿主的 `sessions.provideInfo` 源）。"""
        ...#协议槽

    @property
    def searchResultLimit(自身):#搜索上限
        """`session.search` 结果绑定线模式固定下来的上限。

        不是按连接的状态：每种传输（含夹具）都报告同一个数。
        """
        ...#协议槽

    def open(自身,会话id):#打开会话
        """把一条会话选为当前。

        @param 会话id - 会话 id（必须已在列表里；未知 id 大声失败）。
        """
        ...#协议槽

    def openSubagent(自身,地址):#打开子智能体
        """经精确的直接父地址打开一条健康的名册子项。

        @param 地址 - 名册导出的父与子 id。
        """
        ...#协议槽

    def subagentAddress(自身,会话id):#读子智能体地址
        """解析一条已发现的直接父地址，但不打开它。

        @param 会话id - 可能已寻址的子 id。
        @returns 仍保留的地址（若有）。
        """
        ...#协议槽

    def setSubagentCatalogOpen(自身,父会话id,开闭):#设置名册开闭
        """标记一个名册菜单是否在消费活着的成员更新。

        @param 父会话id - 名册拥有者。
        @param 开闭 - 当前菜单状态。
        """
        ...#协议槽

    async def refreshSubagents(自身,父会话id):#刷新子智能体
        """刷新一份直接子名册。

        @param 父会话id - 名册拥有者。
        @returns 当前或新开始的刷新完成。
        """
        ...#协议槽

    def noteAgentPreset(自身,会话id,智能体预设):#记下预设
        """记下一条会话现在跑的组合。

        agent-preset 座位在空白会话切换成功后调用，
        让头标跟着组合走，而不是等下一次完整列表刷新。
        @param 会话id - 已切换的会话。
        @param 智能体预设 - 宿主确认的预设 id。
        """
        ...#协议槽

    def clear(自身):#清除选择
        """清掉当前选择，进入无会话视图状态。"""
        ...#协议槽

    async def search(自身,查询,信号):#搜索消息
        """搜索宿主可见的消息内容索引。

        结果只属于本次请求；列表快照仍是元数据权威。
        @param 查询 - 非空白字面短语。
        @param 信号 - 被取代的搜索的取消（AbortSignal 鸭式）。
        @returns 有界结果，或业务/传输错误。
        """
        ...#协议槽

    async def fork(自身,选项):#分叉会话
        """从源会话一条已完成回合的前缀分叉。

        兑现时子会话已在列表仓库里，`open()` 可以瞄准它。
        @param 选项 - 含 sessionId、可选 atSeq、可选 increaseTitle。
        @returns 子会话 id。
        @raises 分叉失败，或请求的子标题在创建后重命名失败。
        """
        ...#协议槽

    def provide(自身,描述符):#登记 provide
        """登记一个按会话的标准 props 提供方。

        钩子在渲染侧变成 `use<Name>` 选择器钩；props 原样展开。
        @param 描述符 - 静态成员名册加上按会话的解析器。
        @returns 移除该提供方的 disposer。
        """
        ...#协议槽

    def scope(自身,会话id):#解析作用域
        """解析一个智能体作用域上下文视图（用完即弃）。

        @param 会话id - 会话 id。
        @returns 作用域 ctx；既不在列表里也尚未作用域化则为 None。
        """
        ...#协议槽

    def scopeOf(自身,上下文):#读作用域标签
        """从上下文读出智能体作用域标签。

        服务方法边界：fetch 包必须经 ctx.sessions 到达作用域解析。
        @param 上下文 - 任意客户端上下文。
        @returns 会话 id；根上下文则为 None。
        """
        ...#协议槽

    def sessionOf(自身,上下文):#取会话面
        """解析智能体作用域上下文背后的会话面。

        @param 上下文 - 智能体作用域上下文。
        @returns 会话面；ctx 未打标签或其作用域已被剪掉则为 None。
        """
        ...#协议槽

    def binding(自身,会话id):#取会话绑定
        """解析稳定的会话绑定（按作用域寻址的组装源）。

        @param 会话id - 会话 id。
        @returns 绑定；既不在列表里也尚未作用域化则为 None。
        """
        ...#协议槽
