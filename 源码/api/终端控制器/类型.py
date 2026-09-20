__all__=[
    '远程错误','取远程错误','网页终端标识','终端附着标识','视图问题表','终端保持帧',
]

视图问题表=('missingTerminal','inputFull','attachmentEnded','invalidOutput','terminalLimit')#产品错误键
终端保持帧={'type':'retained'}#窗口保持确认帧形态
class 远程错误(Exception):
    """code/message/details。"""
    def __init__(自身,码,消息,详情=None,原因=None):
        """记下码与英文消息。"""
        super().__init__(消息)
        自身.code=码
        自身.message=消息
        自身.details={} if 详情 is None else 详情
        if 原因 is not None:
            自身.__cause__=原因

def 取远程错误(错误):
    """只承认本包远程错误。"""
    if isinstance(错误,远程错误):
        return 错误
    return None

def 网页终端标识(原始):
    """承认会话内终端身份。"""
    return 原始

def 终端附着标识(原始):
    """承认可写附着身份。"""
    return 原始
