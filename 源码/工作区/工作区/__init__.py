"""工作区实体注册表。"""
import os,re,threading,uuid#路径、写死 ISO、串行写与会话 id
from datetime import datetime,timedelta,timezone#ISO 时间戳、固定偏移与 UTC
from zoneinfo import ZoneInfo#IANA / UTC
from ...依赖 import cordis
服务=cordis.服务
from .实体 import 工作区实体,工作区移动无效错误,工作区错误
from .路径 import 规范化真实路径
from .规格 import 工作区域规格

名称='workspace'#插件名（字面量）
依赖=['storageDomain','sessionPersistence']
_创建时刻=re.compile(#记录 createdAt：Z 或 ±HH:MM 偏移
    r'^([0-9]{4})-([0-9]{2})-([0-9]{2})T([0-9]{2}):([0-9]{2}):([0-9]{2})(?:\.([0-9]+))?(Z|([+-])([0-9]{2}):([0-9]{2}))\Z',
    re.ASCII,
)#写死轮廓，不用 fromisoformat

def 工作区标识(标识):
    """把字符串标成工作区 id。"""
    return 标识

class 工作区未知会话错误(Exception):
    """归档点名了活会话与持久化都不认识的会话。"""
    def __init__(自身,会话号):
        """记下未知会话 id。"""
        super().__init__("cannot archive session: live sessions and session persistence hold no such session")
        自身.sessionId=会话号

class 工作区顺序无效错误(Exception):
    """重排点名了未登记的工作区。"""
    def __init__(自身,工作区号):
        """记下未知工作区 id。"""
        super().__init__("cannot reorder unknown workspace")
        自身.workspaceId=工作区号

def _同id列表(左,右):
    """两份 id 列表是否同序同值。"""
    return len(左)==len(右) and all(左[索引]==右[索引] for 索引 in range(len(左)))

def _头时间(头):
    """会话头 createdAt，缺键当 0。头是 dict。"""
    return 头['createdAt'] if 'createdAt' in 头 else 0#纪元毫秒或秒

def _头排序键(头):
    """头排序：新者优先，再按 id。"""
    return (-_头时间(头),str(头['id'] if 'id' in 头 else ''))

def _同会话列表(左,右):
    """会话 id 列表同序同值。"""
    return _同id列表(左,右)

def _解析创建时刻(文本):
    """把记录 createdAt 从写死的 ISO-8601（Z 或数字偏移）解析成 POSIX 秒。"""
    匹配=_创建时刻.match(文本)#按轮廓
    if 匹配 is None:#形态不对
        raise ValueError('invalid createdAt')#拒绝
    年,月,日=int(匹配.group(1)),int(匹配.group(2)),int(匹配.group(3))#日历
    时,分,秒=int(匹配.group(4)),int(匹配.group(5)),int(匹配.group(6))#墙钟
    小数=匹配.group(7) if 匹配.group(7) is not None else ''#小数秒
    微秒=int((小数+'000000')[:6]) if 小数!='' else 0#微秒
    if 匹配.group(8)=='Z':#UTC
        区=ZoneInfo('UTC')#零区
    else:#数字偏移
        偏移=timedelta(hours=int(匹配.group(10)),minutes=int(匹配.group(11)))#偏移
        if 匹配.group(9)=='-':#西向
            偏移=-偏移#取负
        区=timezone(偏移)#固定偏移载体
    return datetime(年,月,日,时,分,秒,微秒,tzinfo=区).timestamp()#POSIX 秒

class 工作区注册表(服务):
    """耐久工作区注册表。启动等待 sessionPersistence 并完成一次性历史引导。"""
    inject=['storageDomain','sessionPersistence']

    def __init__(自身,上下文):
        """登记服务并接线实体宿主机械。"""
        super().__init__(上下文,'workspaceRegistry')
        自身._表=None
        自身._全局=None
        自身._状态=None
        自身._实体={}
        自身._头={}
        自身._会话路径={}
        自身._无效会话路径={}
        自身._写锁=threading.Lock()
        def 记住会话路径(会话号,路径):
            """发布有效 cwd。"""
            自身._会话路径[会话号]=路径
            自身._无效会话路径.pop(会话号,None)
        def 取表():
            """实体写链取表。"""
            return 自身._要求表()
        def 取会话路径(会话号):
            """实体读会话规范路径。"""
            return 自身._会话路径[会话号] if 会话号 in 自身._会话路径 else None
        def 读会话头(会话号):
            """实体读会话头。"""
            return 自身._读会话头(会话号)
        自身._宿主={
            'table':取表,
            'sessionPath':取会话路径,
            'readSessionHeader':读会话头,
            'rememberSessionPath':记住会话路径,
        }
        自身.__dict__[服务.初始化]=自身._初始化

    def _初始化(自身):
        """打开域、恢复挂起、引导历史并重建实体缓存。"""
        域=自身.所属上下文.storageDomain.open(工作区域规格)
        def 关域():
            """卸载关域。"""
            域.close()
        yield 关域
        自身._表=域.table('workspaces')
        自身._全局=getattr(域,'global')
        自身._状态=自身._全局.get()
        自身._恢复挂起变更()
        自身._校验已存状态(自身._状态)
        if 自身._状态['initialized'] is not True:
            头列表=自身.所属上下文.sessionPersistence.列出()
            自身._替换头索引(头列表)
            自身._引导(头列表)
        elif 自身._表.size>0:
            自身._替换头索引(自身.所属上下文.sessionPersistence.列出())
        自身._索引活会话()
        自身._校验已存状态(自身._要求状态())
        自身._重建实体()
        自身._报告过滤候选()

    def create(自身,路径,标题=None):
        """创建或复用工作区。"""
        规范=规范化真实路径(路径)
        if not os.path.isdir(规范):
            raise 工作区错误("cannot create a workspace: path is not a directory")
        def 创建作业():
            """串行创建。"""
            return 自身._按规范创建(规范,标题)
        return 自身._入队写操作(创建作业)

    def get(自身,标识):
        """按 id 取实体。"""
        return 自身._实体[标识] if 标识 in 自身._实体 else None

    def list(自身):
        """按耐久顺序列出。"""
        结果=[]
        for 标识 in 自身._要求状态()['workspaceIds']:
            if 标识 not in 自身._实体:
                raise 工作区错误("workspace registry order references missing workspace")
            结果.append(自身._实体[标识])
        return 结果

    def delete(自身,标识):
        """删除登记。"""
        def 删除作业():
            """串行删除。"""
            return 自身._删除已知(标识)
        return 自身._入队写操作(删除作业)

    def insertBefore(自身,标识,锚标识=None):
        """按锚重排工作区顺序。"""
        def 操作():
            """写操作。"""
            状态=自身._要求状态()
            if 标识 not in 状态['workspaceIds']:
                raise 工作区顺序无效错误(标识)
            if 锚标识 is not None and 锚标识 not in 状态['workspaceIds']:
                raise 工作区顺序无效错误(锚标识)
            if 锚标识==标识:
                return 状态['workspaceIds']
            去掉=[项 for 项 in 状态['workspaceIds'] if 项!=标识]
            位置=len(去掉) if 锚标识 is None else 去掉.index(锚标识)
            新顺序=去掉[:位置]+[标识]+去掉[位置:]
            if _同id列表(新顺序,状态['workspaceIds']):
                return 状态['workspaceIds']
            自身._写状态({**状态,'workspaceIds':新顺序})
            return 新顺序
        return 自身._入队写操作(操作)

    @property
    def archivedSessionIds(自身):
        """已归档会话。"""
        return 自身._要求状态()['archivedSessionIds']

    def archiveSession(自身,会话号):
        """归档会话。"""
        def 操作():
            """写操作。"""
            if 会话号 in 自身._要求状态()['archivedSessionIds']:
                return
            if 自身._会话已知(会话号) is not True:
                raise 工作区未知会话错误(会话号)
            状态=自身._要求状态()
            自身._写状态({**状态,'archivedSessionIds':[*状态['archivedSessionIds'],会话号]})
        return 自身._入队写操作(操作)

    def unarchiveSession(自身,会话号):
        """取消归档。"""
        def 操作():
            """写操作。"""
            状态=自身._要求状态()
            if 会话号 not in 状态['archivedSessionIds']:
                return
            自身._写状态({**状态,'archivedSessionIds':[项 for 项 in 状态['archivedSessionIds'] if 项!=会话号]})
        return 自身._入队写操作(操作)

    def resolveByPath(自身,路径):
        """按规范路径解析工作区。"""
        规范=规范化真实路径(路径)
        for 实体 in 自身._实体.values():
            if 实体.path==规范:
                return 实体
        return None

    def _按规范创建(自身,规范,标题=None):
        """内部创建或复用。"""
        for 实体 in 自身._实体.values():
            if 实体.path==规范:
                return 实体
        表=自身._要求表()
        状态=自身._要求状态()
        标识=工作区标识(str(uuid.uuid4()))
        现在=datetime.now(ZoneInfo('UTC')).isoformat()
        展示=标题 if 标题 is not None and 标题!='' else os.path.basename(规范)#空串标题回落基名
        记录={'path':规范,'title':展示,'sessionIds':[],'createdAt':现在,'updatedAt':现在}
        实体=工作区实体(自身._宿主,标识,记录)
        自身._实体[标识]=实体#先发布缓存
        挂起状态={**状态,'pendingMutation':{'operation':'create','workspaceId':标识}}
        try:
            自身._写状态(挂起状态)
        except BaseException as 错误:
            del 自身._实体[标识]
            raise 错误
        try:
            表.put(标识,记录)
        except BaseException as 错误:
            del 自身._实体[标识]
            try:
                自身._写状态(状态)
            except BaseException as 回滚错误:
                raise 工作区错误("workspace record write and pending-marker rollback both failed") from 回滚错误
            raise 错误
        try:
            自身._写状态({'initialized':True,'workspaceIds':[标识,*状态['workspaceIds']],'archivedSessionIds':状态['archivedSessionIds']})
        except BaseException as 错误:
            del 自身._实体[标识]
            try:
                表.delete(标识)
            except BaseException as 回滚错误:
                raise 工作区错误("workspace order write and record rollback both failed; the pending marker remains recoverable") from 回滚错误
            try:
                自身._写状态(状态)
            except BaseException as 回滚错误:
                raise 工作区错误("workspace order write and pending-marker rollback both failed") from 回滚错误
            raise 错误
        return 实体

    def _删除已知(自身,标识):
        """删除已知工作区。"""
        if 标识 not in 自身._实体:
            return False#幂等空操作
        实体=自身._实体[标识]
        状态=自身._要求状态()
        下一状态={'initialized':True,'workspaceIds':[项 for 项 in 状态['workspaceIds'] if 项!=标识],'archivedSessionIds':状态['archivedSessionIds']}
        自身._写状态({**下一状态,'pendingMutation':{'operation':'delete','workspaceId':标识}})
        del 自身._实体[标识]#先从缓存拿掉
        try:
            自身._要求表().delete(标识)
        except BaseException as 错误:
            自身._实体[标识]=实体
            try:
                自身._写状态(状态)
            except BaseException as 回滚错误:
                del 自身._实体[标识]#与挂起标记一致
                raise 工作区错误("workspace record deletion and registry-order rollback both failed") from 回滚错误
            raise 错误
        try:
            自身._写状态(下一状态)
        except BaseException as 错误:
            自身.所属上下文.日志.警告("workspace was deleted but its pending marker could not be cleared: "+str(错误))
        return True

    def _恢复挂起变更(自身):
        """完成中断的删除挂起。"""
        状态=自身._要求状态()
        if 'pendingMutation' not in 状态 or 状态['pendingMutation'] is None:
            return
        挂起=状态['pendingMutation']
        if 挂起['workspaceId'] in 状态['workspaceIds']:
            raise 工作区错误("workspace domain is inconsistent: pending mutation is still present in registry order")
        自身._要求表().delete(挂起['workspaceId'])
        自身._写状态({'initialized':状态['initialized'],'workspaceIds':状态['workspaceIds'],'archivedSessionIds':状态['archivedSessionIds']})

    def _引导(自身,头列表):
        """按历史头一次性引导工作区表。头是 dict。"""
        表=自身._要求表()
        状态=自身._要求状态()
        按路径={}
        for 头 in 头列表:
            会话号=头['id']
            if 会话号 not in 自身._会话路径:
                continue
            路径=自身._会话路径[会话号]
            if 路径 not in 按路径:
                按路径[路径]=[]
            按路径[路径].append(头)
        组=[]
        for 路径,组头 in 按路径.items():
            已排序=sorted(组头,key=_头排序键)
            组.append({'path':路径,'headers':已排序,'newestAt':_头时间(已排序[0])})
        def 组间排序键(项):
            """组间：新者优先，再按路径。"""
            return (-项['newestAt'],项['path'])
        组.sort(key=组间排序键)
        路径到id={}
        已记账={}
        for 标识,记录 in 表.entries():
            路径到id[记录['path']]=标识
            for 会话 in 记录['sessionIds']:
                已记账[会话]=标识
        for 组项 in 组:
            标识=路径到id[组项['path']] if 组项['path'] in 路径到id else None
            if 标识 is None:
                会话列表=[头['id'] for 头 in 组项['headers'] if 头['id'] not in 已记账]
                if len(会话列表)==0:
                    continue
                标识=工作区标识(str(uuid.uuid4()))
                最新=组项['newestAt']
                if 最新>1e12:#纪元毫秒
                    创建时刻=datetime.fromtimestamp(最新/1000.0,tz=ZoneInfo('UTC')).isoformat()#毫秒转 ISO
                else:#纪元秒
                    创建时刻=datetime.fromtimestamp(最新,tz=ZoneInfo('UTC')).isoformat()#秒转 ISO
                记录={'path':组项['path'],'title':os.path.basename(组项['path']),'sessionIds':会话列表,'createdAt':创建时刻,'updatedAt':创建时刻}
                表.put(标识,记录)
                路径到id[组项['path']]=标识
                for 会话 in 会话列表:
                    已记账[会话]=标识
                continue
            当前=表.get(标识)
            历史=[头['id'] for 头 in 组项['headers'] if (头['id'] not in 已记账) or 已记账[头['id']]==标识]
            历史集=set(历史)
            会话列表=历史+[会话 for 会话 in 当前['sessionIds'] if 会话 not in 历史集]
            if _同会话列表(当前['sessionIds'],会话列表):
                continue
            def 合并会话(记录,成员=会话列表):
                """写链合并会话账本。"""
                return {**记录,'sessionIds':成员,'updatedAt':datetime.now(ZoneInfo('UTC')).isoformat()}
            表.update(标识,合并会话)
            for 会话 in 历史:
                已记账[会话]=标识
        组排名={组项['path']:组项['newestAt'] for 组项 in 组}
        先前排名={标识:索引 for 索引,标识 in enumerate(状态['workspaceIds'])}
        def 工作区排序键(项):
            """按组新近度、先前顺序、id 排序。"""
            标识,记录=项
            if 记录['path'] in 组排名:
                新近=组排名[记录['path']]
            else:
                新近=_解析创建时刻(记录['createdAt'])
            if 标识 in 先前排名:
                return (-新近,0,先前排名[标识],str(标识))
            return (-新近,1,0,str(标识))
        工作区列表=sorted(表.entries(),key=工作区排序键)
        工作区标识列表=[标识 for 标识,_ in 工作区列表]
        if not _同id列表(状态['workspaceIds'],工作区标识列表):
            自身._写状态({'initialized':False,'workspaceIds':工作区标识列表,'archivedSessionIds':状态['archivedSessionIds']})
        自身._写状态({'initialized':True,'workspaceIds':工作区标识列表,'archivedSessionIds':状态['archivedSessionIds']})

    def _校验已存状态(自身,状态):
        """校验域顺序与表一致。"""
        表=自身._要求表()
        顺序=set()
        for 标识 in 状态['workspaceIds']:
            if 标识 in 顺序:
                raise 工作区错误("workspace domain is inconsistent: registry order repeats a workspace")
            if 标识 not in 表:
                raise 工作区错误("workspace domain is inconsistent: registry order references missing workspace")
            顺序.add(标识)
        if 状态['initialized'] is True and len(顺序)!=表.size:
            raise 工作区错误("workspace domain is inconsistent: a workspace is absent from registry order")
        路径占用={}
        会话占用={}
        for 标识,记录 in 表.entries():
            if 记录['path'] in 路径占用:
                raise 工作区错误("workspace domain is inconsistent: a path is claimed by two workspaces")
            路径占用[记录['path']]=标识
            for 会话 in 记录['sessionIds']:
                if 会话 in 会话占用:
                    raise 工作区错误("workspace domain is inconsistent: a session is accounted by two workspaces")
                会话占用[会话]=标识

    def _重建实体(自身):
        """按顺序重建实体缓存。"""
        自身._实体.clear()
        for 标识 in 自身._要求状态()['workspaceIds']:
            记录=自身._要求表().get(标识)
            自身._实体[标识]=工作区实体(自身._宿主,标识,记录)

    def _替换头索引(自身,头列表):
        """重建头索引。"""
        自身._头.clear()
        自身._会话路径.clear()
        自身._无效会话路径.clear()
        自身.索引头列表(头列表)

    def 索引头列表(自身,头列表):
        """索引一批头。"""
        for 头 in 头列表:
            自身._索引头(头)

    def _索引头(自身,头):
        """索引一头。头是 dict。"""
        自身._头[头['id']]=头
        自身._会话路径.pop(头['id'],None)
        if 'cwd' not in 头 or 头['cwd'] is None:
            自身._无效会话路径[头['id']]='header has no cwd'
            return
        try:
            路径=规范化真实路径(头['cwd'])
            if not os.path.isdir(路径):
                自身._无效会话路径[头['id']]="cwd is not a directory"#不夹路径
                return
            自身._会话路径[头['id']]=路径
            自身._无效会话路径.pop(头['id'],None)
        except OSError:
            自身._无效会话路径[头['id']]="cwd does not resolve"

    def _索引活会话(自身):
        """索引活会话存储里的头。"""
        会话存储=自身.所属上下文.获取服务('sessions',False)#可选
        if 会话存储 is None:
            return
        自身.索引头列表([会话.header for 会话 in 会话存储.列出()])

    def _报告过滤候选(自身):
        """报告账本成员被路径投影滤掉的原因。"""
        for 实体 in 自身._实体.values():
            记录=自身._要求表().get(实体.id)
            for 会话 in 记录['sessionIds']:
                路径=自身._会话路径[会话] if 会话 in 自身._会话路径 else None
                if 路径==记录['path']:
                    continue
                if 会话 in 自身._无效会话路径:
                    原因=自身._无效会话路径[会话]
                elif 会话 in 自身._头:
                    原因='canonical cwd differs from workspace path'#不夹路径
                else:
                    原因='session header is missing'
                自身.所属上下文.日志.警告("workspace filtered a session from membership: "+原因)

    def _读会话头(自身,会话号):
        """读会话头。"""
        活=自身.所属上下文.获取服务('sessions',False)
        if 活 is not None:
            会话=活.获取(会话号)
            if 会话 is not None:
                自身._头[会话号]=会话.header
                return 会话.header
        if 会话号 in 自身._头:
            return 自身._头[会话号]
        头列表=自身.所属上下文.sessionPersistence.列出()
        自身.索引头列表(头列表)
        if 会话号 not in 自身._头:
            raise 工作区错误("cannot validate session: session persistence holds no such session")
        return 自身._头[会话号]

    def _要求表(自身):
        """要求表已启动。"""
        if 自身._表 is None:
            raise 工作区错误('workspace registry is not started yet')
        return 自身._表

    def _要求状态(自身):
        """要求状态已启动。"""
        if 自身._状态 is None:
            raise 工作区错误('workspace registry is not started yet')
        return 自身._状态

    def _写状态(自身,状态):
        """写全局状态。"""
        结果=自身._全局.set(状态)
        自身._状态=状态
        return 结果

    def _会话已知(自身,会话号):
        """会话是否已知。"""
        活=自身.所属上下文.获取服务('sessions',False)
        if 活 is not None and 活.获取(会话号) is not None:
            return True
        if 会话号 in 自身._头:
            return True
        自身.索引头列表(自身.所属上下文.sessionPersistence.列出())
        return 会话号 in 自身._头

    def _入队写操作(自身,操作):
        """串行写。"""
        with 自身._写锁:
            自身._恢复挂起变更()
            return 操作()

def 应用(上下文):
    """在宿主组合上挂载工作区注册表。"""
    工作区注册表(上下文)
    return None

__all__=[
    '工作区标识','工作区错误','工作区未知会话错误','工作区顺序无效错误',
    '工作区注册表','工作区域规格','规范化真实路径',
]
name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
default=工作区注册表#框架槽
