__all__=['远程错误']

class 远程错误(Exception):
    """Typert Remote 错误。"""
    def __init__(自身,码,消息,详情=None):
        """记下 code/message/details。"""
        super().__init__(消息)
        自身.code=码
        自身.message=消息
        自身.details={} if 详情 is None else 详情
        自身.name='RemoteError'
