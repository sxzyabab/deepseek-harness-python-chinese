class Win32错误(Exception):#Win32 调用失败
    'Win32 调用失败，携带 API 名与错误码'
    def __init__(自身,接口,win32码,细节=None):#记下失败上下文
        '记下失败 API、Win32 码与可选细节'
        后缀='' if 细节 is None else ': '+细节#细节后缀
        super().__init__(接口+' failed (Win32 '+str(win32码)+')'+后缀)#英文诊断
        自身.name='Win32Error'#错误名
        自身.api=接口#失败 API
        自身.win32Code=win32码#Win32 码
