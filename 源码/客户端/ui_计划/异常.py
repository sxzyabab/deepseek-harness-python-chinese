class 计划错误(Exception):
    '退出计划模式失败'
    def __init__(自身,消息):
        '记下英文消息'
        super().__init__(消息)#消息原样英文
