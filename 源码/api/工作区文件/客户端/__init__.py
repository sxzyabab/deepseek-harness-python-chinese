"""浏览器半边：经 `remote.workspaceFiles` 的 `file` 资源提供方。

对齐上游 `workspace-files/src/client/index.ts`。公开面仅中文名。
`类型` 为协议面，`变更供给` 每 Session 共享一条宿主流，`提供方` 把供给与 `stat` 收成值流；
本模块只把它们挂到 `ctx.resources`。
"""
from .变更供给 import 变更供给#每 Session 扇出
from .提供方 import 创建文件资源提供方#file 提供方
from .类型 import 工作区文件参数字段#类型面
from .远程 import 工作区文件远程字段,工作区文件命名空间方法#Remote 切片

__all__=[#仅中文公开名
    '注入','应用',
    '变更供给','创建文件资源提供方',
    '工作区文件参数字段',
    '工作区文件远程字段','工作区文件命名空间方法',
]#公开面结束

注入=['resources','remote','remote.workspaceFiles']#硬依赖


def 应用(上下文):
    """登记 `file` 提供方；拆除时等待仍在关闭的 Session 流。"""
    供给=变更供给(上下文.remote)#扇出
    提供方=创建文件资源提供方(上下文.remote,供给)#建造

    def 寿命():
        """登记提供方；拆除时结算供给。"""
        拆除登记=上下文.resources.登记(提供方)#登记
        def 拆除():
            """先卸提供方，再等宿主流关闭。"""
            拆除登记()#卸登记
            供给.结算()#等关闭中
        return 拆除#拆除器

    上下文.副作用(寿命,'workspace-files: file resource provider')#效应


inject=注入#框架槽
apply=应用#框架槽
