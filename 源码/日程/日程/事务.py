"""日程读与耐久变更的智能体作用域串行化。"""
import threading,weakref#互斥与弱表
链尾=weakref.WeakKeyDictionary()#每个智能体当前事务链尾锁

def 跑日程事务(智能体,操作):#按智能体串行跑事务
    """在其精确智能体的前一事务之后跑完一次完整日程事务。"""
    锁=链尾.get(智能体)#取出已有锁
    if 锁 is None:#尚未有锁
        锁=threading.Lock()#新建互斥
        链尾[智能体]=锁#记下
    锁.acquire()#独占
    try:#跑完整操作
        return 操作()#交回操作结果
    finally:#本事务已离开调用栈
        锁.release()#释放
        if 链尾.get(智能体) is 锁:#没有更新的后继则清掉
            try:#弱键可能已失效
                del 链尾[智能体]#清掉链尾
            except KeyError:#键已消失
                pass#吞掉：智能体已无引用
