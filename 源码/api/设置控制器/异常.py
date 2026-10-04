'设置控制器远程失败'
__all__=['远程错误']#仅中文公开名

class 远程错误(Exception):
    '远程错误。附加信息做成属性'
    def __init__(自身,码,消息,详情=None,原因=None):
        '记下 code/message/details'
        super().__init__(消息)#消息
        自身.code=码#错误码
        自身.message=消息#消息
        自身.details={} if 详情 is None else 详情#详情
        if 原因 is not None:#原因
            自身.__cause__=原因#链接
