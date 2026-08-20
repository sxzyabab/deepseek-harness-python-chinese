"""对外的工作区服务面 — `ctx.workspaces` 暴露内容。

对齐上游 `runtime/src/client/contract/workspaces.ts`。公开面仅中文名。
线泵入口留在具体类上；加宽本面就是显式加宽功能对工作区域能做什么。

依赖未迁：DirectoryListing / WorkspaceView / WorkspaceId / SessionId（api-remotes）、
WorkspaceListState（workspaces/service）、完整 ObservableSnapshot / AbortSignal 图；
本叶以鸭式 object / dict / 可调用表达上述类型能承载的通道行为。
"""
from typing import Protocol#协议钉住鸭子面

__all__=[#仅中文公开名
    '工作区面方法',
    '工作区面',
]#公开面结束

#------------------------------ 方法名表（稳定动词清单） ------------------------------

工作区面方法=(#IWorkspaces 方法名
    'list',#列表快照
    'connectWorkspace',#连接工作区
    'startSession',#开始会话
    'create',#创建工作区
    'pickDirectory',#选目录
    'listDirectory',#列目录
    'createDirectory',#创建子目录
    'openPath',#打开路径
    'rename',#重命名
    'delete',#删除
    'insertBefore',#插入到某工作区前
    'insertSessionBefore',#插入会话
    'archiveSession',#归档会话
)#方法结束

#------------------------------ Protocol（对齐 IWorkspaces） ------------------------------

class 工作区面(Protocol):#IWorkspaces
    """作为 `ctx.workspaces` 注入的工作区服务面。"""

    @property
    def list(自身):#列表快照
        """useWorkspaces 标准源（只读面 — 写入留在域内）。"""
        ...#协议槽

    async def connectWorkspace(自身,工作区id):#连接工作区
        """把一个工作区接到其可复用或新造的空白会话。

        @param 工作区id - 目标工作区。
        @returns 接上的会话 id。
        """
        ...#协议槽

    def startSession(自身,工作区id=None):#开始会话
        """新会话流程：连接显式的、当前会话的、或最近的工作区并打开结果会话；失败浮在会话列表状态上。

        @param 工作区id - 显式目标；省略则继承当前会话的工作区，再回退到新近度投影。
        """
        ...#协议槽

    async def create(自身,输入):#创建工作区
        """把一条已有路径登记成工作区。

        @param 输入 - 宿主创建载荷（含 path）。
        @returns 创建或幂等解析到的工作区视图。
        """
        ...#协议槽

    async def pickDirectory(自身):#选目录
        """打开宿主的原生目录选择器。

        @returns 选中的路径；用户取消则为 None。
        """
        ...#协议槽

    async def listDirectory(自身,路径=None,信号=None):#列目录
        """经宿主 browse 能力列出一层目录。

        @param 路径 - 要列出的绝对目录；缺省列出宿主主目录。
        @param 信号 - 调用方取代本次请求时中止线请求（以及宿主扫描）。
        @returns 该层列表，带面包屑祖先。
        """
        ...#协议槽

    async def createDirectory(自身,路径,名称):#创建子目录
        """经宿主 browse 能力创建一个子目录。

        @param 路径 - 已存在的绝对父目录。
        @param 名称 - 单个非空白路径段。
        @returns 创建出的目录的绝对路径。
        """
        ...#协议槽

    async def openPath(自身,路径):#打开路径
        """用宿主操作系统的默认应用打开一条文件系统路径。

        @param 路径 - 绝对路径或宿主可解析路径。
        """
        ...#协议槽

    async def rename(自身,工作区id,标题):#重命名
        """重命名一个工作区。

        @param 工作区id - 目标工作区。
        @param 标题 - 新显示标题。
        @returns 更新后的工作区视图。
        """
        ...#协议槽

    async def delete(自身,工作区id):#删除
        """删除一个工作区（其会话回退到未入账组）。

        @param 工作区id - 目标工作区。
        """
        ...#协议槽

    async def insertBefore(自身,工作区id,前工作区id=None):#插入到某工作区前
        """在注册表显示顺序里移动一个工作区。

        @param 工作区id - 要移动的工作区。
        @param 前工作区id - 锚点工作区；省略则追加到末尾。
        """
        ...#协议槽

    async def insertSessionBefore(自身,工作区id,会话id,前会话id=None):#插入会话
        """在一个工作区的有序列表内/之间移动一条已入账会话。

        @param 工作区id - 目标工作区。
        @param 会话id - 要移动的已入账会话。
        @param 前会话id - 插到其前的已入账锚点；省略则追加。
        @returns 更新后的工作区视图。
        """
        ...#协议槽

    async def archiveSession(自身,会话id):#归档会话
        """把一条会话归档进注册表全局集（对分组面隐藏；会话日志与入账槽仍在）。

        归档当前会话会清掉选择，进入新会话视图状态。
        @param 会话id - 要归档的会话。
        """
        ...#协议槽
