import threading#寿命中止与后台观察
from datetime import datetime#创建时解析
from ...存储 import 创建快照存储#主视图选中持久化

__all__=['目录浏览错误','工作区UI服务','最近工作区']#仅中文公开名


class 目录浏览错误(Exception):
    """目录浏览业务失败。"""
    def __init__(自身,rpc错误):
        """rpc错误为 RemoteFailure dict。"""
        自身.rpcError=rpc错误#业务失败
        码=rpc错误['code'] if isinstance(rpc错误,dict) and 'code' in rpc错误 else ''#码
        文=rpc错误['message'] if isinstance(rpc错误,dict) and 'message' in rpc错误 else str(rpc错误)#文
        super().__init__('directory browse failed: '+str(码)+': '+str(文))#消息原样英文
        自身.name='DirectoryBrowseError'#错误名


def _创建时毫秒(文):
    """工作区 createdAt 转纪元毫秒；失败则 0。"""
    return int(datetime.fromisoformat(文.replace('Z','+00:00')).timestamp()*1000)#纪元毫秒


def 最近工作区(工作区表,会话表):
    """按会话更新时间选最近工作区；并列按 Host 工作区顺序。"""
    已选=None#已选
    已选时=float('-inf')#已选时间
    for 工作区 in 工作区表:#逐
        最新=float('-inf')#本区最新
        for 会话标识 in 工作区['sessionIds']:#逐会话
            摘要=会话表[会话标识] if 会话标识 in 会话表 else None#摘要
            if 摘要 is not None:#有
                最新=max(最新,摘要['updatedAt'])#更新
        if 最新==float('-inf'):#无会话
            最新=_创建时毫秒(工作区['createdAt'] if 'createdAt' in 工作区 else '')#创建时
        if 已选 is None or 最新>已选时:#更近
            已选=工作区['workspaceId']#记
            已选时=最新#时
    return 已选#返回


class 工作区UI服务:#跨控制器导航与目录
    """实现 UiWorkspace 面；经 reflect.provide 登记为 uiWorkspace。"""

    def __init__(自身,上下文,目录选择器,工作区,会话):
        """目录选择器为 remote.directoryPicker。"""
        自身.ctx=上下文#根上下文
        自身.directoryPicker=目录选择器#选目录
        自身.workspaces=工作区#工作区
        自身.sessions=会话#会话
        自身.connecting={}#进行中连接
        自身.lifetime=threading.Event()#寿命中止（set=已中止）
        自身.selection=创建快照存储({},{'persist':{'name':'dsh.sessions.current'}})#主视图选中
        自身.mainReference=None#主视图引用
        def 导航寿命():#策略寿命
            """启动监视并在拆除时释放主引用。"""
            停=自身.监视导航()#监视
            def 拆除():#拆除
                """停监视、中止寿命、释放主引用。"""
                停()#停
                自身.lifetime.set()#中止
                引用=自身.mainReference#主引用
                自身.mainReference=None#清空
                if 引用 is not None:#有引用
                    引用.release()#释放
            return 拆除#拆除器
        上下文.副作用(导航寿命,'ui-workspace: Workspace navigation policy')#导航策略
        上下文.reflect.provide('uiWorkspace',自身)#提供面

    def connectWorkspace(自身,工作区标识):
        """解析可复用或新建空白会话。"""
        快=自身.workspaces.list.getSnapshot()#工作区快照
        工作区=None#目标
        for 项 in 快['items']:#找
            if 项['workspaceId']==工作区标识:#命中
                工作区=项#记
                break#止
        if 工作区 is None:#未知
            raise Exception('uiWorkspace.connectWorkspace: unknown workspace '+str(工作区标识))#抛
        if 工作区标识 in 自身.connecting:#飞行中
            return 自身.connecting[工作区标识].等待()#共享
        已归档=快['archivedSessionIds']#已归档
        会话快=自身.sessions.list.getSnapshot()#会话
        for 标识 in 会话快['ids']:#找可复用
            摘要=会话快['byId'][标识] if 标识 in 会话快['byId'] else None#摘要
            if (摘要 is not None and 摘要['blank'] and 摘要['cwd']==工作区['path']
                and 摘要['id'] in 工作区['sessionIds']
                and 摘要['id'] not in 已归档):#可复用
                return 摘要['id']#复用
        任务=自身.sessions.create({'workspaceId':工作区标识})#创建
        自身.connecting[工作区标识]=任务#记下
        try:#等待
            return 任务.等待()#会话 id
        finally:#清
            自身.connecting.pop(工作区标识,None)#删

    def openSession(自身,目标):
        """选中会话目标并显示对话。"""
        自身.替换主视图(目标,自身.lifetime)#替换

    def openWorkspace(自身,工作区标识,打开前=None):
        """连接并打开；可被后续导航取代。"""
        导航=自身.ctx.layout.beginNavigation()#导航中止 Event
        会话标识=自身.connectWorkspace(工作区标识)#连接
        if 导航.is_set() or 自身.lifetime.is_set():#被取代
            return#止
        自身.替换主视图(会话标识,导航,打开前)#替换

    def forkSession(自身,会话标识):
        """分叉并打开子会话。"""
        导航=自身.ctx.layout.beginNavigation()#导航中止
        子标识=自身.sessions.fork({'sessionId':会话标识,'increaseTitle':True}).等待()#分叉
        if not 导航.is_set() and not 自身.lifetime.is_set():#仍当前
            自身.替换主视图(子标识,导航)#打开

    def startSession(自身,工作区标识=None):
        """新建会话流。"""
        工作区快=自身.workspaces.list.getSnapshot()#工作区
        会话快=自身.sessions.list.getSnapshot()#会话
        当前=自身.mainReference.sessionId if 自身.mainReference is not None else None#当前
        当前工作区=None#所属
        if 当前 is not None:#有当前
            for 项 in 工作区快['items']:#找
                if 当前 in 项['sessionIds']:#命中
                    当前工作区=项['workspaceId']#记
                    break#止
        最近=最近工作区(工作区快['items'],会话快['byId']) if 工作区快['phase']=='ready' and 会话快['phase']=='ready' else None#最近
        目标=工作区标识 if 工作区标识 is not None else (当前工作区 if 当前工作区 is not None else 最近)#目标
        if 目标 is None:#无
            自身.清主视图()#清
            return#止
        try:#打开
            自身.openWorkspace(目标)#打开
        except BaseException as 原因:#失败
            print('new session failed:',原因)#告警

    def archiveSession(自身,会话标识):
        """归档会话；若为当前则清选中。"""
        自身.workspaces.archiveSession(会话标识).等待()#归档
        if 自身.mainReference is not None and 自身.mainReference.sessionId==会话标识:#当前
            自身.清主视图()#清

    def unarchiveSession(自身,会话标识):
        """解除归档，恢复到记录的工作区位置。"""
        自身.workspaces.unarchiveSession(会话标识).等待()#等

    def pickDirectory(自身):
        """打开宿主目录选择器。"""
        结果=自身.directoryPicker.pick().等待()#选
        if not 结果['ok']:#失败
            raise Exception('directory picker failed: '+str(结果['error']['message']))#抛
        return 结果['value']#路径或 None

    def listDirectory(自身,路径=None,信号=None):
        """列一级目录。"""
        结果=自身.directoryPicker.list(路径,信号).等待()#列
        if not 结果['ok']:#失败
            raise 目录浏览错误(结果['error'])#抛
        return 结果['value']#列表

    def createDirectory(自身,路径,名):
        """建子目录。"""
        结果=自身.directoryPicker.createDirectory(路径,名).等待()#建
        if not 结果['ok']:#失败
            raise 目录浏览错误(结果['error'])#抛
        return 结果['value']#绝对路径

    def 监视导航(自身):
        """初始选中与归档当前清理。"""
        初始=['waiting']#阶段盒

        def 调和():
            """调和。"""
            if 自身.lifetime.is_set():#已中止
                return#止
            if 自身.清归档当前():#已清
                return#止
            if 初始[0]!='waiting':#非等待
                return#止
            工作区=自身.workspaces.list.getSnapshot()#工作区
            会话=自身.sessions.list.getSnapshot()#会话
            if 工作区['phase']!='ready' or 会话['phase']!='ready':#未就绪
                return#止
            if 自身.mainReference is not None:#已有主引用
                初始[0]='done'#完成
                return#止
            已存=自身.selection.getSnapshot()#已存选中
            已存目标=None#可恢复
            if 'subagentAddress' in 已存 and 已存['subagentAddress'] is not None:#子智能体
                已存目标=已存['subagentAddress']#地址
            elif 'sessionId' in 已存 and 已存['sessionId'] is not None and 已存['sessionId'] in 会话['byId']:#会话仍在
                已存目标=已存['sessionId']#会话
            if 已存目标 is not None:#有已存
                初始[0]='connecting'#连接中
                try:#恢复
                    if 'subagentAddress' in 已存 and 已存['subagentAddress'] is not None:#子智能体
                        自身.sessions.refreshSubagents(已存['subagentAddress']['parentSessionId'])#刷新
                    自身.openSession(已存目标)#打开
                    初始[0]='done'#完成
                except BaseException as 原因:#失败
                    初始[0]='waiting'#回等待
                    print('initial Session restoration failed:',原因)#告警
                return#止
            目标=最近工作区(工作区['items'],会话['byId'])#最近
            if 目标 is None:#无
                初始[0]='done'#完成
                return#止
            初始[0]='connecting'#连接中
            def 观察():
                """后台连接。"""
                try:#成功
                    会话标识=自身.connectWorkspace(目标)#连接
                    if 自身.mainReference is None:#仍无主
                        自身.openSession(会话标识)#打开
                    初始[0]='done'#完成
                except BaseException as 原因:#失败
                    if 自身.lifetime.is_set():#已中止
                        return#止
                    初始[0]='waiting'#回等待
                    print('initial workspace selection failed:',原因)#告警
            线=threading.Thread(target=观察)#线
            线.daemon=True#守护
            线.start()#启

        拆工作区=自身.workspaces.list.subscribe(调和)#订
        拆会话=自身.sessions.list.subscribe(调和)#订
        调和()#首次

        def 拆除():
            """拆除。"""
            自身.lifetime.set()#中止
            拆会话()#拆
            拆工作区()#拆
        return 拆除#拆除器

    def 清归档当前(自身):
        """若当前已归档则清除；返回是否已清。"""
        当前=自身.mainReference.sessionId if 自身.mainReference is not None else None#当前
        if 当前 is None:#无
            return False#否
        if 当前 not in 自身.workspaces.list.getSnapshot()['archivedSessionIds']:#未归档
            return False#否
        自身.清主视图()#清
        return True#已清

    def 清主视图(自身):
        """清主引用与持久化选中。"""
        旧=自身.mainReference#旧
        自身.mainReference=None#清空
        自身.selection.set({})#清持久化
        if 旧 is not None:#有旧
            旧.release()#释放
        自身.ctx.layout.selectPanel(None)#清面板

    def 替换主视图(自身,目标,信号,打开前=None):
        """占用目标并换主引用。信号为 Event（set=已中止）。"""
        if 信号.is_set():#已中止
            raise Exception('aborted')#抛
        引用=自身.sessions.retain(目标,{'source':'mainView'})#占用
        try:#准备
            if 信号.is_set():#再检
                raise Exception('aborted')#抛
            if 打开前 is not None:#打开前
                打开前(引用.sessionId)#回调
            if 信号.is_set():#被取代
                引用.release()#释放
                return#止
            if isinstance(目标,str):#会话 id
                子地址=自身.sessions.subagentAddress(引用.sessionId)#反查
            else:#本就是地址
                子地址=目标#记下
            选中={'sessionId':引用.sessionId}#持久化
            if 子地址 is not None:#有地址
                选中['subagentAddress']=子地址#带上
            自身.selection.set(选中)#写
        except BaseException:#失败
            引用.release()#释放
            raise#再抛
        旧=自身.mainReference#旧
        自身.mainReference=引用#换新
        if 旧 is not None:#有旧
            旧.release()#释放旧
        自身.sessions.refreshSubagents(引用.sessionId)#刷新
        自身.ctx.layout.selectPanel(None)#清面板
