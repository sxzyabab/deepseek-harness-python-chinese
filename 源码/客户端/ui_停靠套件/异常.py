class 停靠错误(Exception):
    '本包停靠布局失败'

    def __init__(自身,消息):
        '记下英文消息'
        super().__init__(消息)#消息原样英文
