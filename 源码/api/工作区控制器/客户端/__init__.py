"""工作区客户端适配器：面向网关拥有的快照流生命周期。

安装客户端工作区状态、命令与可重连 follow 控制；界面依赖 workspaces 服务。
"""
from ...网关.流载体 import 远程流载体错误
from ...网关.快照流 import 远程快照流
from .模型 import 客户端工作区模型
from .服务 import 工作区创建错误,工作区控制器,应用工作区服务

__all__=[
    '依赖','应用','客户端工作区模型','工作区控制器','工作区创建错误',
    '创建工作区状态流','应用工作区服务',
]

依赖=['remote','remote.workspace']

def _有流工厂(远程):
    """远程是否暴露 $stream 工厂。"""
    return getattr(远程,'$stream',None) is not None

def _取流工厂(远程):
    """取 $stream 可调用。"""
    return getattr(远程,'$stream')

def _接受增量(接收端,帧):
    """按 type 分派 follow 增量帧；帧为 dict，未识别类型视为封闭联合失败。"""
    类型=帧['type'] if 'type' in 帧 else None
    if 类型=='upsert':
        接收端.upsertView(帧['workspace'])
        return
    if 类型=='remove':
        接收端.removeView(帧['workspaceId'])
        return
    if 类型=='order':
        接收端.replaceOrder(帧['workspaceIds'])
        return
    if 类型=='archived':
        接收端.replaceArchived(帧['archivedSessionIds'])
        return
    raise RuntimeError('unreachable Workspace increment: '+repr(帧))

def 创建工作区状态流(远程,选项):
    """创建可重连的工作区状态流。

    选项键：accept / failed / carrierFailed?。
    有 $stream 时返回远程快照流；否则直连 follow 迭代器句柄。
    """
    if not _有流工厂(远程):
        return _直连状态流(远程,选项)
    工作区面=远程.workspace
    流选项={
        'name':'Workspace state stream',
        'open':lambda 信号:工作区面.follow(信号),
        'ended':lambda 已接受:远程流载体错误('Workspace state stream ended without a terminal result') if 已接受 else RuntimeError('Workspace state stream ended before its opening snapshot'),
    }
    if 'carrierFailed' in 选项 and 选项['carrierFailed'] is not None:
        流选项['carrierFailed']=选项['carrierFailed']
    底层=_取流工厂(远程)(流选项)
    return 远程快照流(底层,{
        'name':'Workspace state stream',
        'isSnapshot':lambda 帧:'type' in 帧 and 帧['type']=='baseline',
        'replace':lambda 帧:选项['accept'].replaceBaseline(帧['value'] if 'value' in 帧 else 帧),
        'update':lambda 帧:_接受增量(选项['accept'],帧),
        'failed':选项['failed'],
    })

class _直连状态流句柄:
    """无 $stream 时的直连 follow 句柄。"""

    def __init__(自身,远程,选项):
        """记下远程与接收端。"""
        自身._远程=远程
        自身._选项=选项
        自身._已关闭=False
        自身.name='Workspace state stream'

    def start(自身,信号=None):
        """打开 follow 并投递基线/增量帧。"""
        if 自身._已关闭:
            return
        try:
            跟随=自身._远程.workspace.follow
            for 帧 in 跟随(信号):
                if 自身._已关闭:
                    break
                if 'type' in 帧 and 帧['type']=='baseline':
                    自身._选项['accept'].replaceBaseline(帧['value'])
                else:
                    _接受增量(自身._选项['accept'],帧)
        except BaseException as 错误:
            if 自身._已关闭:
                return
            自身._选项['failed'](错误)

    def dispose(自身):
        """标记关闭，阻止后续帧投递。"""
        自身._已关闭=True

def _直连状态流(远程,选项):
    """无 $stream 时的直连 follow；拆除后吞掉迟到回调。"""
    return _直连状态流句柄(远程,选项)

def 应用(上下文):
    """安装客户端工作区状态、命令与可重连 follow 控制。"""
    远程=上下文.remote
    模型=客户端工作区模型(远程.workspace)
    工作区控制器(上下文,模型)#挂 workspaces 服务
    控制选项={
        'accept':模型,
        'carrierFailed':lambda 错误:模型.handleCarrierFailure(),
        'failed':lambda 错误:模型.handleStreamFailure(错误),
    }
    控制=创建工作区状态流(远程,控制选项)
    控制.start()
    def 拆除():
        """释放状态流。"""
        控制.dispose()
    上下文.副作用(拆除,'workspace-controller.client.control')

inject=依赖#框架槽
apply=应用#框架槽
