class bash工具错误(Exception):#本包校验与组合失败
    'bash工具入参或组合非法'
    def __init__(自身,消息):#记下英文消息
        '用原样英文消息构造'
        super().__init__(消息)#英文消息

class 后台错误(Exception):
    '后台任务适配失败'
    def __init__(自身,消息):
        '用原样英文消息构造'
        super().__init__(消息)
