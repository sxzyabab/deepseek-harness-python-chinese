class 提问错误(Exception):
    '提问回执被拒绝'
    def __init__(自身,消息,原因=None):
        '记下英文消息与可选结构原因'
        super().__init__(消息)#消息原样英文
        自身.reason=原因#结构原因
