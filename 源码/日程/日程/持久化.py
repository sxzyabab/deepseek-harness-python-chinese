"""日程对共享会话耐久屏障的本包用法。"""
from ...依赖 import cordis#外部依赖胶水
class 日程持久错误(Exception):#日程持久失败
    """未能证明当前在线前缀到达了持久监听器。"""
    def __init__(自身,原因=None):#构造持久失败
        """构造一条被包含的持久失败。"""
        Exception.__init__(自身,'Schedule persistence did not complete.')#固定文案
        自身.name='SchedulePersistenceError'#错误名
        自身.__cause__=原因#可选包裹原因

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待承诺
    return 值#同步值

def 冲洗日程持久(上下文,会话):#flush日程持久
    """要求一次成功的共享持久检查点。至少一个监听器显式确认已完成耐久工作之后。"""
    try:#调用共享屏障
        确认=解开(上下文.sessions.flush(会话))#flush 当前前缀
        if not 确认:#无人确认
            raise 日程持久错误()#失败
    except 日程持久错误:#已是本包错误
        raise#原样抛
    except Exception as 错误:#其它拒绝
        raise 日程持久错误(错误)#包成本包错误
