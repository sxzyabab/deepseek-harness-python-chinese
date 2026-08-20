"""失败即关闭的 Win32 错误类型。后端每次 API 失败都用 API 名与精确 Win32 码抛出本类；原 POC 静默忽略每次失败调用，子进程会以未受限方式运行（失败即开放）——本类就是为挡住那种失败模式。"""

class Win32错误(Exception):#失败即关闭的Win32错误
    """失败即关闭的 Win32 错误，携带 API 名与精确 Win32 码。"""
    def __init__(自身,接口名,win32码,细节=None):#构造Win32错误
        """按 API 名、Win32 码与可选细节构造。"""
        消息=接口名+' failed (Win32 '+str(win32码)+')'#消息含API名与码
        if 细节 is not None:#有细节
            消息=消息+': '+细节#接上细节
        super().__init__(消息)#交给Exception
        自身.name='Win32Error'#固定类名
        自身.api=接口名#记下API名
        自身.win32Code=win32码#记下错误码
