"""宿主工作区远程拥有者：显式命令与重连安全状态。"""
from ...typert.协议 import 远程服务,远程 as _远程
from .命令 import 工作区命令
from .提要 import 工作区提要,工作区视图
from .目录选择器 import 目录选择器控制器
from .远程错误与中止 import 已中止

__all__=['包名','名称','依赖','应用','默认','工作区控制器','目录选择器控制器','工作区视图']

包名='@deepseek-ai/dsh-api-workspace-controller'
名称='workspace-controller'
依赖=['typert','workspaceRegistry']

def _工作区标识(值):#品牌化工作区 id
    """尽力把字符串收成工作区标识。"""
    return 值#标识品牌化由 workspace 包拥有

def _工作区记录解析(值):#解析工作区记录
    """解析域记录；完整校验由 workspace 包拥有。"""
    return 值 if isinstance(值,dict) else {}

def _工作区域状态解析(值):#解析域全局状态
    """解析 workspace 域全局状态。"""
    return 值 if isinstance(值,dict) else {}

class 工作区控制器(远程服务):
    """生成远程 workspace 命名空间的宿主服务。"""
    inject=['typert','workspaceRegistry']

    def __init__(自身,上下文):#构造
        """挂载命令、提要与子目录选择器插件。"""
        super().__init__(上下文,'workspaceController',{'namespace':'workspace'})#注册
        自身._命令=工作区命令(上下文,_工作区标识)#命令
        自身._提要=工作区提要(上下文,_工作区记录解析,_工作区域状态解析,_工作区标识)#提要
        上下文.启动插件(目录选择器控制器)#子插件

    @_远程('create')
    def create(自身,请求):#创建工作区
        """创建或幂等解析目录上的工作区。"""
        return 自身._命令.create(请求)#委托

    @_远程('rename')
    def rename(自身,请求):#重命名
        """重命名工作区。"""
        return 自身._命令.rename(请求)#委托

    @_远程('delete')
    def delete(自身,请求):#删除
        """移除工作区注册。"""
        return 自身._命令.delete(请求)#委托

    @_远程('insertBefore')
    def insertBefore(自身,请求):#调序
        """移动工作区显示顺序。"""
        return 自身._命令.insertBefore(请求)#委托

    @_远程('insertSessionBefore')
    def insertSessionBefore(自身,请求):#调会话序
        """移动工作区内会话顺序。"""
        return 自身._命令.insertSessionBefore(请求)#委托

    @_远程('archiveSession')
    def archiveSession(自身,请求):#归档会话
        """从分组面隐藏会话。"""
        return 自身._命令.archiveSession(请求)#委托

    @_远程('follow')
    def follow(自身,信号):#流式 follow
        """产出基线后有序增量。"""
        if 已中止(信号):#已取消
            return#空
        yield from 自身._提要.follow(信号)#委托提要

def 应用(上下文):
    """挂载工作区 Remote 拥有者。"""
    工作区控制器(上下文)#构造即登记

默认=应用
name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
default=默认#框架槽
