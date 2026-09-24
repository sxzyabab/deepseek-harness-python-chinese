__all__=['远程错误']

class 远程错误(Exception):
    """code/message/details。"""
    def __init__(自身,码,消息,详情=None,原因=None):
        """记下码与消息。"""
        super().__init__(消息)
        自身.code=码
        自身.message=消息
        自身.details={} if 详情 is None else 详情
        if 原因 is not None:
            自身.__cause__=原因
