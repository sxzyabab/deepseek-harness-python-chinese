class 远程模拟错误(Exception):
    '远程模拟包的异常基类'

    def __init__(自身,消息,种类=None):
        '记下消息与可选种类'
        super().__init__(消息)#错误消息
        自身.种类=种类#按结构识别，无则None
