"""Workspace 专用适配器，面向 Gateway 拥有的快照流生命周期。

对齐上游 `workspace-controller/src/client/index.ts`。公开面仅中文名。
安装 Client Workspace 状态、命令与可重连 follow 控制；UI inject 依赖 ctx.workspaces。
"""
from ...网关.流载体 import 远程流载体错误#载体错误
from ...网关.快照流 import 远程快照流#快照流
from .模型 import 客户端工作区模型#模型
from .服务 import 工作区创建错误,工作区控制器,应用工作区服务#服务

__all__=[#仅中文公开名
    '注入','应用','客户端工作区模型','工作区控制器','工作区创建错误',
    '创建工作区状态流','应用工作区服务',
]#公开面结束

注入=['remote','remote.workspace']#依赖远程与 workspace 命名空间

def _取工作区面(远程):
    """取 remote.workspace 命名空间。"""
    if hasattr(远程,'workspace'):#属性
        return 远程.workspace#面
    return 远程['workspace']#下标

def _有流工厂(远程):
    """远程是否暴露 $stream。"""
    return getattr(远程,'$stream',None) is not None or (isinstance(远程,dict) and '$stream' in 远程)#有

def _取流工厂(远程):
    """取 $stream 可调用。"""
    工厂=getattr(远程,'$stream',None)#属性
    if 工厂 is not None:#有
        return 工厂#返回
    return 远程['$stream']#下标

def _接受增量(接收端,帧):
    """分派 follow 增量帧。帧为 dict。"""
    类型=帧.get('type')#类型
    if 类型=='upsert':#合并行
        接收端.upsertView(帧['workspace'])#合并
        return#结束
    if 类型=='remove':#移除
        接收端.removeView(帧['workspaceId'])#移除
        return#结束
    if 类型=='order':#顺序
        接收端.replaceOrder(帧['workspaceIds'])#替换
        return#结束
    if 类型=='archived':#归档
        接收端.replaceArchived(帧['archivedSessionIds'])#替换
        return#结束
    raise RuntimeError('unreachable Workspace increment: '+repr(帧))#封闭联合兜底

def 创建工作区状态流(远程,选项):
    """创建可重连的 Workspace 状态流。

    选项：accept / failed / carrierFailed?。
    有 $stream 时返回远程快照流；否则直连 follow 迭代器句柄。
    """
    if not _有流工厂(远程):#回退
        return _直连状态流(远程,选项)#直连
    工作区面=_取工作区面(远程)#workspace
    流选项={
        'name':'Workspace state stream',
        'open':lambda 信号:工作区面.follow(信号),
        'ended':lambda 已接受:远程流载体错误('Workspace state stream ended without a terminal result') if 已接受 else RuntimeError('Workspace state stream ended before its opening snapshot'),
    }#流选项
    if 'carrierFailed' in 选项 and 选项['carrierFailed'] is not None:#有
        流选项['carrierFailed']=选项['carrierFailed']#带上
    底层=_取流工厂(远程)(流选项)#开监督流
    return 远程快照流(底层,{
        'name':'Workspace state stream',
        'isSnapshot':lambda 帧:帧.get('type')=='baseline',
        'replace':lambda 帧:选项['accept'].replaceBaseline(帧['value'] if isinstance(帧,dict) and 'value' in 帧 else 帧),
        'update':lambda 帧:_接受增量(选项['accept'],帧),
        'failed':选项['failed'],
    })#快照流

def _直连状态流(远程,选项):
    """无 $stream 时的直连 follow。"""
    状态={'closed':False}#状态
    def 启动(信号=None):
        """打开 follow 并投递帧。"""
        if 状态['closed']:#已拆
            return#空
        try:
            工作区面=_取工作区面(远程)#面
            跟随=工作区面.follow#方法
            for 帧 in 跟随(信号):#迭代
                if 状态['closed']:#已拆
                    break#停
                if 帧.get('type')=='baseline':#基线
                    选项['accept'].replaceBaseline(帧['value'])#替换
                else:#增量
                    _接受增量(选项['accept'],帧)#分派
        except BaseException as 错误:
            if 状态['closed']:#拆除中
                return#吞
            选项['failed'](错误)#失败
    def 拆除():
        """标记关闭。"""
        状态['closed']=True#关
    return {'启动':启动,'start':启动,'拆除':拆除,'dispose':拆除,'name':'Workspace state stream'}#句柄

def 应用(上下文):
    """安装 Client Workspace 状态、命令与可重连 follow 控制。"""
    远程=上下文.remote#远程根
    模型=客户端工作区模型(_取工作区面(远程))#模型
    工作区控制器(上下文,模型)#安装 ctx.workspaces
    控制选项={
        'accept':模型,#接收端
        'carrierFailed':lambda 错误:模型.handleCarrierFailure(),#载体失败
        'failed':lambda 错误:模型.handleStreamFailure(错误),#终端失败
    }#选项
    控制=创建工作区状态流(远程,控制选项)#状态流
    控制['start']() if isinstance(控制,dict) else 控制.start()#启动
    def 拆除():
        """释放流。"""
        if isinstance(控制,dict):#直连句柄
            控制['dispose']()#拆
        else:#快照流
            控制.dispose()#拆
    上下文.副作用(拆除,'workspace-controller.client.control')#拆除

inject=注入#框架槽
apply=应用#框架槽
