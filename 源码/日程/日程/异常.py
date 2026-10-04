'日程日志、输入与持久失败'
__all__=['日程日志错误','日程输入错误','日程持久错误']#仅中文公开名

class 日程日志错误(Exception):#持久日志错误
    '畸形或转移非法的持久日程数据错误'
    code='corrupt_schedule_log'#日志损坏码
    def __init__(自身,消息):#构造日志错误
        '构造一条持久日志失败'
        Exception.__init__(自身,消息)#交给 Exception
        自身.name='ScheduleLogError'#错误名

class 日程输入错误(Exception):#输入错误
    '模型提供的日程规则无法成为记录时的错误'
    def __init__(自身,码,消息,原因=None):#构造输入错误
        '构造一条稳定输入失败'
        Exception.__init__(自身,消息)#交给 Exception
        自身.name='ScheduleInputError'#错误名
        自身.code=码#钉死公开码
        自身.__cause__=原因#可选 cause

class 日程持久错误(Exception):#日程持久失败
    '未能证明当前在线前缀到达了持久监听器'
    def __init__(自身,原因=None):#构造持久失败
        '构造一条被包含的持久失败'
        Exception.__init__(自身,'Schedule persistence did not complete.')#固定文案
        自身.name='SchedulePersistenceError'#错误名
        自身.__cause__=原因#可选包裹原因
