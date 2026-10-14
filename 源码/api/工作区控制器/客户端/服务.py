'无 React 的 Client Workspace 服务与命令门面'
from ....依赖.cordis import 服务#Cordis 服务基类
from ....基础设施.js特性 import PromiseEX as 期约
from ..异常 import 工作区创建错误,工作区归档错误,失败说明#本包异常

__all__=[#仅中文公开名
    '工作区创建错误','工作区归档错误','工作区控制器','应用工作区服务',
]#公开面结束

def _命令错误(操作,失败):
    '构造命令错误。文案去掉绝对路径，码和原说明保留。'
    码=失败['code'] if isinstance(失败,dict) else getattr(失败,'code',None)#码
    消息=失败['message'] if isinstance(失败,dict) else getattr(失败,'message',None)#消息
    return RuntimeError('workspace '+操作+' failed: '+str(码)+': '+失败说明(消息))#错误

def _可见失败(错误):
    '把拒绝值收成调用方能读的异常，原因链保留。'
    if isinstance(错误,BaseException):
        包装=RuntimeError(失败说明(错误))
        包装.__cause__=错误
        return 包装
    if isinstance(错误,dict):
        文=失败说明(错误['message'] if 'message' in 错误 else 错误)
        if 文=='':
            文=str(错误['code'] if 'code' in 错误 else 'Error')
        return RuntimeError(文)
    return RuntimeError(失败说明(错误) or 'Error')

def _接上(产出,成功,失败):
    '期约走然后；已是值则直接成功。同步失败交给失败回调。'
    try:
        if hasattr(产出,'然后'):
            产出.然后(成功,失败)
            return
        成功(产出)
    except BaseException as 错误:
        失败(错误)

class 工作区控制器(服务):
    '拥有裸 Workspace 快照与仅 Workspace 的命令'

    def __init__(自身,上下文,模型):
        '登记 ctx.workspaces；模型为客户端工作区模型'
        super().__init__(上下文,'workspaces')#登记服务
        自身._模型=模型#模型
        自身.list=模型#模型即快照源

    def _业务期约(自身,产出,成功值,失败值):
        '把模型结果收成期约。成功交出值，失败拒绝并保留原因。'
        落定=期约()
        def 已返回(结果):
            if not isinstance(结果,dict) or not 结果.get('ok'):
                错=结果['error'] if isinstance(结果,dict) and 'error' in 结果 else 结果
                落定.拒绝(失败值(错))
                return
            落定.解决(成功值(结果))
        _接上(产出,已返回,lambda 错误:落定.拒绝(_可见失败(错误)))
        return 落定

    def create(自身,输入):
        '把已有路径登记为 Workspace。输入含 path。返回期约，解决值是工作区视图。'
        return 自身._业务期约(
            自身._模型.create(输入),
            lambda 结果:结果['value']['workspace'],
            工作区创建错误,
        )

    def initializeDefault(自身,信号=None):
        '初始化或复用默认工作区。返回期约，解决值是视图或 None。不创建会话。'
        return 自身._业务期约(
            自身._模型.initializeDefault(信号),
            lambda 结果:None if 结果.get('value') is None else 结果['value']['workspace'],
            工作区创建错误,
        )

    def rename(自身,工作区标识,标题):
        '重命名 Workspace。返回期约，解决值是工作区视图。'
        return 自身._业务期约(
            自身._模型.rename(工作区标识,标题),
            lambda 结果:结果['value']['workspace'],
            lambda 失败:_命令错误('rename',失败),
        )

    def delete(自身,工作区标识):
        '删除一份 Workspace 登记，不删除会话或文件。返回期约。'
        return 自身._业务期约(
            自身._模型.delete(工作区标识),
            lambda 结果:None,
            lambda 失败:_命令错误('delete',失败),
        )

    def insertBefore(自身,工作区标识,锚点=None):
        '在 Host 登记顺序内移动 Workspace。返回期约。'
        return 自身._业务期约(
            自身._模型.insertBefore(工作区标识,锚点),
            lambda 结果:None,
            lambda 失败:_命令错误('reorder',失败),
        )

    def archiveSession(自身,会话标识,选项=None):
        '从 Workspace 分组表层归档一个会话。返回期约。'
        return 自身._业务期约(
            自身._模型.archiveSession(会话标识,选项),
            lambda 结果:None,
            工作区归档错误,
        )

    def unarchiveSession(自身,会话标识):
        '解除归档。返回期约。'
        return 自身._业务期约(
            自身._模型.unarchiveSession(会话标识),
            lambda 结果:None,
            lambda 失败:_命令错误('session unarchive',失败),
        )

    def pinSession(自身,会话标识):
        '钉住会话。返回期约。'
        return 自身._业务期约(
            自身._模型.pinSession(会话标识),
            lambda 结果:None,
            lambda 失败:_命令错误('session pin',失败),
        )

    def unpinSession(自身,会话标识):
        '去掉钉住。返回期约。'
        return 自身._业务期约(
            自身._模型.unpinSession(会话标识),
            lambda 结果:None,
            lambda 失败:_命令错误('session unpin',失败),
        )

    def insertSessionBefore(自身,工作区标识,会话标识,锚点=None):
        '在一个 Workspace 账本内移动会话。返回期约，解决值是工作区视图。'
        return 自身._业务期约(
            自身._模型.insertSessionBefore(工作区标识,会话标识,锚点),
            lambda 结果:结果['value']['workspace'],
            lambda 失败:_命令错误('move',失败),
        )

    def listDirectory(自身,路径=None,信号=None):
        '列一层目录。返回期约，解决值是目录列表。'
        return 自身._目录期约(lambda:自身.ctx.remote.directoryPicker.list(路径,信号))

    def createDirectory(自身,路径,名称):
        '创建单段子目录。返回期约，解决值是新路径。'
        return 自身._目录期约(lambda:自身.ctx.remote.directoryPicker.createDirectory(路径,名称))

    def _目录期约(自身,开工):
        '解开目录远程结果。失败保留去掉路径后的说明。'
        落定=期约()
        def 已返回(结果):
            if isinstance(结果,dict) and 'ok' in 结果:
                if not 结果.get('ok'):
                    落定.拒绝(_可见失败(结果['error'] if 'error' in 结果 else 结果))
                    return
                落定.解决(结果.get('value'))
                return
            落定.解决(结果)
        try:
            产出=开工()
        except BaseException as 错误:
            落定.拒绝(_可见失败(错误))
            return 落定
        _接上(产出,已返回,lambda 错误:落定.拒绝(_可见失败(错误)))
        return 落定

def 应用工作区服务(上下文,模型):
    '安装 workspaces 服务面'
    return 工作区控制器(上下文,模型)#构造即登记
