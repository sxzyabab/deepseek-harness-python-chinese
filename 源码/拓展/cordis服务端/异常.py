class 宿主运行器错误(Exception):
    '动态宿主运行器包的异常基类'

class 动态cordis错误(Exception):
    '动态 Cordis 运行器的异常基类'
    def __init__(自身,消息):
        '用消息构造'
        super().__init__(消息)
        自身.message=消息
