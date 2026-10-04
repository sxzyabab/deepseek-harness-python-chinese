class 交付物错误(Exception):
    '本包异常基类'

class 呈现打开错误(Exception):
    '呈现打开失败'
    def __init__(自身,消息):
        '记下消息'
        super().__init__(消息)#英文

class 已呈现打开错误(Exception):
    '已呈现打开失败'
    def __init__(自身,消息):
        '记下消息'
        super().__init__(消息)#英文
