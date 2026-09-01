"""实时会话队列、任务与投影控制流。

对齐上游 `session-controller/src/control.ts`。公开面仅中文名。
"""
import threading#流等待
from ...工具.双端队列 import 双端队列#缓冲
from .工具 import 取字段,信号已中止#辅助

__all__=['会话控制控制器']#仅中文公开名

class _控制队列:#单代控制流缓冲
    """缓冲控制帧。"""
    def __init__(自身):#新队列
        """建立空缓冲。"""
        自身._缓冲=双端队列()#帧
        自身._事件=threading.Event()#等待
        自身._已结束=False#结束

    def 推(自身,帧):#推帧
        """入队并唤醒。"""
        if 自身._已结束:#已结束
            return#忽略
        自身._缓冲.尾推(帧)#入队
        自身._事件.set()#唤醒

    def 结束(自身):#结束
        """关闭队列。"""
        自身._已结束=True#标记
        自身._事件.set()#唤醒

    def 迭代(自身,信号):#产出帧
        """直到取消或结束。"""
        while (not 自身._已结束) and (not 信号已中止(信号)):#活跃
            帧=自身._缓冲.头弹()#取帧
            if 帧 is not None:#有帧
                yield 帧#产出
                continue#继续
            自身._事件.clear()#清事件
            if 自身._缓冲.大小>0 or 自身._已结束 or 信号已中止(信号):#竞态
                continue#重试
            自身._事件.wait(0.05)#短等
        while 自身._缓冲.大小>0 and (not 信号已中止(信号)):#排空
            帧=自身._缓冲.头弹()#取
            if 帧 is not None:#有
                yield 帧#产出

class 会话控制控制器:#控制流
    """拥有宿主范围会话控制流。"""

    def __init__(自身,上下文):#构造
        """订阅会话、投影与任务变化。"""
        自身._上下文=上下文#Cordis
        自身._流们=set()#活跃流
        上下文.on('session/event',lambda 会话,事件:自身._会话事件(会话,事件))#事件
        上下文.sessionProjections.onChanged(lambda 会话,键,值,序号:自身._广播({'type':'projection','sessionId':取字段(会话,'id'),'key':键,'value':值,'seq':序号}))#投影
        def 挂任务(任务上下文):#jobs
            """订阅任务变化。"""
            任务上下文.jobs.onJobsChanged(lambda 所有者:自身._任务变化(所有者))#监听
        上下文.inject(['jobs'],挂任务)#inject
        上下文.on('session/created',lambda 会话:自身._会话创建(会话))#创建
        上下文.effect(lambda:自身._拆除(),'session-controller.control')#拆除

    def _拆除(自身):#关闭全部流
        """结束全部代。"""
        for 流 in list(自身._流们):#逐个
            流.结束()#结束
        自身._流们.clear()#清空

    def control(自身,信号):#打开一代控制流
        """产出基线后 live 帧。"""
        if 信号已中止(信号):#取消
            return#空
        队列=_控制队列()#新代
        自身._流们.add(队列)#登记
        try:#产出
            yield {'type':'baseline','value':自身._基线()}#基线
            yield from 队列.迭代(信号)#增量
        finally:#清理
            自身._流们.discard(队列)#移除
            队列.结束()#结束

    def _基线(自身):#读当前基线
        """同步读完整控制基线。"""
        会话们=自身._上下文.sessions.list()#全部会话
        队列们={}#队列
        任务们={}#任务
        for 会话 in 会话们:#逐个
            标识=取字段(会话,'id')#id
            智能体=自身._上下文.agents.get(标识)#智能体
            队列们[标识]=[] if 智能体 is None or 取字段(智能体,'session') is not 会话 else []#占位队列视图
            任务们[标识]=自身._任务用于(智能体)#任务
        投影们={}#投影
        for 会话 in 会话们:#投影基线
            快照=自身._上下文.sessionProjections.snapshot(会话)#快照
            投影们[取字段(会话,'id')]={'asOfSeq':取字段(快照,'asOfSeq'),'values':取字段(快照,'values')}#块
        return {'queues':队列们,'jobs':任务们,'projections':投影们}#基线

    def _任务用于(自身,智能体):#列任务
        """读智能体任务快照。"""
        任务服务=自身._上下文.get('jobs')#jobs
        if 任务服务 is None:#无
            return []#空
        return 任务服务.list(智能体)#列表

    def _会话创建(自身,会话):#新会话
        """新会话时补 jobs 帧。"""
        任务们=自身._任务用于(自身._上下文.agents.get(取字段(会话,'id')))#任务
        if len(任务们)>0:#有任务
            自身._广播({'type':'jobs','sessionId':取字段(会话,'id'),'jobs':任务们})#广播

    def _会话事件(自身,会话,事件):#会话事件
        """inbox 拼接时广播 queue 帧。"""
        if 取字段(事件,'type')!='agent/inbox/spliced':#非拼接
            return#忽略
        智能体=自身._上下文.agents.get(取字段(会话,'id'))#智能体
        if 智能体 is None or 取字段(智能体,'session') is not 会话:#不匹配
            return#忽略
        自身._广播({'type':'queue','sessionId':取字段(会话,'id'),'items':[]})#占位队列帧

    def _任务变化(自身,所有者):#任务变化
        """广播 jobs 帧。"""
        if 所有者 is not None:#单所有者
            自身._广播({'type':'jobs','sessionId':取字段(所有者,'id'),'jobs':自身._任务用于(所有者)})#广播
            return#结束
        for 会话 in 自身._上下文.sessions.list():#全量
            自身._广播({'type':'jobs','sessionId':取字段(会话,'id'),'jobs':自身._任务用于(自身._上下文.agents.get(取字段(会话,'id')))})#广播

    def _广播(自身,帧):#广播
        """向全部代推送。"""
        for 流 in 自身._流们:#逐个
            流.推(帧)#推
