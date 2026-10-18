'浏览器半边：经远程 workspaceFiles 登记 file 资源提供方'
from . import 变更供给,提供方,类型,远程#同目录模块，导入时执行它们的顶层
from .变更供给 import 变更供给 as 变更供给类#供给类
from .提供方 import 创建文件资源提供方#file 提供方

__all__=['依赖','应用','变更供给','提供方','类型','远程']#导出模块，不转发类

依赖=['resources','remote','remote.workspaceFiles']#资源、远程面、工作区文件命名空间


def 应用(上下文,配置=None):
    '登记 file 提供方。拆除时先卸提供方，再等仍在关闭的宿主流'
    供给=变更供给类(上下文.remote)#全部会话共用一条供给
    方=创建文件资源提供方(上下文.remote,供给)#file 协议

    def 寿命():
        '挂上提供方，交出拆除器'
        拆除登记=上下文.resources.登记(方)#登记

        def 拆除():
            '卸下提供方并等到流关闭'
            拆除登记()#卸
            供给.结算()#等关闭中的流
        return 拆除#拆除器

    上下文.副作用(寿命,'workspace-files: file resource provider')#本插件寿命


inject=依赖#框架槽
apply=应用#框架槽
