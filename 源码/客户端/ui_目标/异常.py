class 目标错误(Exception):
    '目标界面抛出的失败'

    def __init__(自身,消息):
        '记下上游英文消息'
        super().__init__(消息)#消息原样


def 抛出会话不可用(会话标识):
    '绑定已经不在，不能读或改这一会话的目标'
    raise 目标错误('ui-goal: session "'+str(会话标识)+'" is unavailable')#两处共用
