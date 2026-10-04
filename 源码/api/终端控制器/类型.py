from .异常 import 远程错误#本包异常

__all__=[
    '远程错误','取远程错误','网页终端标识','终端附着标识','视图问题表','终端保持帧',
]

视图问题表=('missingTerminal','inputFull','attachmentEnded','invalidOutput','terminalLimit')#产品错误键
终端保持帧={'type':'retained'}#窗口保持确认帧形态

def 取远程错误(错误):
    '只承认本包远程错误'
    if isinstance(错误,远程错误):
        return 错误
    return None

def 网页终端标识(原始):
    '承认会话内终端身份'
    return 原始

def 终端附着标识(原始):
    '承认可写附着身份'
    return 原始
