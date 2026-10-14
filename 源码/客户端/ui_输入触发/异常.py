def 页面失败文案(错误):
    '页面上给调用方看的失败句。原文原样保留。'
    if isinstance(错误,BaseException):
        名=type(错误).__name__
        原文=str(错误.args[0]) if len(错误.args)>0 else ''
        if 原文=='':
            return 名 if 名!='' else '失败'
        return 名+'：'+原文
    return str(错误)

class 触发错误(Exception):
    '本包触发管线失败'
    def __init__(自身,消息):
        '记下英文消息'
        super().__init__(消息)#消息原样英文
