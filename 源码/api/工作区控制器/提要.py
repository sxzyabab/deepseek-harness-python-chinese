"""重连安全的工作区基线与增量生产者。"""
import threading#关注者等待
from ...工具.双端队列 import 双端队列#帧缓冲
from .远程错误与中止 import 已中止,远程错误#中止与远程错误

__all__=['工作区视图','工作区提要']#仅中文公开名

def 工作区视图(工作区):
    """把注册表实体投影为 Remote 值。工作区为本包对象。"""
    会话列表=工作区.sessionIds if 工作区.sessionIds is not None else []#会话 id 列表
    return {#分离投影
        'workspaceId':工作区.id,#id
        'path':工作区.path,#路径
        'title':工作区.title,#标题
        'sessionIds':list(会话列表),#会话 id 列表
        'createdAt':工作区.createdAt,#创建时间
        'updatedAt':工作区.updatedAt,#更新时间
    }#投影结束

def 变更工作区视图(工作区标识,值,工作区记录解析):
    """把域记录解析为工作区视图。值为线协议 dict。"""
    记录=工作区记录解析(值)#解析记录，记录为 dict
    会话列表=记录['sessionIds'] if 'sessionIds' in 记录 and 记录['sessionIds'] is not None else []#会话
    return {#视图
        'workspaceId':工作区标识,#id
        'path':记录['path'],#路径
        'title':记录['title'],#标题
        'sessionIds':list(会话列表),#会话
        'createdAt':记录['createdAt'],#创建
        'updatedAt':记录['updatedAt'],#更新
    }#结束

def 字符串列相同(左,右):
    """两列字符串是否逐项相同。"""
    if len(左)!=len(右):#长度
        return False#不同
    return all(左[i]==右[i] for i in range(len(左)))#逐项

class _关注者:
    """缓冲 follow 帧直到关闭。"""
    def __init__(自身):
        """建立空缓冲。"""
        自身._帧=双端队列()#帧队列
        自身._事件=threading.Event()#等待事件
        自身._已关闭=False#是否关闭

    def 推(自身,帧):
        """缓冲一帧并唤醒读取方。"""
        if 自身._已关闭:#已关
            return#忽略
        自身._帧.尾推(帧)#入队
        自身._事件.set()#唤醒

    def 关(自身):
        """结束本代。"""
        if 自身._已关闭:#已关
            return#跳过
        自身._已关闭=True#标记
        自身._事件.set()#唤醒

    def 读(自身,信号):
        """在信号未中止前产出缓冲帧。"""
        while (not 自身._已关闭) and (not 已中止(信号)):#仍活跃
            帧=自身._帧.头弹()#取帧
            if 帧 is not None:#有帧
                yield 帧#产出
                continue#继续
            if 自身._已关闭 or 已中止(信号):#结束
                break#退出
            自身._事件.clear()#清事件
            if 自身._帧.大小>0 or 自身._已关闭 or 已中止(信号):#竞态
                continue#重试
            自身._事件.wait(0.05)#短等待
        while 自身._帧.大小>0 and (not 已中止(信号)):#排空
            帧=自身._帧.头弹()#取帧
            if 帧 is not None:#有帧
                yield 帧#产出

class 工作区提要:
    """拥有工作区域观察与全部活跃 follow 代。"""

    def __init__(自身,上下文,工作区记录解析,工作区域状态解析,工作区标识函数):
        """从注册表基线开始观察 domain/changed。"""
        自身._上下文=上下文#Cordis 上下文
        自身._关注者集合=set()#活跃关注者
        自身._工作区记录解析=工作区记录解析#记录解析
        自身._工作区域状态解析=工作区域状态解析#域状态解析
        自身._工作区标识=工作区标识函数#品牌化 id
        基线=上下文.workspaceRegistry.list()#当前列表
        自身._已知标识=set(str(项.id) for 项 in 基线)#已知 id
        自身._顺序=[str(项.id) for 项 in 基线]#顺序
        归档=上下文.workspaceRegistry.archivedSessionIds#归档
        自身._归档=[str(项) for 项 in (归档 if 归档 is not None else [])]#归档
        def 域变更(变更):
            """订阅域变更。"""
            自身._变更(变更)#委托
        def 拆除提要():
            """登记拆除。"""
            自身._拆除()#委托
        上下文.监听('domain/changed',域变更)#订阅域变更
        上下文.副作用(拆除提要,'workspace-controller.feed')#登记拆除

    def _拆除(自身):
        """关闭并清空全部 follow 代。"""
        for 关注者 in list(自身._关注者集合):#逐个
            关注者.关()#关闭
        自身._关注者集合.clear()#清空

    def 基线(自身):
        """同步读完整基线。"""
        归档=自身._上下文.workspaceRegistry.archivedSessionIds#归档
        return {#基线
            'items':[工作区视图(项) for 项 in 自身._上下文.workspaceRegistry.list()],#工作区
            'archivedSessionIds':list(归档 if 归档 is not None else []),#归档
        }#结束

    def follow(自身,信号):
        """先产出基线，再产出有序增量。"""
        if 已中止(信号):#已取消
            return#空生成器
        关注者=_关注者()#新代
        自身._关注者集合.add(关注者)#登记
        try:
            yield {'type':'baseline','value':自身.基线()}#基线帧
            yield from 关注者.读(信号)#增量帧
        finally:
            自身._关注者集合.discard(关注者)#移除
            关注者.关()#关闭

    def _发布(自身,帧):
        """广播一帧增量。"""
        for 关注者 in 自身._关注者集合:#逐个
            关注者.推(帧)#推送

    def _变更(自身,变更):
        """把域变更翻译成 follow 增量。变更为 dict。"""
        if 变更['domain']!='workspace':#非工作区域
            return#忽略
        表=变更['table']#表名
        if 表=='':#全局状态行
            if 变更['operation']!='put':#只处理 put
                return#跳过
            状态=自身._工作区域状态解析(变更['value'])#解析状态，状态为 dict
            标识列=状态['workspaceIds'] if 'workspaceIds' in 状态 and 状态['workspaceIds'] is not None else []#顺序
            下一顺序=[str(标识) for 标识 in 标识列]#顺序
            顺序变了=not 字符串列相同(自身._顺序,下一顺序)#是否变序
            for 标识 in 标识列:#新 id
                键=str(标识)#字符串键
                if 键 in 自身._已知标识:#已知
                    continue#跳过
                工作区=自身._上下文.workspaceRegistry.get(标识)#取实体
                if 工作区 is None:#缺失
                    raise 远程错误('gateway/internal','committed Workspace registry references missing Workspace "'+键+'"',{})#不一致
                自身._已知标识.add(键)#记下
                自身._发布({'type':'upsert','workspace':工作区视图(工作区)})#upsert
            自身._顺序=下一顺序#更新顺序
            if 顺序变了:#顺序变更
                自身._发布({'type':'order','workspaceIds':list(标识列)})#order
            归档列=状态['archivedSessionIds'] if 'archivedSessionIds' in 状态 and 状态['archivedSessionIds'] is not None else []#归档
            下一归档=[str(项) for 项 in 归档列]#归档
            if not 字符串列相同(自身._归档,下一归档):#归档变更
                自身._归档=下一归档#更新
                自身._发布({'type':'archived','archivedSessionIds':list(归档列)})#archived
            return#全局处理完
        if 表!='workspaces':#其它表
            return#忽略
        操作=变更['operation']#操作
        键=变更['key']#键
        if 操作=='deleted':#删除
            if 键 not in 自身._已知标识:#未知
                return#忽略
            自身._已知标识.discard(键)#移除
            自身._发布({'type':'remove','workspaceId':自身._工作区标识(键)})#remove
            return
        if 键 not in 自身._已知标识:#未知 upsert
            return#忽略
        自身._发布({'type':'upsert','workspace':变更工作区视图(键,变更['value'],自身._工作区记录解析)})#upsert
