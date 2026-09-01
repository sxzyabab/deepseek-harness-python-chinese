"""工作区命令实现与稳定 Remote 失败映射。

对齐上游 `workspace-controller/src/commands.ts`。公开面仅中文名。
"""
import threading#串行锁
from .工具 import 取字段,解开,远程错误,远程错误消息#辅助
from .提要 import 工作区视图#投影

__all__=['工作区命令','工作区未找到']#仅中文公开名

def 工作区未找到(工作区标识):#构造 not-found
    """稳定 workspace/not-found 失败。"""
    return 远程错误('workspace/not-found','Workspace "'+str(工作区标识)+'" not found',{'workspaceId':工作区标识})#失败

class 工作区命令:#工作区变更实现
    """对权威注册表执行工作区变更。"""

    def __init__(自身,上下文,工作区标识函数):#构造
        """保存上下文与品牌化函数。"""
        自身._上下文=上下文#Cordis
        自身._锁=threading.Lock()#串行锁
        自身._工作区标识=工作区标识函数#品牌化

    def create(自身,请求):#创建或解析
        """在目录上创建或幂等解析工作区。"""
        with 自身._锁:#串行
            try:#解析或创建
                已有=解开(自身._上下文.workspaceRegistry.resolveByPath(取字段(请求,'path')))#按路径
                if 已有 is not None:#已存在
                    return {'workspace':工作区视图(已有),'created':False}#未创建
                工作区=解开(自身._上下文.workspaceRegistry.create(取字段(请求,'path')))#新建
                return {'workspace':工作区视图(工作区),'created':True}#已创建
            except Exception as 错误:#失败
                raise 远程错误('workspace/invalid-path','cannot create a Workspace at "'+str(取字段(请求,'path'))+'": '+远程错误消息(错误),{'path':取字段(请求,'path')},cause=错误)#映射

    def rename(自身,请求):#重命名
        """重命名工作区。"""
        标题=str(取字段(请求,'title') or '').strip()#去空白
        if 标题=='':#空白
            raise 远程错误('gateway/bad-request','Workspace rename requires a non-blank title',{})#拒绝
        with 自身._锁:#串行
            工作区=自身._要求工作区(取字段(请求,'workspaceId'))#必须存在
            if 标题!=取字段(工作区,'title'):#真要改
                for 候选 in 自身._上下文.workspaceRegistry.list():#查重
                    if 取字段(候选,'id')!=取字段(工作区,'id') and 取字段(候选,'title')==标题:#冲突
                        raise 远程错误('workspace/name-conflict',"Workspace name '"+标题+"' is already in use",{'name':标题})#冲突
                解开(工作区.setTitle(标题))#写入
            return {'workspace':工作区视图(工作区)}#返回

    def delete(自身,请求):#删除
        """移除注册，不删目录与会话。"""
        with 自身._锁:#串行
            if not 解开(自身._上下文.workspaceRegistry.delete(自身._工作区标识(取字段(请求,'workspaceId')))):#未找到
                raise 工作区未找到(取字段(请求,'workspaceId'))#拒绝
            return {'deleted':True}#确认

    def insertBefore(自身,请求):#调整工作区顺序
        """移动工作区顺序。"""
        try:#调用注册表
            标识们=解开(自身._上下文.workspaceRegistry.insertBefore(
                自身._工作区标识(取字段(请求,'workspaceId')),
                None if 取字段(请求,'beforeWorkspaceId') is None else 自身._工作区标识(取字段(请求,'beforeWorkspaceId')),
            ))#插入
            return {'workspaceIds':list(标识们)}#顺序
        except Exception as 错误:#失败
            工作区标识=getattr(错误,'workspaceId',None)#顺序错误携带 id
            if 工作区标识 is not None:#映射为 not-found
                raise 工作区未找到(工作区标识)#转
            raise#原样

    def insertSessionBefore(自身,请求):#调整会话顺序
        """移动工作区内会话顺序。"""
        工作区=自身._要求工作区(取字段(请求,'workspaceId'))#必须存在
        try:#移动
            解开(工作区.insertSessionBefore(取字段(请求,'sessionId'),取字段(请求,'beforeSessionId')))#调用
        except Exception as 错误:#失败
            详情={'workspaceId':取字段(请求,'workspaceId'),'sessionId':取字段(请求,'sessionId')}#详情
            if 取字段(请求,'beforeSessionId') is not None:#有锚点
                详情['beforeSessionId']=取字段(请求,'beforeSessionId')#锚点
            raise 远程错误('workspace/move-invalid',远程错误消息(错误),详情,cause=错误)#映射
        return {'workspace':工作区视图(工作区)}#返回

    def archiveSession(自身,请求):#归档会话
        """把已知会话加入全局归档集。"""
        try:#归档
            解开(自身._上下文.workspaceRegistry.archiveSession(取字段(请求,'sessionId')))#调用
        except Exception as 错误:#失败
            raise 远程错误('session/not-found',远程错误消息(错误),{'sessionId':取字段(请求,'sessionId')},cause=错误)#映射
        return {'archivedSessionIds':list(自身._上下文.workspaceRegistry.archivedSessionIds or [])}#归档集

    def _要求工作区(自身,工作区标识):#要求存在
        """取工作区或抛 not-found。"""
        工作区=自身._上下文.workspaceRegistry.get(自身._工作区标识(工作区标识))#查找
        if 工作区 is None:#缺失
            raise 工作区未找到(工作区标识)#拒绝
        return 工作区#实体
