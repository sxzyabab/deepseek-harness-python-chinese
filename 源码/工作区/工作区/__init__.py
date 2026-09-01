"""工作区实体注册表（`ctx.workspaceRegistry`）。对齐上游 workspace/src/index.ts。"""
import os,threading,uuid#路径、串行写与会话 id
from datetime import datetime,timezone#ISO 时间戳
from ...依赖 import cordis#Cordis
服务=cordis.服务#服务基类
from ...内核.会话 import 会话标识#会话 id 品牌
from .实体 import 工作区实体,工作区移动无效错误#实体
from .路径 import 规范化真实路径#路径规范化
from .规格 import 工作区域域规格#域 spec
__all__=[#仅中文公开名
    '工作区标识','工作区未知会话错误','工作区顺序无效错误',
    '工作区注册表','默认','名称','注入','应用','apply',
    '工作区域域规格','规范化真实路径',
]#公开面结束

名称='workspace'#Cordis 插件名
注入=['storageDomain','sessionPersistence']#强依赖

def 工作区标识(标识):#品牌构造
    """把字符串打成工作区 id 品牌。"""
    return 标识#品牌即字符串

class 工作区未知会话错误(Exception):#未知会话
    def __init__(自身,会话号):#构造
        super().__init__(f"cannot archive session '{会话号}': live sessions and session persistence hold no such session")#消息
        自身.sessionId=会话号#记下
        自身.name='WorkspaceUnknownSessionError'#错误名

class 工作区顺序无效错误(Exception):#顺序无效
    def __init__(自身,工作区号):#构造
        super().__init__(f"cannot reorder unknown workspace '{工作区号}'")#消息
        自身.workspaceId=工作区号#记下
        自身.name='WorkspaceOrderInvalidError'#错误名

def _同id列表(左,右):#id 列表同序同值
    return len(左)==len(右) and all(左[索引]==右[索引] for 索引 in range(len(左)))#逐项

def _比较头(左,右):#头排序：新者优先
    差=右.get('createdAt',0)-左.get('createdAt',0)#时间差
    if 差!=0:#时间决胜
        return 差#新者优先
    return (str(左.get('id'))>str(右.get('id')))-(str(左.get('id'))<str(右.get('id')))#id 决胜

def _同会话列表(左,右):#会话 id 列表同序同值
    return _同id列表(左,右)#复用

def 解开(值):#承诺则等待
    """承诺则等待，否则原样返回。"""
    等待=getattr(值,'wait',None) or getattr(值,'等待',None)#取 wait
    if callable(等待):#可等待
        return 等待()#等待
    return 值#同步

class 工作区注册表(服务):#耐久工作区注册表
    """耐久工作区注册表。启动等待 sessionPersistence 并完成一次性历史引导。"""
    inject=['storageDomain','sessionPersistence']#注入依赖
    def __init__(自身,上下文对象):#构造
        super().__init__(上下文对象,'workspaceRegistry')#登记服务
        自身._表=None#工作区表
        自身._全局=None#全局句柄
        自身._状态=None#内存状态
        自身._实体={}#实体缓存
        自身._头={}#头索引
        自身._会话路径={}#有效 cwd 路径
        自身._无效会话路径={}#无效原因
        自身._写锁=threading.Lock()#写链锁
        def 记住会话路径(会话号,路径):#发布有效 cwd
            自身._会话路径[会话号]=路径#记下
            自身._无效会话路径.pop(会话号,None)#清无效
        自身._宿主={#实体宿主
            'table':lambda: 自身._要求表(),
            'sessionPath':lambda 会话号: 自身._会话路径.get(会话号),
            'readSessionHeader':lambda 会话号: 自身._读会话头(会话号),
            'rememberSessionPath':记住会话路径,
        }#宿主结束
        自身.__dict__[服务.初始化]=自身._初始化#登记 Service.init

    def _初始化(自身):#服务启动
        域=解开(自身.ctx.storageDomain.open(工作区域域规格))#打开域
        def 关域():#卸载关域
            解开(域.close())#关闭域
        yield 关域#登记 effect
        自身._表=域.table('workspaces')#工作区表
        自身._全局=域.global#全局句柄
        自身._状态=域.global.get()#读状态
        自身._恢复挂起变更()#恢复挂起
        自身._校验已存状态(自身._状态)#校验
        if not 自身._状态['initialized']:#未引导
            头们=解开(自身.ctx.sessionPersistence.list())#列历史头
            自身._替换头索引(头们)#重建索引
            自身._引导(头们)#一次性引导
        elif 自身._表.size>0:#已引导且有记录
            自身._替换头索引(解开(自身.ctx.sessionPersistence.list()))#刷新索引
        自身._索引活会话()#活会话
        自身._校验已存状态(自身._要求状态())#再校验
        自身._重建实体()#实体缓存
        自身._报告过滤候选()#过滤警告

    def create(自身,路径,标题=None):#创建或复用
        规范=规范化真实路径(路径)#规范路径
        if not os.path.isdir(规范):#不是目录
            raise Exception(f"cannot create a workspace at '{规范}': path is not a directory")#拒绝
        return 自身._入队写操作(lambda: 自身._按规范创建(规范,标题))#串行写

    def get(自身,标识):#按 id 取
        return 自身._实体.get(标识)#查缓存

    def list(自身):#按耐久顺序列出
        结果=[]#有序实体
        for 标识 in 自身._要求状态()['workspaceIds']:#按顺序
            实体=自身._实体.get(标识)#取实体
            if 实体 is None:#缺失
                raise Exception(f"workspace registry order references missing workspace '{标识}'")#不一致
            结果.append(实体)#收集
        return 结果#返回

    def delete(自身,标识):#删除登记
        return 自身._入队写操作(lambda: 自身._删除已知(标识))#串行写

    def insertBefore(自身,标识,锚标识=None):#重排
        def 操作():#写操作
            状态=自身._要求状态()#当前状态
            if 标识 not in 状态['workspaceIds']:#源未知
                raise 工作区顺序无效错误(标识)#拒绝
            if 锚标识 is not None and 锚标识 not in 状态['workspaceIds']:#锚未知
                raise 工作区顺序无效错误(锚标识)#拒绝
            if 锚标识==标识:#自己锚自己
                return 状态['workspaceIds']#不变
            去掉=[项 for 项 in 状态['workspaceIds'] if 项!=标识]#去源
            位置=len(去掉) if 锚标识 is None else 去掉.index(锚标识)#插入点
            新顺序=去掉[:位置]+[标识]+去掉[位置:]#新顺序
            if _同id列表(新顺序,状态['workspaceIds']):#未变
                return 状态['workspaceIds']#不变
            解开(自身._写状态({**状态,'workspaceIds':新顺序}))#耐久写
            return 新顺序#返回
        return 自身._入队写操作(操作)#串行

    @property
    def archivedSessionIds(自身):#已归档会话
        return 自身._要求状态()['archivedSessionIds']#读状态

    def archiveSession(自身,会话号):#归档会话
        def 操作():#写操作
            if 会话号 in 自身._要求状态()['archivedSessionIds']:#已归档
                return#幂等
            if not 解开(自身._会话已知(会话号)):#确定未命中
                raise 工作区未知会话错误(会话号)#拒绝
            状态=自身._要求状态()#当前状态
            解开(自身._写状态({**状态,'archivedSessionIds':[*状态['archivedSessionIds'],会话号]}))#追加
        return 自身._入队写操作(操作)#串行

    def resolveByPath(自身,路径):#按路径解析
        规范=规范化真实路径(路径)#规范
        for 实体 in 自身._实体.values():#扫描
            if 实体.path==规范:#命中
                return 实体#返回
        return None#无人拥有

    def _按规范创建(自身,规范,标题=None):#内部创建
        for 实体 in 自身._实体.values():#复用扫描
            if 实体.path==规范:#已有
                return 实体#复用
        表=自身._要求表()#表
        状态=自身._要求状态()#状态
        标识=工作区标识(str(uuid.uuid4()))#新 id
        现在=datetime.now(timezone.utc).isoformat()#时间戳
        记录={'path':规范,'title':标题 or os.path.basename(规范),'sessionIds':[],'createdAt':现在,'updatedAt':现在}#新记录
        实体=工作区实体(自身._宿主,标识,记录)#构造实体
        自身._实体[标识]=实体#先发布缓存
        挂起状态={**状态,'pendingMutation':{'operation':'create','workspaceId':标识}}#挂起创建
        try:#写挂起
            解开(自身._写状态(挂起状态))#耐久标记
        except BaseException as 错误:#失败
            del 自身._实体[标识]#撤回缓存
            raise 错误#再抛
        try:#写记录
            解开(表.put(标识,记录))#耐久记录
        except BaseException as 错误:#失败
            del 自身._实体[标识]#撤回缓存
            try:#回滚标记
                解开(自身._写状态(状态))#恢复
            except BaseException as 回滚错误:#双失败
                raise Exception(f"workspace '{标识}' record write and pending-marker rollback both failed") from 回滚错误#聚合
            raise 错误#再抛
        try:#写顺序
            解开(自身._写状态({'initialized':True,'workspaceIds':[标识,*状态['workspaceIds']],'archivedSessionIds':状态['archivedSessionIds']}))#提交
        except BaseException as 错误:#顺序失败
            del 自身._实体[标识]#撤回缓存
            try:#回滚记录
                解开(表.delete(标识))#删行
            except BaseException as 回滚错误:#记录回滚失败
                raise Exception(f"workspace '{标识}' order write and record rollback both failed; the pending marker remains recoverable") from 回滚错误#聚合
            try:#回滚标记
                解开(自身._写状态(状态))#恢复
            except BaseException as 回滚错误:#标记回滚失败
                raise Exception(f"workspace '{标识}' order write and pending-marker rollback both failed") from 回滚错误#聚合
            raise 错误#再抛
        return 实体#返回

    def _删除已知(自身,标识):#删除已知
        实体=自身._实体.get(标识)#取实体
        if 实体 is None:#未知
            return False#幂等空操作
        状态=自身._要求状态()#当前
        下一状态={'initialized':True,'workspaceIds':[项 for 项 in 状态['workspaceIds'] if 项!=标识],'archivedSessionIds':状态['archivedSessionIds']}#去 id
        解开(自身._写状态({**下一状态,'pendingMutation':{'operation':'delete','workspaceId':标识}}))#挂起删除
        del 自身._实体[标识]#先从缓存拿掉
        try:#删表行
            解开(自身._要求表().delete(标识))#耐久删
        except BaseException as 错误:#失败
            自身._实体[标识]=实体#恢复缓存
            try:#回滚顺序
                解开(自身._写状态(状态))#恢复
            except BaseException as 回滚错误:#双失败
                del 自身._实体[标识]#与标记对齐
                raise Exception(f"workspace '{标识}' record deletion and registry-order rollback both failed") from 回滚错误#聚合
            raise 错误#再抛
        try:#清挂起
            解开(自身._写状态(下一状态))#提交
        except BaseException as 错误:#清标记失败
            自身.ctx.logger.warn(f"workspace '{标识}' was deleted but its pending marker could not be cleared: {错误}")#警告
        return True#确实删除

    def _恢复挂起变更(自身):#恢复挂起
        状态=自身._要求状态()#当前
        挂起=状态.get('pendingMutation')#挂起
        if 挂起 is None:#无挂起
            return#结束
        if 挂起['workspaceId'] in 状态['workspaceIds']:#顺序仍在
            raise Exception(f"workspace domain is inconsistent: pending {挂起['operation']} workspace '{挂起['workspaceId']}' is still present in registry order")#不一致
        解开(自身._要求表().delete(挂起['workspaceId']))#完成删除
        解开(自身._写状态({'initialized':状态['initialized'],'workspaceIds':状态['workspaceIds'],'archivedSessionIds':状态['archivedSessionIds']}))#清标记

    def _引导(自身,头们):#历史引导
        表=自身._要求表()#表
        状态=自身._要求状态()#状态
        按路径={}#路径分组
        for 头 in 头们:#每个头
            路径=自身._会话路径.get(头['id'])#有效路径
            if 路径 is None:#无效
                continue#跳过
            按路径.setdefault(路径,[]).append(头)#分组
        组=[{'path':路径,'headers':sorted(组头,key=lambda 项: (-项.get('createdAt',0),str(项.get('id')))),'newestAt':sorted(组头,key=lambda 项: -项.get('createdAt',0))[0].get('createdAt',0)} for 路径,组头 in 按路径.items()]#建组
        组.sort(key=lambda 项: (-项['newestAt'],项['path']))#组间排序
        路径到id={}#路径到工作区
        已记账={}#会话占用
        for 标识,记录 in 表.entries():#已有记录
            路径到id[记录['path']]=标识#记路径
            for 会话 in 记录['sessionIds']:#成员
                已记账[会话]=标识#记账
        for 组项 in 组:#每组
            标识=路径到id.get(组项['path'])#已有
            if 标识 is None:#需新建
                会话们=[头['id'] for 头 in 组项['headers'] if 头['id'] not in 已记账]#未记账
                if len(会话们)==0:#全已记账
                    continue#下一组
                标识=工作区标识(str(uuid.uuid4()))#新 id
                创建时刻=datetime.fromtimestamp(组项['newestAt']/1000.0,tz=timezone.utc).isoformat() if 组项['newestAt']>1e12 else datetime.fromtimestamp(组项['newestAt'],tz=timezone.utc).isoformat()#时间
                记录={'path':组项['path'],'title':os.path.basename(组项['path']),'sessionIds':会话们,'createdAt':创建时刻,'updatedAt':创建时刻}#记录
                解开(表.put(标识,记录))#写入
                路径到id[组项['path']]=标识#记路径
                for 会话 in 会话们:#记账
                    已记账[会话]=标识#记下
                continue#下一组
            当前=表.get(标识)#已有
            历史=[头['id'] for 头 in 组项['headers'] if 已记账.get(头['id']) in (None,标识)]#历史成员
            历史集=set(历史)#集合
            会话们=历史+[会话 for 会话 in 当前['sessionIds'] if 会话 not in 历史集]#合并
            if _同会话列表(当前['sessionIds'],会话们):#未变
                continue#下一组
            解开(表.update(标识,lambda 记录: {**记录,'sessionIds':会话们,'updatedAt':datetime.now(timezone.utc).isoformat()}))#更新
            for 会话 in 历史:#记账历史
                已记账[会话]=标识#记下
        组排名={组项['path']:组项['newestAt'] for 组项 in 组}#路径新近度
        先前排名={标识:索引 for 索引,标识 in enumerate(状态['workspaceIds'])}#先前顺序
        工作区们=sorted(表.entries(),key=lambda 项: (-(组排名.get(项[1]['path']) or datetime.fromisoformat(项[1]['createdAt'].replace('Z','+00:00')).timestamp()),先前排名.get(项[0],2**62),str(项[0])))#排序
        工作区id们=[标识 for 标识,_ in 工作区们]#只留 id
        if not _同id列表(状态['workspaceIds'],工作区id们):#顺序变了
            解开(自身._写状态({'initialized':False,'workspaceIds':工作区id们,'archivedSessionIds':状态['archivedSessionIds']}))#先写未标记
        解开(自身._写状态({'initialized':True,'workspaceIds':工作区id们,'archivedSessionIds':状态['archivedSessionIds']}))#提交已初始化

    def _校验已存状态(自身,状态):#校验状态
        表=自身._要求表()#表
        顺序=set()#顺序集合
        for 标识 in 状态['workspaceIds']:#顺序 id
            if 标识 in 顺序:#重复
                raise Exception(f"workspace domain is inconsistent: registry order repeats workspace '{标识}'")#不一致
            if 表.get(标识) is None:#表缺行
                raise Exception(f"workspace domain is inconsistent: registry order references missing workspace '{标识}'")#不一致
            顺序.add(标识)#记下
        if 状态['initialized'] and len(顺序)!=表.size:#孤儿
            孤儿=next((标识 for 标识,_ in 表.entries() if 标识 not in 顺序),None)#找孤儿
            raise Exception(f"workspace domain is inconsistent: workspace '{孤儿}' is absent from registry order")#不一致
        路径占用={}#路径
        会话占用={}#会话
        for 标识,记录 in 表.entries():#每条记录
            if 记录['path'] in 路径占用:#路径冲突
                raise Exception(f"workspace domain is inconsistent: path '{记录['path']}' is claimed by both workspace '{路径占用[记录['path']]}' and workspace '{标识}'")#不一致
            路径占用[记录['path']]=标识#记下
            for 会话 in 记录['sessionIds']:#成员
                if 会话 in 会话占用:#会话冲突
                    raise Exception(f"workspace domain is inconsistent: session '{会话}' is accounted by both workspace '{会话占用[会话]}' and workspace '{标识}'")#不一致
                会话占用[会话]=标识#记下

    def _重建实体(自身):#重建缓存
        自身._实体.clear()#清空
        for 标识 in 自身._要求状态()['workspaceIds']:#按顺序
            记录=自身._要求表().get(标识)#取记录
            自身._实体[标识]=工作区实体(自身._宿主,标识,记录)#构造

    def _替换头索引(自身,头们):#重建头索引
        自身._头.clear()#清头
        自身._会话路径.clear()#清路径
        自身._无效会话路径.clear()#清原因
        自身._索引头们(头们)#重建

    def _索引头们(自身,头们):#索引一批头
        for 头 in 头们:#逐个
            解开(自身._索引头(头))#索引

    def _索引头(自身,头):#索引一头
        自身._头[头['id']]=头#记下
        自身._会话路径.pop(头['id'],None)#先清
        if 头.get('cwd') is None:#无 cwd
            自身._无效会话路径[头['id']]='header has no cwd'#原因
            return#结束
        try:#解析 cwd
            路径=规范化真实路径(头['cwd'])#规范
            if not os.path.isdir(路径):#非目录
                自身._无效会话路径[头['id']]=f"cwd '{头['cwd']}' is not a directory"#原因
                return#结束
            自身._会话路径[头['id']]=路径#有效
            自身._无效会话路径.pop(头['id'],None)#清无效
        except OSError:#解析失败
            自身._无效会话路径[头['id']]=f"cwd '{头['cwd']}' does not resolve"#原因

    def _索引活会话(自身):#索引活会话
        会话存储=自身.ctx.get('sessions')#可选
        if 会话存储 is None:#无活会话
            return#跳过
        自身._索引头们([会话.header for 会话 in 会话存储.list()])#索引活头

    def _报告过滤候选(自身):#报告过滤
        for 实体 in 自身._实体.values():#每个实体
            记录=自身._要求表().get(实体.id)#记录
            for 会话 in 记录['sessionIds']:#成员
                路径=自身._会话路径.get(会话)#有效路径
                if 路径==记录['path']:#匹配
                    continue#留下
                原因=自身._无效会话路径.get(会话) or (f"canonical cwd '{路径}' differs from workspace path '{记录['path']}'" if 会话 in 自身._头 else 'session header is missing')#原因
                自身.ctx.logger.warn(f"workspace '{实体.id}' filtered session '{会话}' from membership: {原因}")#警告

    def _读会话头(自身,会话号):#读会话头
        活=自身.ctx.get('sessions')#活会话
        if 活 is not None:#有活存储
            会话=活.get(会话号)#查活
            if 会话 is not None:#活着
                自身._头[会话号]=会话.header#刷新
                return 会话.header#返回
        缓存=自身._头.get(会话号)#缓存
        if 缓存 is not None:#命中
            return 缓存#返回
        头们=解开(自身.ctx.sessionPersistence.list())#列持久化
        自身._索引头们(头们)#刷新
        头=自身._头.get(会话号)#再查
        if 头 is None:#仍无
            raise Exception(f"cannot validate session '{会话号}': session persistence holds no such session")#拒绝
        return 头#返回

    def _要求表(自身):#要求表已启动
        if 自身._表 is None:#未启动
            raise Exception('workspace registry is not started yet')#拒绝
        return 自身._表#返回

    def _要求状态(自身):#要求状态已启动
        if 自身._状态 is None:#未启动
            raise Exception('workspace registry is not started yet')#拒绝
        return 自身._状态#返回

    def _写状态(自身,状态):#写全局状态
        结果=自身._全局.set(状态)#耐久写
        自身._状态=状态#更新内存
        return 结果#返回承诺

    def _会话已知(自身,会话号):#会话是否已知
        if 自身.ctx.get('sessions') and 自身.ctx.get('sessions').get(会话号) is not None:#活
            return True#已知
        if 会话号 in 自身._头:#已索引
            return True#已知
        自身._索引头们(解开(自身.ctx.sessionPersistence.list()))#刷新
        return 会话号 in 自身._头#再查

    def _入队写操作(自身,操作):#串行写
        with 自身._写锁:#持锁
            自身._恢复挂起变更()#先恢复
            return 操作()#跑操作

def 应用(上下文对象):#安装注册表
    """在宿主组合上挂载工作区注册表。"""
    工作区注册表(上下文对象)#构造并登记
    return None#无额外拆除

apply=应用#Cordis 插件入口
默认=工作区注册表#默认导出
