from nicegui import ui as 界面

def 页面失败文案(错误):
    '页面上给调用方看的失败句。原文原样保留。'
    if isinstance(错误,BaseException):
        名=type(错误).__name__
        原文=str(错误.args[0]) if len(错误.args)>0 else ''
        if 原文=='':
            return 名 if 名!='' else '失败'
        return 名+'：'+原文
    return str(错误)

def 贴出失败(自身):
    '父级拆掉旧画面时，把失败句留在当前容器里。'
    文=getattr(自身,'画面失败',None)
    if isinstance(文,str) and 文!='':
        界面.label(文)
        自身.画面失败=None

class 聊天错误(Exception):
    'ui-chat 包内的本地失败'
