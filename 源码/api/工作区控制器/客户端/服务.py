"""无 React 的 Client Workspace 服务与命令门面。"""
from ....依赖.cordis import 服务#Cordis 服务基类

__all__=[#仅中文公开名
    '工作区创建错误','工作区控制器','应用工作区服务',
]#公开面结束

class 工作区创建错误(Exception):
    """区分 Host 业务错误的结构化创建失败。"""

    def __init__(自身,远程失败):
        """记下 Host 业务或折叠后的载体失败。"""
        码=远程失败['code'] if isinstance(远程失败,dict) else getattr(远程失败,'code',None)#码
        消息=远程失败['message'] if isinstance(远程失败,dict) else getattr(远程失败,'message',None)#消息
        super().__init__('workspace create failed: '+str(码)+': '+str(消息))#文案
        自身.name='WorkspaceCreateError'#错误名
        自身.rpcError=远程失败#远程失败

class _可等待:
    """把同步结果包成带 等待() 的完成态，供 UI inject 面链式等待。"""

    def __init__(自身,值):
        """记下值。"""
        自身._值=值#结果

    def 等待(自身):
        """立即返回。"""
        return 自身._值#值

def _命令错误(操作,失败):
    """构造命令错误。"""
    码=失败['code'] if isinstance(失败,dict) else getattr(失败,'code',None)#码
    消息=失败['message'] if isinstance(失败,dict) else getattr(失败,'message',None)#消息
    return RuntimeError('workspace '+操作+' failed: '+str(码)+': '+str(消息))#错误

class 工作区控制器(服务):
    """拥有裸 Workspace 快照与仅 Workspace 的命令。"""

    def __init__(自身,上下文,模型):
        """登记 ctx.workspaces；模型为客户端工作区模型。"""
        super().__init__(上下文,'workspaces')#登记服务
        自身._模型=模型#模型
        自身.list=模型#模型即快照源

    def create(自身,输入):
        """把已有路径登记为 Workspace。输入含 path。"""
        结果=自身._模型.create(输入)#发远程创建
        if not 结果.get('ok'):#业务失败
            raise 工作区创建错误(结果['error'])#结构化
        return _可等待(结果['value']['workspace'])#视图

    def rename(自身,工作区标识,标题):
        """重命名 Workspace。"""
        结果=自身._模型.rename(工作区标识,标题)#发远程
        if not 结果.get('ok'):
            raise _命令错误('rename',结果['error'])#映射
        return _可等待(结果['value']['workspace'])#视图

    def delete(自身,工作区标识):
        """删除一份 Workspace 登记，不删除会话或文件。"""
        结果=自身._模型.delete(工作区标识)#发远程
        if not 结果.get('ok'):
            raise _命令错误('delete',结果['error'])#映射
        return _可等待(None)#完成

    def insertBefore(自身,工作区标识,锚点=None):
        """在 Host 登记顺序内移动 Workspace。"""
        结果=自身._模型.insertBefore(工作区标识,锚点)#发远程
        if not 结果.get('ok'):
            raise _命令错误('reorder',结果['error'])#映射
        return _可等待(None)#完成

    def archiveSession(自身,会话标识):
        """从 Workspace 分组表层归档一个会话。"""
        结果=自身._模型.archiveSession(会话标识)#发远程
        if not 结果.get('ok'):
            raise _命令错误('session archive',结果['error'])#映射
        return _可等待(None)#完成

    def insertSessionBefore(自身,工作区标识,会话标识,锚点=None):
        """在一个 Workspace 账本内移动会话。"""
        结果=自身._模型.insertSessionBefore(工作区标识,会话标识,锚点)#发远程
        if not 结果.get('ok'):
            raise _命令错误('move',结果['error'])#映射
        return _可等待(结果['value']['workspace'])#视图

def 应用工作区服务(上下文,模型):
    """安装 workspaces 服务面。"""
    return 工作区控制器(上下文,模型)#构造即登记
