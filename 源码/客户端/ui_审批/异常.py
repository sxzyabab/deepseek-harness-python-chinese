class 审批错误(Exception):
    '本包审批结算、中止与委托失败'
    def __init__(自身,消息,码=None):
        '记下英文消息与可选结构码'
        super().__init__(消息)#消息原样英文
        自身.code=码#结构识别码
