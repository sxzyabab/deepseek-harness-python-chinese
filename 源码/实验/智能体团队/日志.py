import threading#串行队尾
from ...基础设施.js特性 import PromiseEX as 期约#事务与刷新的异步结果
from .异常 import 团队错误#领域错误

__all__=['团队日志']#仅中文公开名

class 团队日志:#团队日志
    '拥有按 Lead 的事务顺序与已提交 Team 事件发布'
    def __init__(自身,上下文,提交时):#构造
        '记下上下文与提交回调'
        自身.ctx=上下文#服务上下文
        自身._提交时=提交时#提交回调
        自身._尾={}#每 Lead 队尾期约
        自身._锁=threading.Lock()#队尾表锁

    def 状态(自身,根):#读投影状态
        '读取一个精确 live Lead 的权威 Team 状态'
        投影=自身.ctx.sessionProjections.stateOf(根.session,'agentTeam')#取投影
        if 投影 is None:#未注册
            raise 团队错误('Agent Teams projection is not registered','TEAM_INVALID_ARGUMENT')#未注册
        if 'failure' in 投影:#有失败
            raise 团队错误(str(投影['failure']),'TEAM_INVALID_ARGUMENT')#投影失败
        return 投影#可用状态

    def 事务(自身,根标识,操作):#串行事务
        '串行化一个 Lead 的变更操作。操作无参，返回值或期约；本方法返回期约，兑现值是操作结果'
        本尾=期约()#本操作结清后兑现，后来的事务排在它后面
        with 自身._锁:#交换队尾必须原子，否则两个线程会排在同一个前驱后面
            if 根标识 in 自身._尾:#已有前驱
                前驱=自身._尾[根标识]#排在前驱之后
            else:#没有前驱
                前驱=期约()#空前驱
                前驱.解决(None)#已结算，立即可跑
            自身._尾[根标识]=本尾#更新队尾
        def 运行操作(前驱结果):#前驱结算后
            '无论前驱成败都运行本操作'
            return 操作()#操作的返回值或期约
        运行=前驱.然后(运行操作,运行操作)#前驱成功或失败都轮到本操作
        def 结清(运行结果):#本操作结算后
            '清掉仍是自己的队尾并放行后来的事务'
            with 自身._锁:#读写队尾表
                if 根标识 in 自身._尾 and 自身._尾[根标识] is 本尾:#仍是自己
                    del 自身._尾[根标识]#清尾
            本尾.解决(None)#放行后来的事务，不传递本操作的成败
        运行.然后(结清,结清)#队尾只跟踪结算，不观察对错
        return 运行#调用方观察本操作的结果

    def 追加并刷新(自身,根,类型,数据):#追加并 flush
        '在发布前追加并 checkpoint 一条根拥有的 Team 事件。返回期约，flush 成功并通知提交后兑现'
        根.session.append(类型,数据)#追加事件
        def 通知提交(刷新值):#flush 成功后
            '通知提交回调'
            自身._提交时(根)#通知提交
        return 自身.ctx.sessions.flush(根.session).然后(通知提交)#flush 落盘后通知
