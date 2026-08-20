"""无 React 的工作区实体，带着客户端本地物化生命周期。

对齐上游 `runtime/src/client/workspaces/workspace.ts`。公开面仅中文名。
"""
import asyncio#物化任务
import re#路径分段
from ..客户端.会话.通知器 import 通知器#批通知（路B权威）

__all__=['工作区','折叠传输错误','取字段']#仅中文公开名

def 折叠传输错误(错误):#载体抛错 → 业务错误支
    """对齐 apiproxy transportError：internal + 空 details。"""
    if isinstance(错误,BaseException):#异常
        消息=str(错误)#取 message
    else:#其它
        消息=str(错误)#String()
    return {'ok':False,'error':{'code':'internal','message':消息,'details':{}}}#失败支

def 意图名(输入):#从路径取展示名
    """末段；空则原路径。"""
    修剪=re.sub(r'[\\/]+$','',输入['path'])#去掉尾部分隔符
    段们=re.split(r'[\\/]',修剪)#分段
    return 段们[-1] if 段们 and 段们[-1] else 输入['path']#末段

def 取字段(对象,键,缺省=None):#读字段
    """映射或属性。"""
    if 对象 is None:#空
        return 缺省#缺
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class 工作区:#工作区实体
    """可观察的工作区对象，身份在宿主物化后仍存活。"""

    def __init__(自身,接口,来源):#按来源播种
        """本地创建输入，或已有宿主工作区视图。"""
        自身._接口=接口#共享线客户端
        自身._视图=None#已物化宿主视图
        自身._意图=None#本地创建意图
        自身._物化=None#进行中的物化
        if 取字段(来源,'workspaceId') is not None:#已有宿主视图
            自身._视图=来源#直接采纳
        else:#本地意图
            自身._意图={#记下输入
                'input':来源,#创建载荷
                'snapshot':{'name':意图名(来源),'phase':'ready'},#就绪意图
            }#意图结束
        自身._通知器=通知器(自身._建快照写入)#脏时重建
        自身._快照缓存=自身._建快照()#初始缓存

    def _建快照写入(自身):#重建写入缓存
        """通知器回调：写入快照缓存。"""
        自身._快照缓存=自身._建快照()#写入

    def 物化(自身):#开始物化
        """经宿主创建 API 物化本本地工作区；已物化返回 None。"""
        if 自身._物化 is not None:#共享进行中
            return 自身._物化#进行中
        意图=自身._意图#当前意图
        if 意图 is None:#已物化
            return None#无事
        意图['snapshot']={'name':意图['snapshot']['name'],'phase':'creating'}#标创建中
        自身._通知器.立刻通知()#立刻通知
        任务箱=[None]#闭包箱，供 finally 认身份
        async def 包装():#跑完清进行中
            try:#物化
                return await 自身._完成物化(意图)#宿主结果
            finally:#无论成败
                if 自身._物化 is 任务箱[0]:#只清自己这一趟
                    自身._物化=None#清空
        try:#有运行中事件环
            任务箱[0]=asyncio.get_running_loop().create_task(包装())#可共享 Task
        except RuntimeError:#无环
            任务箱[0]=包装()#裸协程，调用方 await
        自身._物化=任务箱[0]#记下进行中
        return 任务箱[0]#共享承诺

    async def _完成物化(自身,意图):#真正打创建 API
        """宿主结果。"""
        try:#打创建
            响应=await 自身._接口.workspace.create(意图['input'])#创建
            结果=取字段(响应,'result',响应)#取出 result
        except Exception as 错误:#传输失败
            结果=折叠传输错误(错误)#折成错误分支
        if 自身._意图 is not 意图:#意图已被替换
            return 结果#只返回
        if 取字段(结果,'ok'):#创建成功
            自身.采纳(取字段(取字段(结果,'value'),'workspace'))#采纳返回视图
        else:#业务失败
            错=取字段(结果,'error') or {}#错误
            意图['snapshot']={#回到就绪并带错误
                'name':意图['snapshot']['name'],#保留展示名
                'phase':'ready',#可再试
                'error':str(取字段(错,'code',''))+': '+str(取字段(错,'message','')),#错误文案
            }#失败快照
            自身._通知器.标脏()#标脏
        return 结果#折叠结果

    def 采纳(自身,视图):#采纳宿主视图
        """已有物化身份只接受同一工作区 id 的更新。"""
        if 自身._视图 is not None and 取字段(自身._视图,'workspaceId')!=取字段(视图,'workspaceId'):#身份冲突
            raise Exception('cannot adopt a different Workspace id')#拒绝换 id
        自身._视图=视图#写入视图
        自身._意图=None#意图已兑现
        自身._通知器.标脏()#标脏

    def 订阅(自身,监听):#登记监听器
        """订阅工作区快照失效。"""
        return 自身._通知器.订阅(监听)#交给通知器

    def 取快照(自身):#读快照
        """冲掉挂起通知后读缓存的工作区快照。"""
        自身._通知器.确保新鲜()#脏则先重建
        return 自身._快照缓存#返回缓存

    def _建快照(自身):#拼对外快照
        """视图或意图。"""
        意图快照=取字段(自身._意图,'snapshot') if 自身._意图 is not None else None#意图
        return {'view':自身._视图,'intent':意图快照}#快照
