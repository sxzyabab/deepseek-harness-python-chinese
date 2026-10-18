'无 React 的客户端工作区服务。命令直接返回解决后的值'
from ....依赖.cordis.服务 import 服务#服务基类
from ..异常 import 工作区创建错误,工作区归档错误,命令错误#本包失败

__all__=['工作区控制器']


class 工作区控制器(服务):
    '拥有工作区快照和只针对工作区的命令'
    def __init__(自身,上下文,模型):
        '以 workspaces 登记。list 就是模型的快照面'
        super().__init__(上下文,'workspaces')#服务名
        自身.模型=模型#远程投影
        自身.list=模型#快照与订阅

    def create(自身,输入):
        '把已有路径登记为工作区。输入含 path。返回工作区视图'
        结果=自身.模型.create(输入)#远程结果
        if not 结果['ok']:#宿主拒绝
            raise 工作区创建错误(结果['error'])#创建失败
        return 结果['value']['workspace']#工作区视图

    def initializeDefault(自身,信号=None):
        '准备或复用默认工作区。不具备条件时返回空。失败按创建失败抛出'
        结果=自身.模型.initializeDefault(信号)#远程结果
        if not 结果['ok']:#准备失败
            raise 工作区创建错误(结果['error'])#创建失败
        if 结果['value'] is None:#不具备条件
            return None#空
        return 结果['value']['workspace']#工作区视图

    def rename(自身,工作区号,标题):
        '重命名工作区。返回改名后的工作区视图'
        结果=自身.模型.rename(工作区号,标题)#远程结果
        if not 结果['ok']:#拒绝
            raise 命令错误('rename',结果['error'])#命令失败
        return 结果['value']['workspace']#工作区视图

    def delete(自身,工作区号):
        '删除一份工作区登记，不删除会话或文件'
        结果=自身.模型.delete(工作区号)#远程结果
        if not 结果['ok']:#拒绝
            raise 命令错误('delete',结果['error'])#命令失败

    def insertBefore(自身,工作区号,锚=None):
        '在宿主登记顺序里移动工作区。省略锚则追加到末尾'
        结果=自身.模型.insertBefore(工作区号,锚)#远程结果
        if not 结果['ok']:#拒绝
            raise 命令错误('reorder',结果['error'])#命令失败

    def archiveSession(自身,会话号,选项=None):
        '从分组面归档会话。stopActivity 为真时宿主先停运行中的工作，否则仍在运行会拒绝'
        if 选项 is None:#没给选项
            选项={}#空
        结果=自身.模型.archiveSession(会话号,选项)#远程结果
        if not 结果['ok']:#拒绝
            raise 工作区归档错误(结果['error'])#归档失败

    def unarchiveSession(自身,会话号):
        '把会话从归档列表里拿出来'
        结果=自身.模型.unarchiveSession(会话号)#远程结果
        if not 结果['ok']:#拒绝
            raise 命令错误('session unarchive',结果['error'])#命令失败

    def pinSession(自身,会话号):
        '把会话钉到未钉会话前面'
        结果=自身.模型.pinSession(会话号)#远程结果
        if not 结果['ok']:#拒绝
            raise 命令错误('session pin',结果['error'])#命令失败

    def unpinSession(自身,会话号):
        '去掉会话的钉，不改已保存的会话顺序'
        结果=自身.模型.unpinSession(会话号)#远程结果
        if not 结果['ok']:#拒绝
            raise 命令错误('session unpin',结果['error'])#命令失败

    def insertSessionBefore(自身,工作区号,会话号,锚=None):
        '在一个工作区账本里移动会话。返回变更后的工作区视图'
        结果=自身.模型.insertSessionBefore(工作区号,会话号,锚)#远程结果
        if not 结果['ok']:#拒绝
            raise 命令错误('move',结果['error'])#命令失败
        return 结果['value']['workspace']#工作区视图
