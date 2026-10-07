'浏览器半边：经远程 workspaceFiles 登记 `file` 资源提供方'
from .变更供给 import 变更供给#每会话扇出
from .提供方 import 创建文件资源提供方#file 提供方
from .类型 import 工作区文件参数字段#协议字段
from .远程 import 工作区文件远程字段,工作区文件命名空间方法#远程切片

__all__=[
    '依赖','应用',
    '变更供给','创建文件资源提供方',
    '工作区文件参数字段',
    '工作区文件远程字段','工作区文件命名空间方法',
]

依赖=['resources','remote','remote.workspaceFiles']


def 应用(上下文):
    '登记 `file` 资源提供方；拆除时等待仍在关闭的会话流'
    供给=变更供给(上下文.remote)
    提供方=创建文件资源提供方(上下文.remote,供给)

    def 寿命():
        '登记提供方；拆除时结算供给'
        拆除登记=上下文.resources.登记(提供方)
        def 拆除():
            '先卸提供方，再等宿主流关闭，返回流全部关闭后解决的期约'
            拆除登记()
            return 供给.结算()
        return 拆除

    上下文.副作用(寿命,'workspace-files: file resource provider')


inject=依赖#框架槽
apply=应用#框架槽
