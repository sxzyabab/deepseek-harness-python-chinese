__all__=[#仅中文公开名
    '远程错误','取远程错误','网页终端标识','终端附着标识','视图问题表',
]#公开面结束

视图问题表=('missingTerminal','inputFull','attachmentEnded','invalidOutput','terminalLimit')#产品错误键

class 远程错误(Exception):#对齐上游 RemoteError
    """code/message/details。"""
    def __init__(自身,码,消息,详情=None,原因=None):#记下
        """记下码与英文消息。"""
        super().__init__(消息)#消息
        自身.code=码#码
        自身.message=消息#消息
        自身.details={} if 详情 is None else 详情#详情
        if 原因 is not None:#原因
            自身.__cause__=原因#链

def 取远程错误(错误):#从抛出值恢复 RemoteError
    """只承认本包远程错误。"""
    if isinstance(错误,远程错误):#本类
        return 错误#原样
    return None#未匹配

def 网页终端标识(原始):#品牌化
    """承认会话内终端身份。"""
    return 原始#原样

def 终端附着标识(原始):#品牌化
    """承认可写附着身份。"""
    return 原始#原样
