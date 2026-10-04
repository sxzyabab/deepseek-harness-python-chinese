'终端控制器远程失败与视图失败'
__all__=['远程错误','终端视图错误']#仅中文公开名

class 远程错误(Exception):
    'code/message/details'
    def __init__(自身,码,消息,详情=None,原因=None):
        '记下码与英文消息'
        super().__init__(消息)
        自身.code=码
        自身.message=消息
        自身.details={} if 详情 is None else 详情
        if 原因 is not None:
            自身.__cause__=原因

class 终端视图错误(远程错误):#本视图失败
    'code=terminal/view，details.issue 为产品键'
    def __init__(自身,问题,消息=None):#记下
        '缺省消息即问题键'
        super().__init__('terminal/view',问题 if 消息 is None else 消息,{'issue':问题})#构造
