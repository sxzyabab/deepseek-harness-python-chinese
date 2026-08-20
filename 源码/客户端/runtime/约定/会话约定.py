"""会话业务约定：事件匹配、位置、节点定义与视图构建器面。

对齐上游 `runtime/src/client/contract/conversation.ts`。公开面仅中文名。
声明合并映射在 Python 侧以可扩展 dict / Protocol 约定表达；引擎键用长度前缀防碰撞。
未增强的合并映射在 Runtime 程序里有意为空；已安装业务包在消费方补具体键。
ConversationLocationDataValue 上游未 export，此处同为模块内私有。
"""
from typing import Protocol,TypedDict,NotRequired,Any,Literal#协议、结构类型与字面量

__all__=[#与上游 export 对齐的中文公开名
    '发布节奏',
    '位置数据作用域',
    '会话上下文键',
    '对话事件输入',
    '对话匹配结果',
    '对话回合数据映射',
    '对话步骤数据映射',
    '对话位置数据仓库',
    '对话位置数据',
    '步骤位置',
    '回合位置',
    '对话位置',
    '对话匹配',
    '对话视图节点',
    '对话视图快照映射',
    '对话视图快照仓库',
    '聊天对话视图节点',
    '对话节点上下文',
    '对话前驱上下文',
    '对话上下文读取器',
    '对话节点定义',
    '对话时间线快照',
    '对话视图构建器',
    '对话视图定义',
]#公开面结束

#------------------------------ 上游已 export 的类型别名 ------------------------------

发布节奏=Literal['none','animation-frame','immediate']#ConversationPublication
位置数据作用域=Literal['step','turn']#ConversationLocationDataScope

#------------------------------ 键构造 ------------------------------

def 会话上下文键(种类,标识):#拼上下文键
    """为定义局部业务身份构造稳定、无碰撞的引擎 Context 键。

    @param 种类 - 定义 kind。
    @param 标识 - 定义局部业务身份。
    @returns 引擎拥有的 Context 键。
    """
    return str(len(种类))+':'+种类+标识#长度前缀防拼接碰撞

#------------------------------ 事件与匹配 ------------------------------

class 对话事件输入(TypedDict):#ConversationEventInput
    """一条原始日志事件，外加可选的信封级展示视图。"""
    event:Any#原始会话事件 SessionEvent
    view:Any#可选展示视图 ToolEventView | None

class 对话匹配结果(TypedDict):#ConversationMatchResult
    """从一条事件抽出的、定义局部的身份与生命周期角色。"""
    id:str#业务身份
    role:Literal['start','update']#生命周期角色

# 可合并扩展的、挂在 Turn / Step 上发布的业务值（声明合并空映射）
对话回合数据映射=dict#ConversationTurnDataMap；业务包补键
对话步骤数据映射=dict#ConversationStepDataMap；业务包补键

class 对话位置数据仓库(Protocol):#ConversationLocationDataStore
    """独立拥有的 Location 业务值的稳定按键读取器。"""

    def get(自身,键):#按键读取
        """读一个业务值，不暴露另一拥有者的可变 State。

        @param 键 - 声明合并出的业务键。
        @returns 最新不可变值（当其拥有 Context 已发布过）。
        """
        ...#协议槽

class _未登记位置数据值(TypedDict):#ConversationLocationDataValue；上游未 export
    """未登记时的位置数据值（模块内私有，不进公开面）。"""
    kind:Literal['turn','step']#所在层级
    turn:int#回合号
    key:str#业务键
    value:Any#业务值
    step:NotRequired[int]#可选步骤号

# 上游：映射仍为空时用未登记值；已登记时为按键展开联合。
# Python 无条件类型：消费方以字典形态承载，键集由业务包声明合并填入。
对话位置数据=_未登记位置数据值#ConversationLocationData 未登记臂；已登记臂同形

class 步骤位置(TypedDict):#StepLocation
    """一个 Agent 步骤的不可变已解析边界。"""
    turn:int#回合号
    step:int#步骤号
    start:Any#可选开始事件 SessionEvent<'step/start'> | None
    end:Any#可选结束事件 SessionEvent<'step/end'> | None
    status:Literal['open','closed','unknown']#开闭状态
    data:Any#步骤作用域业务值读取器（对话位置数据仓库）

class 回合位置(TypedDict):#TurnLocation
    """一个 Agent 回合的不可变已解析边界。"""
    turn:int#回合号
    start:Any#可选开始事件 SessionEvent<'turn/start'> | None
    end:Any#可选结束事件 SessionEvent<'turn/end'> | None
    status:Literal['open','closed','unknown']#开闭状态
    steps:list#其下步骤（步骤位置只读序列）
    data:Any#回合作用域业务值读取器（对话位置数据仓库）

class _会话级对话位置(TypedDict):#ConversationLocation session 臂；不单独 export
    """会话级放置。"""
    kind:Literal['session']#会话级

class _回合级对话位置(TypedDict):#ConversationLocation turn 臂；不单独 export
    """回合级放置。"""
    kind:Literal['turn']#回合级
    turn:回合位置#已解析回合

class _步骤级对话位置(TypedDict):#ConversationLocation step 臂；不单独 export
    """步骤级放置。"""
    kind:Literal['step']#步骤级
    turn:回合位置#所属回合
    step:步骤位置#已解析步骤

class _未解析对话位置(TypedDict):#ConversationLocation unresolved 臂；不单独 export
    """尚未解析的放置。"""
    kind:Literal['unresolved']#尚未解析

# ConversationLocation 四臂（kind 判别），与上游联合一致
对话位置=_会话级对话位置|_回合级对话位置|_步骤级对话位置|_未解析对话位置#四臂联合

class 对话匹配(对话事件输入):#ConversationMatch
    """一条定义接受的事件，带着当前已解析 Location。"""
    role:Literal['start','update']#生命周期角色
    location:对话位置#已解析位置

#------------------------------ 视图节点与快照 ------------------------------

class 对话视图节点(TypedDict):#ConversationViewNode
    """业务定义返回的、与目标无关的身份。"""
    key:str#引擎上下文键
    kind:str#定义 kind
    id:str#定义局部身份
    target:str#视图目标
    data:Any#节点载荷

对话视图快照映射=dict#ConversationViewSnapshotMap；声明合并空映射

class 对话视图快照仓库(Protocol):#ConversationViewSnapshotStore
    """每个已登记视图目标最新快照的稳定读取器。"""

    def get(自身,目标):#按目标读取
        """读已登记视图目标的当前快照。

        @param 目标 - 已登记视图目标。
        @returns 其当前快照。
        """
        ...#协议槽

class 聊天对话视图节点(对话视图节点):#ChatConversationViewNode
    """业务定义直接产出的最终 Chat 渲染单元。"""
    target:Literal['chat']#固定聊天目标
    anchorSeq:int#锚点序号
    location:对话位置#已解析位置
    visibility:Literal['visible','hidden']#可见性

#------------------------------ 节点上下文与定义 ------------------------------

class 对话节点上下文(TypedDict):#ConversationNodeContext
    """一个已组装业务 Context 的不可变公开视图。"""
    key:str#引擎上下文键
    kind:str#定义 kind
    id:str#定义局部身份
    matches:list#已收集匹配（对话匹配）
    start:Any#可选开始匹配
    state:Any#可选业务状态
    current:Any#当前各目标节点（只读 Map 形）

class 对话前驱上下文(TypedDict):#ConversationPreviousContext
    """交给定义 start 函数的只读前驱。"""
    key:str#引擎上下文键
    kind:str#定义 kind
    id:str#定义局部身份
    startSeq:int#开始事件序号
    state:Any#只读状态
    matches:list#已收集匹配

class 对话上下文读取器(Protocol):#ConversationContextReader
    """求值 start 时可用的、严格向后的 Context 查找。"""

    def previous(自身,种类):#向前查找
        """找 `种类` 的活动 Context，取其开始序号小于当前开始事件的最大者。

        @param 种类 - 要查询的定义 kind。
        @returns 最近前驱；当前窗口没有则为 None。
        """
        ...#协议槽

class 对话节点定义(Protocol):#ConversationNodeDefinition
    """一台独立登记的、事件到节点的业务状态机。"""

    @property
    def kind(自身)->str:#定义 kind
        """本定义 kind。"""
        ...#协议槽

    @property
    def target(自身)->str|None:#可选视图目标
        """本定义独占的视图目标；仅状态的 Context 省略。"""
        ...#协议槽

    def match(自身,事件):#匹配事件
        """从一条事件抽出本定义的稳定业务身份。

        @param 事件 - 原始会话事件；此时没有 Context 或历史可访问。
        @returns 身份与生命周期角色；无关则 None。
        """
        ...#协议槽

    def start(自身,上下文,匹配,读取器):#创建状态
        """用唯一的开始 Match 创建 State。

        @param 上下文 - 当前已为该 Context 收集的完整证据。
        @param 匹配 - 开始 Match。
        @param 读取器 - 严格向后的只读 Context 查找。
        @returns 引擎采纳的 State。
        """
        ...#协议槽

    def update(自身,上下文,匹配):#应用更新
        """应用一条开始之后的更新 Match。

        @param 上下文 - 带着当前 State 的 Context。
        @param 匹配 - 按日志升序的更新 Match。
        @returns 引擎采纳的 State。
        """
        ...#协议槽

    def publication(自身,匹配):#可选发布节奏
        """为一条已接受 Match 选择发布节奏。

        @param 匹配 - 已接受 Match。
        @returns 请求的节奏；省略则默认 immediate。
        """
        ...#协议槽

    def buildLocationData(自身,上下文,作用域):#可选位置数据
        """为本定义发布某一 Location 相的只读业务值。

        引擎先对每个定义求 Step，再求 Turn，拥有替换/移除，
        并拒绝另一 Context 往同一 Location 键发布。

        @param 上下文 - 最新完整 Context。
        @param 作用域 - 当前正在物化的 Location 层级。
        @returns 当前 Location 值；尚不可用则为 None。
        """
        ...#协议槽

    def buildViewNode(自身,上下文):#可选视图节点
        """为本定义声明的视图目标物化一个最终节点。

        @param 上下文 - 最新完整 Context。
        @returns 最终节点；本 Context 当前不可见则为 None。
        """
        ...#协议槽

#------------------------------ 时间线与视图构建器 ------------------------------

class 对话时间线快照(TypedDict):#ConversationTimelineSnapshot
    """与视图节点并列发布的、引用稳定的 Turn/Step 事实。"""
    turnOrder:list#回合顺序
    turns:Any#回合号 → 位置（只读 Map 形）

class 对话视图构建器(Protocol):#ConversationViewBuilder
    """每个视图目标、按会话增量的构建器。"""

    @property
    def empty(自身):#空快照
        """空快照单例。"""
        ...#协议槽

    def replace(自身,输入):#全量替换
        """替换低频的、完整物化节点集。

        @param 输入 - 含 nodes 与 timeline。
        @returns 下一视图快照。
        """
        ...#协议槽

    def apply(自身,输入):#增量应用
        """只应用本事务中物化值已变的节点。

        @param 输入 - 含 upserts 与 timeline。
        @returns 下一视图快照。
        """
        ...#协议槽

class 对话视图定义(Protocol):#ConversationViewDefinition
    """登记贡献：为每个会话创建一台隔离的视图构建器。"""

    @property
    def target(自身)->str:#视图目标
        """视图目标名。"""
        ...#协议槽

    def create(自身):#创建构建器
        """返回一台新的、会话拥有的增量构建器。"""
        ...#协议槽
