"""WorkspaceRuntime：把工作区对象管理器投影给 UI 消费方。

对齐上游 `runtime/src/client/workspaces/service.ts`。公开面仅中文名。
"""
import warnings#初始选择失败诊断
from ..约定.存储 import 创建快照存储#快照存储工厂
from .工作区 import 取字段#字段读取
from .管理器 import 工作区管理器#对象层

__all__=['工作区运行时','工作区创建错误','目录浏览错误','最近工作区']#仅中文公开名

class 工作区创建错误(Exception):#创建失败
    """结构化的创建失败，供 UI 流程区分宿主业务错误。"""

    def __init__(自身,rpc错误):#带上 RPC 错误
        """拼消息并钉死名字。"""
        码=取字段(rpc错误,'code','')#码
        消息=取字段(rpc错误,'message','')#消息
        super().__init__('workspace create failed: '+str(码)+': '+str(消息))#拼消息
        自身.rpcError=rpc错误#RPC 错误
        自身.name='WorkspaceCreateError'#固定错误名

class 目录浏览错误(Exception):#浏览失败
    """结构化的浏览失败，以便目录浏览器按宿主业务码分支。"""

    def __init__(自身,rpc错误):#带上 RPC 错误
        """拼消息并钉死名字。"""
        码=取字段(rpc错误,'code','')#码
        消息=取字段(rpc错误,'message','')#消息
        super().__init__('directory browse failed: '+str(码)+': '+str(消息))#拼消息
        自身.rpcError=rpc错误#RPC 错误
        自身.name='DirectoryBrowseError'#固定错误名

def 最近工作区(工作区们,会话按标识):#最近活动工作区
    """稳定平局跟随宿主工作区顺序。"""
    胜者=None#当前胜者
    胜者时间=float('-inf')#胜者时间
    for 工作区视图 in 工作区们:#按宿主顺序
        最新=float('-inf')#本工作区最新会话
        for 会话标识 in (取字段(工作区视图,'sessionIds') or []):#已入账会话
            会话=会话按标识.get(会话标识) if hasattr(会话按标识,'get') else 会话按标识[会话标识] if 会话标识 in 会话按标识 else None#行
            if 会话 is not None:#有行
                最新=max(最新,取字段(会话,'updatedAt',0) or 0)#取更新时间
        if 最新==float('-inf'):#没有会话
            创建=取字段(工作区视图,'createdAt')#创建时间
            try:#解析
                from datetime import datetime#时刻
                最新=datetime.fromisoformat(str(创建).replace('Z','+00:00')).timestamp()*1000#毫秒近似
            except Exception:#畸形
                最新=0#最旧
        if 胜者 is None or 最新>胜者时间:#更新或尚无胜者
            胜者=取字段(工作区视图,'workspaceId')#记下胜者
            胜者时间=最新#记下时间
    return 胜者#最近 id

class 工作区运行时:#工作区运行时
    """真实工作区对象层与宿主动作。"""

    def __init__(自身,上下文,接口,会话端口):#组装运行时
        """管理器 + UI 投影存储；注入 ctx.workspaces。"""
        自身._接口=接口#共享线客户端
        自身._会话=会话端口#跨域会话面
        自身._管理器=工作区管理器(接口)#对象层
        自身.list=创建快照存储({#UI 投影存储
            'items':[],'archivedSessionIds':[],'state':'idle','phase':'pending','error':None,#空列表
            'baselinesReady':False,'recentWorkspaceId':None,#未就绪
        })#结束初始
        自身._连接中={}#进行中连接
        自身._初始选择已启=False#是否已启动初始选择
        自身._管理器.订阅(自身._投影)#管理器脏则投影
        自身._会话.list.订阅(自身._投影)#会话列表脏则投影
        提供=getattr(getattr(上下文,'reflect',None),'provide',None)#reflect.provide
        if callable(提供):#有注入面
            提供('workspaces',自身,None)#注入 ctx.workspaces
        elif hasattr(上下文,'provide') and callable(上下文.provide):#退化 provide
            上下文.provide('workspaces',自身)#注入

    async def 连接工作区(自身,工作区标识):#接到空白会话
        """复用或新造空白会话；返回会话 id。"""
        快照=自身.list.取快照()#列表
        工作区视图=next((项 for 项 in 快照['items'] if 取字段(项,'workspaceId')==工作区标识),None)#列表行
        if 工作区视图 is None:#未知
            raise Exception('workspaces.connectWorkspace: unknown workspace '+str(工作区标识))#未知工作区
        在飞=自身._连接中.get(工作区标识)#进行中创建
        if 在飞 is not None:#共享
            return await 在飞#等待
        归档=快照['archivedSessionIds']#归档集
        会话快照=自身._会话.list.取快照()#会话列表
        for 标识 in 会话快照.get('ids') or []:#扫描行
            摘要=(会话快照.get('byId') or {}).get(标识)#行摘要
            if 摘要 is not None and 取字段(摘要,'blank') and 取字段(摘要,'cwd')==取字段(工作区视图,'path') and 标识 in (取字段(工作区视图,'sessionIds') or []) and 标识 not in 归档:#可复用
                return 标识#复用
        async def 尝试():#新造
            try:#创建
                return await 自身._会话.create({'workspaceId':工作区标识})#新造空白会话
            finally:#结束
                自身._连接中.pop(工作区标识,None)#清进行中
        自身._连接中[工作区标识]=尝试()#记下
        return await 自身._连接中[工作区标识]#共享承诺

    def 启动初始选择(自身):#一次性初始选择
        """跟随第一份完整基线恰好选择一次默认会话。"""
        if 自身._初始选择已启:#已经启动过
            raise Exception('workspaces.startInitialSelection: already started')#禁止二次
        自身._初始选择已启=True#钉住一次性
        状态盒={'state':'waiting'}#选择状态机
        拆除盒={'disposed':False}#是否已拆除
        def 对照():#对照基线
            """等待 → 连接 → 完成。"""
            if 拆除盒['disposed'] or 状态盒['state']!='waiting':#已拆或不再等待
                return#停
            工作区快照=自身.list.取快照()#工作区投影
            if not 工作区快照.get('baselinesReady'):#双基线未齐
                return#等
            当前=自身._会话.list.取快照().get('current')#已有当前会话
            目标=工作区快照.get('recentWorkspaceId')#最近工作区
            if 当前 is not None or 目标 is None:#已有选择或没有工作区
                状态盒['state']='done'#无需连接
                return#结束
            状态盒['state']='connecting'#开始连接
            async def 跑():#连接
                try:#连接
                    会话标识=await 自身.连接工作区(目标)#接到空白会话
                    if 拆除盒['disposed']:#已拆
                        return#不再导航
                    if 自身._会话.list.取快照().get('current') is None:#期间没有别人选上
                        自身._会话.open(会话标识)#打开结果
                    状态盒['state']='done'#完成
                except Exception as 原因:#失败
                    if 拆除盒['disposed']:#已拆
                        return#不再重试
                    状态盒['state']='waiting'#允许下次投影再试
                    warnings.warn('initial workspace selection failed: '+str(原因))#诊断
            try:#有环
                import asyncio#asyncio
                asyncio.get_running_loop().create_task(跑())#挂任务
            except RuntimeError:#无环
                pass#宿主稍后驱动
        退订=自身.list.订阅(对照)#跟随投影
        对照()#立刻对照一次
        def 拆除():#拆除
            """禁止再导航。"""
            拆除盒['disposed']=True#钉住
            退订()#退订
        return 拆除#拆除器

    def 开始会话(自身,工作区标识=None):#新会话
        """解析目标工作区，连接空白会话并导航。"""
        工作区快照=自身.list.取快照()#工作区投影
        当前=自身._会话.list.取快照().get('current')#当前会话
        当前工作区=None#当前会话所属
        if 当前 is not None:#有当前
            当前工作区=next((取字段(项,'workspaceId') for 项 in 工作区快照['items'] if 当前 in (取字段(项,'sessionIds') or [])),None)#所属
        目标=工作区标识 if 工作区标识 is not None else (当前工作区 if 当前工作区 is not None else 工作区快照.get('recentWorkspaceId'))#显式 / 当前 / 最近
        if 目标 is None:#没有任何工作区
            自身._会话.clear()#进入新会话视图
            return#结束
        async def 跑():#连接
            try:#连接
                会话标识=await 自身.连接工作区(目标)#接到空白会话
                自身._会话.open(会话标识)#打开
            except Exception as 原因:#失败
                warnings.warn('new session failed: '+str(原因))#失败只诊断
        try:#有环
            import asyncio#asyncio
            asyncio.get_running_loop().create_task(跑())#挂任务
        except RuntimeError:#无环
            pass#宿主稍后驱动

    async def 创建(自身,输入):#创建工作区
        """把一条已有路径登记成工作区。"""
        结果=await 自身._管理器.创建(输入)#交给管理器
        if not 取字段(结果,'ok'):#业务失败
            raise 工作区创建错误(取字段(结果,'error'))#结构化抛
        return 取字段(取字段(结果,'value'),'workspace')#返回视图

    async def 选目录(自身):#选目录
        """打开宿主原生目录选择器。"""
        响应=await 自身._接口.host.pickDirectory({})#原生选择器
        结果=取字段(响应,'result',响应)#结果
        if not 取字段(结果,'ok'):#业务失败
            raise Exception('directory picker failed: '+str(取字段(取字段(结果,'error'),'message')))#大声失败
        return 取字段(取字段(结果,'value'),'path')#选中路径或 null

    async def 列目录(自身,路径=None,信号=None):#列目录
        """经宿主 browse 能力列出一层目录。"""
        载荷={} if 路径 is None else {'path':路径}#载荷
        if 信号 is None:#无中止
            响应=await 自身._接口.host.listDirectory(载荷)#浏览 RPC
        else:#带信号
            响应=await 自身._接口.host.listDirectory(载荷,信号)#浏览 RPC
        结果=取字段(响应,'result',响应)#结果
        if not 取字段(结果,'ok'):#失败
            raise 目录浏览错误(取字段(结果,'error'))#结构化抛
        return 取字段(结果,'value')#该层列表

    async def 创建目录(自身,路径,名):#创建子目录
        """经宿主 browse 能力创建子目录。"""
        响应=await 自身._接口.host.createDirectory({'path':路径,'name':名})#创建 RPC
        结果=取字段(响应,'result',响应)#结果
        if not 取字段(结果,'ok'):#失败
            raise 目录浏览错误(取字段(结果,'error'))#结构化抛
        return 取字段(取字段(结果,'value'),'path')#新目录绝对路径

    async def 打开路径(自身,路径):#打开路径
        """用宿主默认应用打开路径。"""
        响应=await 自身._接口.host.openPath({'path':路径})#打开 RPC
        结果=取字段(响应,'result',响应)#结果
        if not 取字段(结果,'ok'):#业务失败
            raise Exception('path open failed: '+str(取字段(取字段(结果,'error'),'message')))#大声失败

    async def 重命名(自身,工作区标识,标题):#重命名
        """重命名工作区。"""
        结果=await 自身._管理器.重命名(工作区标识,标题)#交给管理器
        if not 取字段(结果,'ok'):#失败
            错=取字段(结果,'error') or {}#错误
            raise Exception('workspace rename failed: '+str(取字段(错,'code'))+': '+str(取字段(错,'message')))#大声失败
        return 取字段(取字段(结果,'value'),'workspace')#更新后的视图

    async def 删除(自身,工作区标识):#删除
        """删除工作区登记。"""
        结果=await 自身._管理器.删除(工作区标识)#交给管理器
        if not 取字段(结果,'ok'):#失败
            错=取字段(结果,'error') or {}#错误
            raise Exception('workspace delete failed: '+str(取字段(错,'code'))+': '+str(取字段(错,'message')))#大声失败

    async def 插到之前(自身,工作区标识,锚点工作区标识=None):#重排工作区
        """在持久注册表显示顺序里移动工作区。"""
        结果=await 自身._管理器.插到之前(工作区标识,锚点工作区标识)#交给管理器
        if not 取字段(结果,'ok'):#失败
            错=取字段(结果,'error') or {}#错误
            raise Exception('workspace reorder failed: '+str(取字段(错,'code'))+': '+str(取字段(错,'message')))#大声失败

    async def 归档会话(自身,会话标识):#归档会话
        """把会话归档进注册表全局集。"""
        结果=await 自身._管理器.归档会话(会话标识)#交给管理器
        if not 取字段(结果,'ok'):#失败
            错=取字段(结果,'error') or {}#错误
            raise Exception('session archive failed: '+str(取字段(错,'code'))+': '+str(取字段(错,'message')))#大声失败

    async def 插会话到之前(自身,工作区标识,会话标识,锚点会话标识=None):#插会话
        """在工作区手动顺序里移动会话。"""
        结果=await 自身._管理器.插会话到之前(工作区标识,会话标识,锚点会话标识)#交给管理器
        if not 取字段(结果,'ok'):#失败
            错=取字段(结果,'error') or {}#错误
            raise Exception('workspace move failed: '+str(取字段(错,'code'))+': '+str(取字段(错,'message')))#大声失败
        return 取字段(取字段(结果,'value'),'workspace')#更新后的视图

    def 刷新(自身):#刷新基线
        """刷新工作区基线，复用进行中的拉取。"""
        return 自身._管理器.刷新()#交给管理器

    def 处理宿主信封(自身,信封):#派发帧
        """把宿主流信封路由进工作区对象层。"""
        自身._管理器.处理宿主信封(信封)#交给管理器

    def 处理已连接(自身):#重连
        """连接之后重建工作区基线。"""
        自身._管理器.处理已连接()#交给管理器

    def _投影(自身):#投影到 UI 存储
        """管理器 + 会话列表 → UI 快照。"""
        工作区=自身._管理器.取快照()#对象层快照
        会话=自身._会话.list.取快照()#会话列表
        双基线齐=工作区.get('phase')=='ready' and 会话.get('phase')=='ready'#双基线齐
        当前=会话.get('current')#当前会话
        if 当前 is not None and 当前 in (工作区.get('archivedSessionIds') or []):#当前已归档
            自身._会话.clear()#清选择
        自身.list.设({#整份替换投影
            'items':工作区.get('items') or [],#工作区行
            'archivedSessionIds':工作区.get('archivedSessionIds') or [],#归档集
            'state':工作区.get('state'),#拉取状态
            'phase':工作区.get('phase'),#到达阶段
            'error':工作区.get('error'),#最近错误
            'baselinesReady':双基线齐,#双基线就绪
            'recentWorkspaceId':最近工作区(工作区.get('items') or [],会话.get('byId') or {}) if 双基线齐 else None,#就绪才算最近
        })#结束 set
