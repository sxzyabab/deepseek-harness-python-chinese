class 本地文件系统错误(Exception):#本包配置非法
    '本地文件系统配置非法；详情保持英文线协议原文'
    def __init__(自身,消息):#记下英文消息
        '用原样英文消息构造'
        super().__init__(消息)#英文消息

错误文件未找到=2#文件未找到
错误路径未找到=3#路径未找到
错误访问被拒绝=5#访问被拒绝

class Win32系统错误(Exception):#带 Win32 错误码的系统异常
    '带 Win32 细节的系统异常'
    def __init__(自身,系统调用,win32码,路径):#构造带 Win32 细节的系统异常
        '构造带 Win32 细节的系统异常'
        if win32码==错误文件未找到 or win32码==错误路径未找到:#文件或路径未找到
            码='ENOENT'#映射为 ENOENT
        elif win32码==错误访问被拒绝:#访问被拒绝
            码='EACCES'#映射为 EACCES
        else:#其余错误
            码='EIO'#映射为 EIO
        super().__init__(f'{系统调用} {码} (Win32 {win32码}): {路径}')
        自身.code=码#Node 错误码
        自身.errno=win32码#数字错误号
        自身.syscall=系统调用#系统调用名
        自身.path=路径#相关路径
        自身.win32Code=win32码#原始 Win32 码
