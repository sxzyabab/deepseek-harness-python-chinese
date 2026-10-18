class 定时不变式错误(Exception):
    '定时描述读到了调用方已经证明过界的下标'

    def __init__(自身,消息):
        '记下违反的不变式'
        super().__init__(消息)
        自身.name='CronInvariantError'
