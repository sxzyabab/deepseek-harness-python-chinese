'失败即关闭的 Win32 错误类型'

class Win32错误(Exception):
    '失败即关闭的 Win32 错误，携带 API 名与精确 Win32 码'
    def __init__(自身,接口名,win32码,细节=None):
        '按 API 名、Win32 码与可选细节构造'
        消息=接口名+' failed (Win32 '+str(win32码)+')'#消息含API名与码
        if 细节 is not None:#有细节
            消息=消息+': '+细节#接上细节
        super().__init__(消息)#交给Exception
        自身.api=接口名#记下API名
        自身.win32Code=win32码#记下错误码

class 访问控制错误(Exception):
    'Windows ACL 沙箱的校验与编排错误'

class 运行器失败(Exception):#已打印过签名的失败
    '已向 stderr 打印签名行的运行器失败'
    pass#无额外字段
