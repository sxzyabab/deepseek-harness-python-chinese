'工作区变更。创建和重命名串行，避免检查之后、写入之前被另一路插进来'
import threading#串行锁
from ...类型化远程调用.协议 import 取远程错误#已经是线路失败则原样抛
from ...工作区.工作区 import 工作区标识#品牌化 id
from ...工作区.工作区.异常 import (
    工作区移动无效错误,#会话或锚不在账本里
    工作区未知会话错误,#会话不存在
    工作区顺序无效错误,#工作区或锚不在登记顺序里
    工作区活动会话错误,#会话还有运行中的工作
    工作区已归档会话钉住错误,#已归档会话不能钉住
)
from .异常 import 远程错误,错误消息,工作区未找到#本包失败
from .提要 import 工作区视图#投影

__all__=['工作区命令']


class 工作区命令:
    '对权威注册表执行工作区变更'

    def __init__(自身,上下文):
        '记下注册表所在的上下文'
        自身.ctx=上下文#宿主上下文
        自身.操作锁=threading.Lock()#创建与重命名串行

    def create(自身,请求):
        '在已有目录上创建或幂等解析工作区。请求含 path'

        def 操作():
            '解析已有路径，没有则创建'
            try:#注册表拒绝或系统拒绝都折成 invalid-path
                已有=自身.ctx.workspaceRegistry.resolveByPath(请求['path'])#按路径
                if 已有 is not None:#已经登记
                    return {'workspace':工作区视图(已有),'created':False}#未新建
                工作区=自身.ctx.workspaceRegistry.create(请求['path'])#新建
                return {'workspace':工作区视图(工作区),'created':True}#已新建
            except Exception as 错误:#折成线路失败
                if 取远程错误(错误) is not None:#已经是线路失败
                    raise#原样
                if isinstance(错误,BaseException) and len(错误.args)>0 and isinstance(错误.args[0],str):#有消息
                    说明=错误.args[0]#消息
                else:#其它
                    说明=错误消息(错误)#收成字符串
                raise 远程错误(
                    'workspace/invalid-path',
                    'cannot create a Workspace at "'+str(请求['path'])+'": '+说明,
                    {'path':请求['path']},
                    原因=错误,
                )#路径不能作为工作区

        return 自身.入队(操作)#串行

    def rename(自身,请求):
        '把工作区改成不重复的非空白标题。请求含 workspaceId 与 title'
        标题=str(请求['title']).strip()#去掉两端空白
        if 标题=='':#空白标题
            raise 远程错误('gateway/bad-request','Workspace rename requires a non-blank title',{})#拒绝

        def 操作():
            '占住标题后再写'
            工作区=自身.要求工作区(请求['workspaceId'])#必须存在
            if 标题!=工作区.title:#确实要改
                for 候选 in 自身.ctx.workspaceRegistry.list():#查重
                    if 候选.id!=工作区.id and 候选.title==标题:#别的工作区已用这个名字
                        raise 远程错误(
                            'workspace/name-conflict',
                            "Workspace name '"+标题+"' is already in use",
                            {'name':标题},
                        )#冲突
                工作区.setTitle(标题)#写入
            return {'workspace':工作区视图(工作区)}#整行

        return 自身.入队(操作)#串行

    def delete(自身,请求):
        '去掉一份工作区登记，不删目录和会话。请求含 workspaceId'

        def 操作():
            '登记不存在则 not-found'
            if not 自身.ctx.workspaceRegistry.delete(工作区标识(请求['workspaceId'])):#没有这份登记
                raise 工作区未找到(请求['workspaceId'])#拒绝
            return {'deleted':True}#回执

        return 自身.入队(操作)#串行

    def insertBefore(自身,请求):
        '在耐久顺序里移动一份工作区。请求含 workspaceId，锚 beforeWorkspaceId 可省略'
        try:#非法顺序折成 not-found
            锚=请求['beforeWorkspaceId'] if 'beforeWorkspaceId' in 请求 else None#锚
            标识列=自身.ctx.workspaceRegistry.insertBefore(
                工作区标识(请求['workspaceId']),
                None if 锚 is None else 工作区标识(锚),
            )#新顺序
            return {'workspaceIds':list(标识列)}#完整顺序
        except 工作区顺序无效错误 as 错误:#点名了未登记的工作区
            raise 工作区未找到(错误.workspaceId)#not-found

    def insertSessionBefore(自身,请求):
        '在一份工作区的手工顺序里移动会话。请求含 workspaceId、sessionId，锚可省略'
        工作区=自身.要求工作区(请求['workspaceId'])#必须存在
        锚=请求['beforeSessionId'] if 'beforeSessionId' in 请求 else None#锚
        try:#账本里没有会话或锚
            工作区.insertSessionBefore(请求['sessionId'],锚)#移动
        except 工作区移动无效错误 as 错误:#非法移动
            详情={
                'workspaceId':请求['workspaceId'],#工作区
                'sessionId':请求['sessionId'],#会话
            }#详情
            if 锚 is not None:#有锚
                详情['beforeSessionId']=锚#锚
            raise 远程错误('workspace/move-invalid',str(错误),详情,原因=错误)#线路失败
        return {'workspace':工作区视图(工作区)}#整行

    def archiveSession(自身,请求):
        '把已知会话放进全局归档集。stopActivity 为真时先让提供方停掉运行中的工作'
        选项={'stopActivity':True} if 请求.get('stopActivity') is True else {}#是否先停
        try:#未知会话或仍在运行
            自身.ctx.workspaceRegistry.archiveSession(请求['sessionId'],选项)#归档
        except 工作区未知会话错误 as 错误:#不认识
            raise 远程错误('session/not-found',str(错误),{'sessionId':请求['sessionId']},原因=错误)#找不到
        except 工作区活动会话错误 as 错误:#还有工作在跑
            raise 远程错误(
                'workspace/session-active',
                str(错误),
                {'sessionId':请求['sessionId'],'activity':错误.activity},
                原因=错误,
            )#拒绝归档
        return {'archivedSessionIds':list(自身.ctx.workspaceRegistry.archivedSessionIds)}#完整归档集

    def unarchiveSession(自身,请求):
        '从全局归档集去掉会话。本来就没归档也不是错误'
        自身.ctx.workspaceRegistry.unarchiveSession(请求['sessionId'])#还原
        return {'archivedSessionIds':list(自身.ctx.workspaceRegistry.archivedSessionIds)}#完整归档集

    def pinSession(自身,请求):
        '把已知且未归档的会话放进全局钉住集，最近钉的在前'
        try:#未知或已归档
            自身.ctx.workspaceRegistry.pinSession(请求['sessionId'])#钉住
        except 工作区未知会话错误 as 错误:#不认识
            raise 远程错误('session/not-found',str(错误),{'sessionId':请求['sessionId']},原因=错误)#找不到
        except 工作区已归档会话钉住错误 as 错误:#已归档
            raise 远程错误('gateway/bad-request',str(错误),{},原因=错误)#拒绝
        return {'pinnedSessionIds':list(自身.ctx.workspaceRegistry.pinnedSessionIds)}#完整钉住集

    def unpinSession(自身,请求):
        '从全局钉住集去掉会话。本来就没钉也不是错误'
        自身.ctx.workspaceRegistry.unpinSession(请求['sessionId'])#去掉
        return {'pinnedSessionIds':list(自身.ctx.workspaceRegistry.pinnedSessionIds)}#完整钉住集

    def 要求工作区(自身,标识):
        '按 id 取工作区。没有则抛 not-found'
        工作区=自身.ctx.workspaceRegistry.get(工作区标识(标识))#查找
        if 工作区 is None:#没有
            raise 工作区未找到(标识)#拒绝
        return 工作区#实体

    def 入队(自身,操作):
        '等前一次创建或重命名结束后再跑。操作是无参函数'
        with 自身.操作锁:#串行
            return 操作()#本次结果
