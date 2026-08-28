"""跨域会话端口：兄弟域（工作区）消费的约定面。

对齐上游 `runtime/src/client/contract/sessions-port.ts`。公开面仅中文名。
会话域在结构上满足本面；加宽本面就是显式加宽跨域依赖。

依赖未迁：SessionId / WorkspaceId（api-remotes）、完整 ObservableSnapshot 图；
本叶以鸭式 str / dict / 可观察快照约定表达上述类型能承载的入参与返回。
"""
from typing import Protocol,TypedDict,NotRequired,Literal#协议与结构类型

__all__=[#仅中文公开名
    '会话端口摘要键',
    '会话端口列表键',
    '会话端口方法',
    '会话端口摘要',
    '会话端口列表',
    '会话端口',
]#公开面结束

#------------------------------ 方法名表（稳定动词清单） ------------------------------

会话端口摘要键=(#端口摘要行字段
    'id',#会话 id
    'blank',#是否空白
    'cwd',#可选工作目录
    'updatedAt',#更新时间
)#摘要键结束

会话端口列表键=(#端口列表字段
    'ids',#顺序 id
    'byId',#按 id 的行
    'current',#当前会话
    'phase',#pending / ready
)#列表键结束

会话端口方法=(#注入给兄弟域的方法
    'list',#可观察列表快照
    'create',#创建会话
    'open',#打开会话
    'clear',#清除选择
)#方法结束

#------------------------------ TypedDict / Protocol（对齐接口体） ------------------------------

class 会话端口摘要(TypedDict):#SessionsPortSummary
    """兄弟域读取的会话列表行事实：新近度、空白复用资格、以及其 cwd 规范。"""

    id:str#会话 id
    blank:bool#是否空白
    updatedAt:float#更新时间
    cwd:NotRequired[str]#可选工作目录

class 会话端口列表(TypedDict):#SessionsPortList
    """兄弟域读取的会话列表事实：就绪、选择、以及行映射。"""

    ids:list#顺序 id（SessionId 序列）
    byId:dict#按 id 的行（SessionId → 会话端口摘要）
    current:str|None#当前会话；无选择则为 None
    phase:Literal['pending','ready']#列表阶段

class 会话端口(Protocol):#SessionsPort
    """注入给兄弟域的会话服务面。"""

    @property
    def list(自身):#列表快照
        """可观察列表快照（只读面；写入留在会话域内）。"""
        ...#协议槽

    async def create(自身,选项):#创建会话
        """在宿主上创建一条会话。

        @param 选项 - 含 workspaceId 的目标工作区。
        @returns 新会话 id。
        """
        ...#协议槽

    def open(自身,会话id):#打开会话
        """把一条会话选为当前。

        @param 会话id - 会话 id（必须已在列表仓库里）。
        """
        ...#协议槽

    def clear(自身):#清除选择
        """清掉当前选择，进入无会话视图状态。"""
        ...#协议槽
