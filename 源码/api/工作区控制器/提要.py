'重连安全的工作区基线与增量。replace 帧只由访问过滤发出，提要本身不产它'
import threading#关注者唤醒
from ...工具.双端队列 import 双端队列#帧缓冲
from ...工作区.工作区 import 工作区标识#品牌化 id
from ...工作区.工作区.规格 import 工作区记录,工作区域状态#域记录与全局状态
from ..网关.流协议 import 已中止,若中止则抛 as 若已中止则抛出#寿命

__all__=['工作区视图','工作区提要']


def 工作区视图(工作区):
    '把注册表实体投影成远程值。工作区是注册表实体'
    return {
        'workspaceId':工作区.id,#登记 id
        'path':工作区.path,#宿主目录
        'title':工作区.title,#标题
        'sessionIds':list(工作区.sessionIds),#账本副本
        'createdAt':工作区.createdAt,#创建时刻
        'updatedAt':工作区.updatedAt,#最近变更
    }#投影


def 字符串列相同(左,右):
    '两列字符串是否同长且逐项相同'
    if len(左)!=len(右):#长度不同
        return False#不同
    下标=0#游标
    while 下标<len(左):#逐项
        if 左[下标]!=右[下标]:#某一项不同
            return False#不同
        下标+=1#下一项
    return True#相同


class 工作区关注者:
    '一代 follow 的帧缓冲。推入或关闭会唤醒正在读的一方'

    def __init__(自身):
        '建立空缓冲'
        自身.帧=双端队列()#待读帧
        自身.锁=threading.Lock()#域写入线程和 follow 读取线程共用这一圈缓冲
        自身.唤醒=threading.Event()#有帧或已关闭
        自身.已关闭=False#本代结束

    def 推入(自身,帧):
        '缓冲一帧并唤醒读取。已关闭的代不再接收'
        with 自身.锁:#改缓冲
            if 自身.已关闭:#已结束
                return#丢掉
            自身.帧.尾推(帧)#入队
        自身.唤醒.set()#唤醒

    def 关闭(自身):
        '结束本代并唤醒读取'
        with 自身.锁:#改标记
            if 自身.已关闭:#已经结束
                return#空
            自身.已关闭=True#标记
        自身.唤醒.set()#唤醒

    def 读取(自身,信号):
        '在信号未中止且本代未关闭时产出缓冲帧。信号是中止信号'
        while True:#直到关闭或中止
            with 自身.锁:#取一帧
                if 自身.已关闭 or 已中止(信号):#本代结束
                    return#停
                帧=自身.帧.头弹()#可能为空
            if 帧 is not None:#有帧
                yield 帧#交出
                continue#再取
            自身.等待(信号)#等下一帧或中止

    def 等待(自身,信号):
        '阻塞到有帧、本代关闭或信号中止。中止最多一个轮询间隔后看见'
        while True:#直到条件成立
            with 自身.锁:#看当前
                if 已中止(信号) or 自身.已关闭 or 自身.帧.大小>0:#可以返回
                    break#停
            自身.唤醒.wait(0.05)#等推入或关闭
        自身.唤醒.clear()#这一轮已看过


class 工作区提要:
    '观察工作区域，并向全部打开的 follow 代发布增量'

    def __init__(自身,上下文):
        '从注册表当前基线开始听 domain/changed'
        自身.ctx=上下文#宿主上下文
        基线=上下文.workspaceRegistry.list()#当前工作区
        自身.已知标识=set(str(工作区.id) for 工作区 in 基线)#见过的 id
        自身.顺序=[str(工作区.id) for 工作区 in 基线]#显示顺序
        自身.归档=[str(标识) for 标识 in 上下文.workspaceRegistry.archivedSessionIds]#归档集
        自身.钉住=[str(标识) for 标识 in 上下文.workspaceRegistry.pinnedSessionIds]#钉住集
        自身.关注者集合=set()#打开的代

        def 域变更(变更):
            '把域变更译成 follow 增量'
            自身.变更(变更)#翻译

        上下文.监听('domain/changed',域变更)#订阅

        def 登记拆除():
            '卸载时关闭全部代'

            def 清理():
                '关闭并清空'
                for 关注者 in list(自身.关注者集合):#每一代
                    关注者.关闭()#结束
                自身.关注者集合.clear()#清空

            return 清理#拆除器

        上下文.副作用(登记拆除,'workspace-controller.feed')#寿命

    def 读取基线(自身):
        '同步读完整投影：工作区、归档会话、钉住会话'
        return {
            'items':[工作区视图(工作区) for 工作区 in 自身.ctx.workspaceRegistry.list()],#工作区
            'archivedSessionIds':list(自身.ctx.workspaceRegistry.archivedSessionIds),#归档
            'pinnedSessionIds':list(自身.ctx.workspaceRegistry.pinnedSessionIds),#钉住
        }#基线

    def follow(自身,信号):
        '先产出一份完整基线，再产出有序增量。信号取消本代'
        若已中止则抛出(信号)#已取消则拒绝
        关注者=工作区关注者()#本代
        自身.关注者集合.add(关注者)#登记
        try:#读完或失败都摘掉
            yield {'type':'baseline','value':自身.读取基线()}#开口基线
            yield from 关注者.读取(信号)#后续增量
        finally:#本代结束
            自身.关注者集合.discard(关注者)#摘掉
            关注者.关闭()#不再接收

    def 发布(自身,帧):
        '把一帧增量交给当前每一代'
        for 关注者 in list(自身.关注者集合):#快照
            关注者.推入(帧)#缓冲

    def 变更(自身,变更):
        '把一条 domain/changed 译成增量。变更是域事件 dict'
        if 变更['domain']!='workspace':#不是本域
            return#忽略
        if 变更['table']=='':#全局状态
            if 变更['operation']!='put':#不是写入
                return#忽略
            状态=工作区域状态(变更['value'])#校验后的全局状态
            下一顺序=[str(标识) for 标识 in 状态['workspaceIds']]#新顺序
            顺序变了=not 字符串列相同(自身.顺序,下一顺序)#顺序是否变
            for 标识 in 状态['workspaceIds']:#新出现的工作区
                if str(标识) in 自身.已知标识:#已经见过
                    continue#下一个
                工作区=自身.ctx.workspaceRegistry.get(标识)#实体
                if 工作区 is None:#顺序指向缺失记录
                    raise RuntimeError('committed Workspace registry references missing Workspace "'+str(标识)+'"')#拒绝
                自身.已知标识.add(str(标识))#记下
                自身.发布({'type':'upsert','workspace':工作区视图(工作区)})#新增
            自身.顺序=下一顺序#换顺序
            if 顺序变了:#顺序变了
                自身.发布({'type':'order','workspaceIds':list(状态['workspaceIds'])})#顺序帧
            下一归档=[str(标识) for 标识 in 状态['archivedSessionIds']]#新归档
            if not 字符串列相同(自身.归档,下一归档):#归档变了
                自身.归档=下一归档#记下
                自身.发布({'type':'archived','archivedSessionIds':list(状态['archivedSessionIds'])})#归档帧
            下一钉住=[str(标识) for 标识 in 状态['pinnedSessionIds']]#新钉住
            if not 字符串列相同(自身.钉住,下一钉住):#钉住变了
                自身.钉住=下一钉住#记下
                自身.发布({'type':'pinned','pinnedSessionIds':list(状态['pinnedSessionIds'])})#钉住帧
            return#全局处理完
        if 变更['table']!='workspaces':#不是工作区表
            return#忽略
        if 变更['operation']=='deleted':#删除
            键=str(变更['key'])#记录键
            if 键 not in 自身.已知标识:#没交付过
                return#忽略
            自身.已知标识.remove(键)#忘掉
            自身.发布({'type':'remove','workspaceId':工作区标识(变更['key'])})#移除
            return#删除处理完
        if str(变更['key']) not in 自身.已知标识:#还没进入顺序
            return#忽略
        记录=工作区记录(变更['value'])#校验记录
        标识=工作区标识(变更['key'])#品牌化
        自身.发布({
            'type':'upsert',
            'workspace':{
                'workspaceId':标识,#id
                'path':记录['path'],#目录
                'title':记录['title'],#标题
                'sessionIds':list(记录['sessionIds']),#账本
                'createdAt':记录['createdAt'],#创建
                'updatedAt':记录['updatedAt'],#变更
            },
        })#更新
