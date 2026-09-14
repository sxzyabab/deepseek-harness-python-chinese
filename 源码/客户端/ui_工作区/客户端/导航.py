import threading#寿命中止与后台观察
from datetime import datetime#创建时解析

__all__=['目录浏览错误','工作区UI服务','最近工作区']#仅中文公开名


class 目录浏览错误(Exception):
    """目录浏览业务失败。"""
    def __init__(自身,rpc错误):
        """rpc错误为 RemoteFailure dict。"""
        自身.rpcError=rpc错误#业务失败
        码=rpc错误['code'] if isinstance(rpc错误,dict) and 'code' in rpc错误 else ''#码
        文=rpc错误['message'] if isinstance(rpc错误,dict) and 'message' in rpc错误 else str(rpc错误)#文
        super().__init__('目录浏览失败: '+str(码)+': '+str(文))#消息
        自身.name='DirectoryBrowseError'#错误名


def _创建时毫秒(文):
    """工作区 createdAt 转纪元毫秒；失败则 0。"""
    try:#解析
        return int(datetime.fromisoformat(文.replace('Z','+00:00')).timestamp()*1000)#纪元毫秒
    except Exception:#失败
        return 0#零


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
        上下文.副作用(lambda:自身.监视导航(),'ui-workspace: Workspace navigation policy')#导航策略
        if hasattr(上下文,'reflect') and hasattr(上下文.reflect,'provide'):#可提供
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
            raise Exception('uiWorkspace.connectWorkspace: 未知工作区 '+str(工作区标识))#抛
        if 工作区标识 in 自身.connecting:#飞行中
            return 自身.connecting[工作区标识].等待()#共享
        已归档=快['archivedSessionIds']#已归档
        会话快=自身.sessions.list.getSnapshot()#会话
        for 标识 in 会话快['ids']:#找可复用
            摘要=会话快['byId'][标识] if 标识 in 会话快['byId'] else None#摘要
            if (摘要 is not None and 摘要.get('blank') and 摘要.get('cwd')==工作区['path']
                and 摘要['id'] in 工作区['sessionIds']
                and 摘要['id'] not in 已归档):#可复用
                return 摘要['id']#复用
        任务=自身.sessions.create({'workspaceId':工作区标识})#创建
        自身.connecting[工作区标识]=任务#记下
        try:#等待
            return 任务.等待()#会话 id
        finally:#清
            自身.connecting.pop(工作区标识,None)#删

    def openSession(自身,会话标识):
        """选中会话并清全局面板。"""
        自身.sessions.open(会话标识)#打开
        自身.ctx.layout.selectPanel(None)#清面板

    def openWorkspace(自身,工作区标识,打开前=None):
        """连接并打开；可被后续导航取代。"""
        导航=自身.ctx.layout.beginNavigation()#导航中止 Event
        def 仍当前():
            """导航与寿命均未中止。"""
            导航已中=导航.is_set()#导航
            return (not 导航已中) and (not 自身.lifetime.is_set())#当前
        会话标识=自身.connectWorkspace(工作区标识)#连接
        if not 仍当前():#被取代
            return#止
        if 打开前 is not None:#准备
            打开前(会话标识)#回调
        if 仍当前():#仍当前
            自身.openSession(会话标识)#打开

    def forkSession(自身,会话标识):
        """分叉并打开子会话。"""
        导航=自身.ctx.layout.beginNavigation()#导航中止
        任务=自身.sessions.fork({'sessionId':会话标识,'increaseTitle':True})#分叉
        子标识=任务.等待()#子
        导航已中=导航.is_set()#导航
        if not 导航已中 and not 自身.lifetime.is_set():#仍当前
            自身.openSession(子标识)#打开

    def startSession(自身,工作区标识=None):
        """新建会话流。"""
        工作区快=自身.workspaces.list.getSnapshot()#工作区
        会话快=自身.sessions.list.getSnapshot()#会话
        当前=会话快['current'] if 'current' in 会话快 else None#当前
        当前工作区=None#所属
        if 当前 is not None:#有当前
            for 项 in 工作区快['items']:#找
                if 当前 in 项['sessionIds']:#命中
                    当前工作区=项['workspaceId']#记
                    break#止
        最近=最近工作区(工作区快['items'],会话快['byId']) if 工作区快.get('phase')=='ready' and 会话快.get('phase')=='ready' else None#最近
        目标=工作区标识 if 工作区标识 is not None else (当前工作区 if 当前工作区 is not None else 最近)#目标
        if 目标 is None:#无
            自身.sessions.clear()#清
            自身.ctx.layout.selectPanel(None)#清面板
            return#止
        try:#打开
            自身.openWorkspace(目标)#打开
        except BaseException as 原因:#失败
            print('新建会话失败:',原因)#告警

    def archiveSession(自身,会话标识):
        """归档会话。"""
        任务=自身.workspaces.archiveSession(会话标识)#归档
        任务.等待()#等

    def pickDirectory(自身):
        """打开宿主目录选择器。"""
        结果=自身.directoryPicker.pick()#选
        结果=结果.等待()#等
        if not 结果['ok']:#失败
            错误体=结果['error']#错误体
            raise Exception('目录选择器失败: '+str(错误体['message'] if isinstance(错误体,dict) and 'message' in 错误体 else 错误体))#抛
        return 结果['value']#路径或 None

    def listDirectory(自身,路径=None,信号=None):
        """列一级目录。"""
        结果=自身.directoryPicker.list(路径,信号)#列
        结果=结果.等待()#等
        if not 结果['ok']:#失败
            raise 目录浏览错误(结果['error'])#抛
        return 结果['value']#列表

    def createDirectory(自身,路径,名):
        """建子目录。"""
        结果=自身.directoryPicker.createDirectory(路径,名)#建
        结果=结果.等待()#等
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
            if 工作区.get('phase')!='ready' or 会话.get('phase')!='ready':#未就绪
                return#止
            if 会话.get('current') is not None:#已有当前
                初始[0]='done'#完成
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
                    if 自身.lifetime.is_set():#已中止
                        return#止
                    if 自身.sessions.list.getSnapshot().get('current') is None:#仍无当前
                        自身.sessions.open(会话标识)#打开
                    初始[0]='done'#完成
                except BaseException as 原因:#失败
                    if 自身.lifetime.is_set():#已中止
                        return#止
                    初始[0]='waiting'#回等待
                    print('初始工作区选择失败:',原因)#告警
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
        当前=自身.sessions.list.getSnapshot().get('current')#当前
        if 当前 is None:#无
            return False#否
        if 当前 not in 自身.workspaces.list.getSnapshot().get('archivedSessionIds',()):#未归档
            return False#否
        自身.sessions.clear()#清
        return True#已清
