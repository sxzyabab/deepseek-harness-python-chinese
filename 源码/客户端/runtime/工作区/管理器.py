"""工作区基线、增量帧与一元动作的拥有者。

对齐上游 `runtime/src/client/workspaces/manager.ts`。公开面仅中文名。
"""
import asyncio#刷新任务
from datetime import datetime#updatedAt 比较
from ..会话.通知器 import 通知器#批通知（再导出路B）
from .工作区 import 工作区,折叠传输错误,取字段#实体与折叠

__all__=['工作区管理器','工作区列表阶段']#仅中文公开名

工作区列表阶段=('pending','ready')#列表阶段

def 解析时刻(文本):#ISO 时刻 → 可比较数
    """对齐 Date.parse；失败为负无穷。"""
    if 文本 is None:#空
        return float('-inf')#最旧
    try:#解析
        return datetime.fromisoformat(str(文本).replace('Z','+00:00')).timestamp()#时间戳
    except Exception:#畸形
        return float('-inf')#最旧

def 视图升插(条目们,工作区视图):#视图 upsert
    """已知 id 保留位置；新创建进最前。"""
    下标=next((i for i,项 in enumerate(条目们) if 取字段(项,'workspaceId')==取字段(工作区视图,'workspaceId')),-1)#已有
    if 下标==-1:#没有
        return [工作区视图]+list(条目们)#插最前
    return [工作区视图 if i==下标 else 项 for i,项 in enumerate(条目们)]#换掉该位

def 重放增量(条目们,增量):#重放增量
    """原地 upsert，或丢掉被删 id，或按序重排。"""
    种类=增量['type']#增量种类
    if 种类=='upsert':#插入或更新
        return 视图升插(条目们,增量['workspace'])#upsert
    if 种类=='remove':#删除
        return [项 for 项 in 条目们 if 取字段(项,'workspaceId')!=增量['workspaceId']]#滤掉
    位次={标识:i for i,标识 in enumerate(增量['workspaceIds'])}#id → 位次
    return sorted(条目们,key=lambda 项:位次.get(取字段(项,'workspaceId'),10**18))#未知排最后

def 插到锚点前(标识们,标识,锚点=None):#本地乐观重排
    """把已知 id 移到可选锚点前；未知保持不变。"""
    if 标识 not in 标识们 or (锚点 is not None and 锚点 not in 标识们) or 锚点==标识:#守卫
        return list(标识们)#原样
    去掉=[候选 for 候选 in 标识们 if 候选!=标识]#先拿掉
    点=len(去掉) if 锚点 is None else 去掉.index(锚点)#插入点
    return 去掉[:点]+[标识]+去掉[点:]#插回去

def asyncio_模组():#取 asyncio
    """惰性导入 asyncio。"""
    return __import__('asyncio')#模块

def asyncio_创建任务(协程):#无环时吞掉（对齐 void refresh）
    """fire-and-forget 刷新。"""
    try:#有环
        asyncio_模组().get_running_loop().create_task(协程)#挂任务
    except RuntimeError:#无环
        pass#宿主稍后驱动

class 工作区管理器:#工作区管理器
    """由一份列表基线与变更帧 upsert 驱动的工作区对象簇。"""

    def __init__(自身,接口):#绑定 API
        """共享线客户端。"""
        自身._接口=接口#API
        自身._条目们=[]#活着的工作区对象
        自身._视图源=None#视图缓存对应的 items 引用
        自身._视图缓存=()#已物化视图缓存
        自身._归档会话们=()#归档集
        自身._状态='idle'#拉取状态
        自身._阶段='pending'#到达阶段
        自身._错误=None#最近错误
        自身._在飞=None#进行中的刷新
        自身._刷新帧=None#刷新期间到达的增量
        自身._归档覆盖刷新=False#归档是否新于在飞基线
        自身._顺序请求世代=0#本地重排世代
        自身._顺序帧世代=0#顺序帧世代
        自身._已提交顺序=[]#已提交顺序
        自身._已删集=set()#删除墓碑
        自身._通知器=通知器(自身._建快照写入)#脏时重建
        自身._快照缓存=自身._建快照()#初始缓存

    def _建快照写入(自身):#重建写入缓存
        """通知器回调。"""
        自身._快照缓存=自身._建快照()#写入

    async def 刷新(自身):#拉基线
        """从 workspace.list 刷新；共享进行中。"""
        if 自身._在飞 is not None:#共享进行中
            return await 自身._在飞#等待同一趟
        自身._状态='loading'#标加载
        自身._错误=None#清错误
        帧们=[]#本趟收集的增量
        自身._刷新帧=帧们#挂上收集器
        自身._通知器.标脏()#标脏
        async def 一趟():#开一趟刷新
            try:#打列表
                响应=await 自身._接口.workspace.list({})#列表 RPC
                结果=取字段(响应,'result',响应)#取出 result
                if 取字段(结果,'ok'):#成功
                    条目们=list(取字段(取字段(结果,'value'),'items') or [])#宿主行
                    条目们=[项 for 项 in 条目们 if 取字段(项,'workspaceId') not in 自身._已删集]#滤墓碑
                    for 增量 in 帧们:#重放期间增量
                        条目们=重放增量(条目们,增量)#重放
                    自身._安装视图们(条目们)#安装对象簇
                    if not 自身._归档覆盖刷新:#基线归档未过期
                        自身._安装归档(取字段(取字段(结果,'value'),'archivedSessionIds') or [])#装归档
                    自身._状态='idle'#回到空闲
                    自身._阶段='ready'#到达完成
                else:#业务失败
                    自身._状态='error'#标错误
                    自身._错误=取字段(结果,'error')#记下错误
            except Exception as 错误:#传输失败
                自身._状态='error'#标错误
                折叠=折叠传输错误(错误)#折成错误分支
                自身._错误=None if 取字段(折叠,'ok') else 取字段(折叠,'error')#记下错误
            finally:#无论成败
                自身._刷新帧=None#清收集器
                自身._归档覆盖刷新=False#清覆盖位
                自身._在飞=None#清进行中
                自身._通知器.标脏()#标脏
        try:#有运行中事件环
            自身._在飞=asyncio.get_running_loop().create_task(一趟())#可共享 Task
        except RuntimeError:#无环
            自身._在飞=一趟()#裸协程
        return await 自身._在飞#等待

    async def 创建(自身,输入):#创建工作区
        """创建或解析真实工作区，发布返回快照。"""
        对象=工作区(自身._接口,输入)#本地意图对象
        完成=对象.物化()#开始物化
        if 完成 is None:#本地必须能物化
            raise Exception('a local Workspace must be materializable')#失败
        结果=await 完成#等宿主
        if 取字段(结果,'ok'):#成功
            自身._升插(取字段(取字段(结果,'value'),'workspace'),对象)#upsert 并保留身份
        return 结果#线结果

    async def 重命名(自身,工作区标识,标题):#重命名
        """重命名后发布返回快照。"""
        响应=await 自身._接口.workspace.rename({'workspaceId':工作区标识,'title':标题})#RPC
        结果=取字段(响应,'result',响应)#结果
        if 取字段(结果,'ok'):#成功
            自身._升插(取字段(取字段(结果,'value'),'workspace'))#upsert
        return 结果#线结果

    async def 删除(自身,工作区标识):#删除
        """删除登记并从本地投影拿掉。"""
        响应=await 自身._接口.workspace.delete({'workspaceId':工作区标识})#RPC
        结果=取字段(响应,'result',响应)#结果
        if 取字段(结果,'ok'):#成功
            自身._移除(工作区标识,True)#立刻移除
        return 结果#线结果

    async def 插到之前(自身,工作区标识,锚点工作区标识=None):#插到某工作区前
        """移动工作区并安装返回的完整顺序。"""
        自身._顺序请求世代+=1#本请求世代
        请求世代=自身._顺序请求世代#钉住
        帧世代=自身._顺序帧世代#出发时帧世代
        本地顺序=[取字段(项,'workspaceId') for 项 in 自身._条目视图们()]#当前本地顺序
        自身._安装顺序(插到锚点前(本地顺序,工作区标识,锚点工作区标识))#乐观安装
        try:#打重排
            载荷={'workspaceId':工作区标识}#必填
            if 锚点工作区标识 is not None:#可选锚点
                载荷['beforeWorkspaceId']=锚点工作区标识#写入
            响应=await 自身._接口.workspace.insertBefore(载荷)#一元
            结果=取字段(响应,'result',响应)#结果
        except Exception as 错误:#传输失败
            if 请求世代==自身._顺序请求世代 and 帧世代==自身._顺序帧世代:#仍最新
                自身._安装顺序(自身._已提交顺序)#回滚
            raise 错误#继续抛
        if 取字段(结果,'ok') and 请求世代==自身._顺序请求世代 and 帧世代==自身._顺序帧世代:#成功且最新
            自身._安装顺序(取字段(取字段(结果,'value'),'workspaceIds') or [],True)#安装并记提交
        elif (not 取字段(结果,'ok')) and 请求世代==自身._顺序请求世代 and 帧世代==自身._顺序帧世代:#失败且最新
            自身._安装顺序(自身._已提交顺序)#回滚
        return 结果#线结果

    async def 插会话到之前(自身,工作区标识,会话标识,锚点会话标识=None):#插会话
        """在工作区手动顺序里移动会话。"""
        载荷={'workspaceId':工作区标识,'sessionId':会话标识}#必填
        if 锚点会话标识 is not None:#可选锚点
            载荷['beforeSessionId']=锚点会话标识#写入
        响应=await 自身._接口.workspace.insertSessionBefore(载荷)#RPC
        结果=取字段(响应,'result',响应)#结果
        if 取字段(结果,'ok'):#成功
            自身._升插(取字段(取字段(结果,'value'),'workspace'))#upsert
        return 结果#线结果

    async def 归档会话(自身,会话标识):#归档会话
        """归档进注册表全局集并安装返回全集。"""
        响应=await 自身._接口.workspace.archiveSession({'sessionId':会话标识})#RPC
        结果=取字段(响应,'result',响应)#结果
        if 取字段(结果,'ok'):#成功
            自身._安装归档(取字段(取字段(结果,'value'),'archivedSessionIds') or [])#安装
        return 结果#线结果

    def 处理宿主信封(自身,信封):#派发宿主帧
        """非工作区帧忽略。"""
        载荷=取字段(信封,'payload')#载荷
        种类=取字段(载荷,'type')#帧类型
        if 种类=='host/workspace-changed':#变更
            自身._升插(取字段(载荷,'workspace'))#upsert
        elif 种类=='host/workspace-removed':#删除
            自身._移除(取字段(载荷,'workspaceId'))#移除
        elif 种类=='host/workspace-order-changed':#顺序变更
            自身._顺序帧世代+=1#抬帧世代
            自身._安装顺序(取字段(载荷,'workspaceIds') or [],True)#安装并记提交
        elif 种类=='host/archived-sessions-changed':#归档变更
            自身._安装归档(取字段(载荷,'archivedSessionIds') or [])#安装全集

    def 处理已连接(自身):#重连
        """每个连接世代之后重新拉基线。"""
        try:#有环
            asyncio.get_running_loop().create_task(自身.刷新())#再拉列表
        except RuntimeError:#无环
            pass#宿主稍后驱动

    def 订阅(自身,监听):#登记监听器
        """订阅工作区快照失效。"""
        return 自身._通知器.订阅(监听)#交给通知器

    def 取快照(自身):#读快照
        """冲掉挂起通知后读缓存。"""
        自身._通知器.确保新鲜()#脏则先重建
        return 自身._快照缓存#返回缓存

    def _建快照(自身):#拼对外快照
        """列表快照。"""
        return {#快照
            'items':自身._条目视图们(),#已物化行
            'archivedSessionIds':自身._归档会话们,#归档集
            'state':自身._状态,#拉取状态
            'phase':自身._阶段,#到达阶段
            'error':自身._错误,#最近错误
        }#结束

    def _安装归档(自身,归档会话们):#安装归档集
        """成员真正变了才替换。"""
        if 自身._刷新帧 is not None:#在飞刷新
            自身._归档覆盖刷新=True#覆盖基线归档
        归档=tuple(归档会话们)#拷一份
        if len(归档)==len(自身._归档会话们) and all(归档[i]==自身._归档会话们[i] for i in range(len(归档))):#相同
            return#不动
        自身._归档会话们=归档#写入
        自身._通知器.标脏()#标脏

    def _安装顺序(自身,工作区标识们,已提交=False):#安装顺序
        """重排已知工作区对象。"""
        if 已提交:#宿主提交
            if 自身._刷新帧 is not None:#刷新期间
                自身._刷新帧.append({'type':'order','workspaceIds':list(工作区标识们)})#记下增量
            自身._已提交顺序=list(工作区标识们)#记下已提交
        位次={标识:i for i,标识 in enumerate(工作区标识们)}#id → 位次
        def 位次键(对象):#排序键
            视图=取字段(对象.取快照(),'view')#视图
            标识=取字段(视图,'workspaceId') if 视图 is not None else None#id
            return 位次.get(标识,10**18) if 标识 is not None else 10**18#未知排最后
        新条目=sorted(自身._条目们,key=位次键)#按位次排
        if all(新条目[i] is 自身._条目们[i] for i in range(len(新条目))) and len(新条目)==len(自身._条目们):#未变
            return#不动
        自身._条目们=新条目#写入
        自身._通知器.标脏()#标脏

    def _升插(自身,视图,身份=None):#插入或更新
        """upsert 宿主视图，可选保留本地对象。"""
        标识=取字段(视图,'workspaceId')#id
        if 标识 in 自身._已删集:#墓碑
            return#挡住复活
        if 自身._刷新帧 is not None:#刷新期间
            自身._刷新帧.append({'type':'upsert','workspace':视图})#记下增量
        下标=next((i for i,项 in enumerate(自身._条目们) if 取字段(取字段(项.取快照(),'view'),'workspaceId')==标识),-1)#已有
        已装=None if 下标==-1 else 取字段(自身._条目们[下标].取快照(),'view')#已安装视图
        if 已装 is not None and 解析时刻(取字段(视图,'updatedAt'))<解析时刻(取字段(已装,'updatedAt')):#更旧
            return#拒
        if 标识 not in 自身._已提交顺序:#尚未进已提交顺序
            自身._已提交顺序=[标识]+自身._已提交顺序#新行排最前
        if 身份 is not None:#保留本地身份
            if 下标==-1:#尚无行
                自身._条目们=[身份]+自身._条目们#插到最前
            else:#换掉该位
                自身._条目们=[身份 if i==下标 else 项 for i,项 in enumerate(自身._条目们)]#替换
        elif 下标==-1:#没有本地身份且是新行
            自身._条目们=[工作区(自身._接口,视图)]+自身._条目们#造对象插最前
        else:#已有行
            自身._条目们[下标].采纳(视图)#采纳新视图
            自身._条目们=list(自身._条目们)#换数组身份以便通知
        自身._通知器.标脏()#标脏

    def _移除(自身,工作区标识,直接=False):#移除
        """幂等移除并留墓碑。"""
        if 自身._刷新帧 is not None:#刷新期间
            自身._刷新帧.append({'type':'remove','workspaceId':工作区标识})#记下增量
        自身._已删集.add(工作区标识)#立墓碑
        自身._已提交顺序=[标识 for 标识 in 自身._已提交顺序 if 标识!=工作区标识]#拿掉
        新条目=[项 for 项 in 自身._条目们 if 取字段(取字段(项.取快照(),'view'),'workspaceId')!=工作区标识]#过滤
        if len(新条目)==len(自身._条目们):#本地本来就没有
            if 直接:#一元路径
                自身._通知器.立刻通知()#立刻通知
            return#无需改
        自身._条目们=新条目#写入
        if 直接:#一元路径
            自身._通知器.立刻通知()#立刻通知
        else:#帧路径
            自身._通知器.标脏()#批通知

    def _安装视图们(自身,视图们):#按基线安装对象簇
        """复用或新建，按基线顺序。"""
        已有={}#已有对象按 id
        for 对象 in 自身._条目们:#现有
            视图=取字段(对象.取快照(),'view')#当前视图
            if 视图 is not None:#已物化
                已有[取字段(视图,'workspaceId')]=对象#记下
        已装={}#本趟安装结果
        for 视图 in 视图们:#基线每一行
            标识=取字段(视图,'workspaceId')#id
            if 标识 in 已装:#本趟已见
                已装[标识].采纳(视图)#后到的覆盖
                continue#下一行
            对象=已有.get(标识) or 工作区(自身._接口,视图)#复用或新建
            对象.采纳(视图)#采纳本行
            已装[标识]=对象#记下
        自身._条目们=list(已装.values())#按基线顺序（dict 保序）
        自身._已提交顺序=[取字段(视图,'workspaceId') for 视图 in 视图们]#基线即已提交

    def _条目视图们(自身):#已物化视图列表
        """items 引用未变则用缓存。"""
        if 自身._视图源 is 自身._条目们:#引用未变
            return 自身._视图缓存#缓存
        自身._视图源=自身._条目们#记下当前引用
        视图们=[]#展成视图
        for 对象 in 自身._条目们:#逐个
            视图=取字段(对象.取快照(),'view')#当前视图
            if 视图 is not None:#已物化
                视图们.append(视图)#收入
        自身._视图缓存=tuple(视图们)#缓存
        return 自身._视图缓存#返回
