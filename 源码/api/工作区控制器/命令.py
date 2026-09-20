"""工作区命令实现与稳定 Remote 失败映射。"""
import threading#串行锁
from .远程错误与中止 import 远程错误,远程错误消息#远程错误
from .提要 import 工作区视图#投影

__all__=['工作区命令','工作区未找到']#仅中文公开名

def 工作区未找到(工作区标识):#构造 not-found
    """稳定 workspace/not-found 失败。"""
    return 远程错误('workspace/not-found','Workspace "'+str(工作区标识)+'" not found',{'workspaceId':工作区标识})

class 工作区命令:#工作区变更实现
    """对权威注册表执行工作区变更。"""

    def __init__(自身,上下文,工作区标识函数):#构造
        """保存上下文与品牌化函数。"""
        自身._上下文=上下文#Cordis
        自身._锁=threading.Lock()#串行锁
        自身._工作区标识=工作区标识函数#品牌化

    def create(自身,请求):#创建或解析
        """在目录上创建或幂等解析工作区。请求为线协议 dict。"""
        with 自身._锁:#串行
            try:#解析或创建
                已有=自身._上下文.workspaceRegistry.resolveByPath(请求['path'])#按路径
                if 已有 is not None:#已存在
                    return {'workspace':工作区视图(已有),'created':False}#未创建
                工作区=自身._上下文.workspaceRegistry.create(请求['path'])#新建
                return {'workspace':工作区视图(工作区),'created':True}#已创建
            except OSError as 错误:
                raise 远程错误('workspace/invalid-path','cannot create a Workspace at "'+str(请求['path'])+'": '+远程错误消息(错误),{'path':请求['path']},原因=错误)#映射
            except ValueError as 错误:
                raise 远程错误('workspace/invalid-path','cannot create a Workspace at "'+str(请求['path'])+'": '+远程错误消息(错误),{'path':请求['path']},原因=错误)#映射

    def rename(自身,请求):#重命名
        """重命名工作区。"""
        标题=str(请求['title'] if 'title' in 请求 and 请求['title'] is not None else '').strip()#去空白
        if 标题=='':#空白
            raise 远程错误('gateway/bad-request','Workspace rename requires a non-blank title',{})#拒绝
        with 自身._锁:#串行
            工作区=自身._要求工作区(请求['workspaceId'])#必须存在
            if 标题!=工作区.title:#真要改
                for 候选 in 自身._上下文.workspaceRegistry.list():#查重
                    if 候选.id!=工作区.id and 候选.title==标题:#冲突
                        raise 远程错误('workspace/name-conflict',"Workspace name '"+标题+"' is already in use",{'name':标题})#冲突
                工作区.setTitle(标题)#写入
            return {'workspace':工作区视图(工作区)}#返回

    def delete(自身,请求):#删除
        """移除注册，不删目录与会话。"""
        with 自身._锁:#串行
            if not 自身._上下文.workspaceRegistry.delete(自身._工作区标识(请求['workspaceId'])):#未找到
                raise 工作区未找到(请求['workspaceId'])#拒绝
            return {'deleted':True}#确认

    def insertBefore(自身,请求):#调整工作区顺序
        """移动工作区顺序。"""
        try:#调用注册表
            锚=请求['beforeWorkspaceId'] if 'beforeWorkspaceId' in 请求 else None#锚点
            标识列表=自身._上下文.workspaceRegistry.insertBefore(
                自身._工作区标识(请求['workspaceId']),
                None if 锚 is None else 自身._工作区标识(锚),
            )#插入
            return {'workspaceIds':list(标识列表)}#顺序
        except 远程错误:#已是 Remote
            raise#原样
        except ValueError as 错误:
            工作区标识=错误.workspaceId if hasattr(错误,'workspaceId') else None#顺序错误携带 id
            if 工作区标识 is not None:#映射为 not-found
                raise 工作区未找到(工作区标识)#转
            raise#原样

    def insertSessionBefore(自身,请求):#调整会话顺序
        """移动工作区内会话顺序。"""
        工作区=自身._要求工作区(请求['workspaceId'])#必须存在
        锚=请求['beforeSessionId'] if 'beforeSessionId' in 请求 else None#锚点
        try:#移动
            工作区.insertSessionBefore(请求['sessionId'],锚)#调用
        except ValueError as 错误:
            详情={'workspaceId':请求['workspaceId'],'sessionId':请求['sessionId']}#详情
            if 锚 is not None:#有锚点
                详情['beforeSessionId']=锚#锚点
            raise 远程错误('workspace/move-invalid',远程错误消息(错误),详情,原因=错误)#映射
        return {'workspace':工作区视图(工作区)}#返回

    def archiveSession(自身,请求):#归档会话
        """把已知会话加入全局归档集。"""
        try:#归档
            自身._上下文.workspaceRegistry.archiveSession(请求['sessionId'])#调用
        except ValueError as 错误:
            raise 远程错误('session/not-found',远程错误消息(错误),{'sessionId':请求['sessionId']},原因=错误)#映射
        归档=自身._上下文.workspaceRegistry.archivedSessionIds#归档集
        return {'archivedSessionIds':list(归档 if 归档 is not None else [])}#归档集

    def _要求工作区(自身,工作区标识):#要求存在
        """取工作区或抛 not-found。"""
        工作区=自身._上下文.workspaceRegistry.get(自身._工作区标识(工作区标识))
        if 工作区 is None:#缺失
            raise 工作区未找到(工作区标识)#拒绝
        return 工作区#实体
