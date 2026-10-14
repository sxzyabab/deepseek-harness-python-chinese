__all__=('录制错误',)#仅中文公开名

def 失败说明(错误):
    '失败句去掉绝对路径，其余原文保留'
    if isinstance(错误,BaseException) and len(错误.args)>0:
        原文=str(错误.args[0])
    else:
        原文=str(错误)
    留下=[]
    for 词 in 原文.split():
        去引=词.strip('\'"()[]{}<>')
        统一=去引.replace('\\','/')
        if 统一.startswith('/') or 统一.startswith('~'):
            continue
        if len(统一)>2 and 统一[0].isalpha() and 统一[1]==':' and 统一[2]=='/':
            continue
        留下.append(词)
    说明=' '.join(留下).strip()
    if 说明!='':
        return 说明
    if isinstance(错误,BaseException):
        return type(错误).__name__
    return '失败'

class 录制错误(Exception):
    '采集失败，文案键由调用方按 kind 翻译'
    def __init__(自身,kind):
        'kind 为 unavailable / permission / empty / cancelled / interrupted / deviceMissing'
        super().__init__(kind)
        自身.kind=kind
        自身.name='RecordingError'
