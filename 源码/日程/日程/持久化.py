'日程对共享会话耐久屏障的本包用法'
from ...依赖 import cordis#外部依赖胶水
from .异常 import 日程持久错误#本包异常

def 冲洗日程持久(上下文,会话):
    '要求一次成功的共享持久检查点。至少一个监听器显式确认已完成耐久工作之后'
    try:#调用共享屏障
        确认=上下文.sessions.flush(会话)#flush 当前前缀，同步
        if not 确认:#无人确认
            raise 日程持久错误()#失败
    except 日程持久错误:#已是本包错误
        raise#原样抛
    except Exception as 错误:#其它拒绝
        raise 日程持久错误(错误)#包成本包错误
