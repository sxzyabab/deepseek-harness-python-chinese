import threading#串行队尾
from .错误 import 团队错误#领域错误

__all__=['团队日志']#仅中文公开名

class 团队日志:#团队日志
    """拥有按 Lead 的事务顺序与已提交 Team 事件发布。"""
    def __init__(自身,上下文,提交时):#构造
        """记下上下文与提交回调。"""
        自身.ctx=上下文#服务上下文
        自身._提交时=提交时#提交回调
        自身._尾={}#每 Lead 队尾门
        自身._锁=threading.Lock()#队尾表锁

    def 状态(自身,根):#读投影状态
        """读取一个精确 live Lead 的权威 Team 状态。"""
        投影=自身.ctx.sessionProjections.stateOf(根.session,'agentTeam')#取投影
        if 投影 is None:#未注册
            raise 团队错误('Agent Teams projection is not registered','TEAM_INVALID_ARGUMENT')#未注册
        if 'failure' in 投影:#有失败
            raise 团队错误(str(投影['failure']),'TEAM_INVALID_ARGUMENT')#投影失败
        return 投影#可用状态

    def 事务(自身,根标识,操作):#串行事务
        """串行化一个 Lead 的变更操作。"""
        with 自身._锁:#取先前尾
            先前=自身._尾[根标识] if 根标识 in 自身._尾 else None#前一尾
            门=threading.Event()#本操作门
            自身._尾[根标识]=门#更新队尾
        if 先前 is not None:#等先前
            先前.wait()#前后都跑
        try:#跑操作
            return 操作()#结果
        finally:#清尾
            门.set()#放行后来
            with 自身._锁:#仍是自己则清
                if 根标识 in 自身._尾 and 自身._尾[根标识] is 门:#仍是自己
                    自身._尾.pop(根标识,None)#清尾

    def 追加并刷新(自身,根,类型,数据):#追加并 flush
        """在发布前追加并 checkpoint 一条根拥有的 Team 事件。"""
        根.session.append(类型,数据)#追加事件
        自身.ctx.sessions.flush(根.session)#flush 落盘
        自身._提交时(根)#通知提交
