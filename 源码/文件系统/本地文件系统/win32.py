"""原子本地文件替换所用的 Windows 安全描述符辅助。ctypes 惰性加载，因此非 Windows 进程从不打开 Win32 库。"""
import os#路径与平台判定
import ctypes#加载 Win32 DLL
from ctypes import wintypes#Win32 宽度类型

DACL安全信息=0x00000004#请求 DACL 的安全信息标志
保护DACL安全信息=0x80000000#保护 DACL 不被父目录继承
错误文件未找到=2#文件未找到
错误路径未找到=3#路径未找到
错误访问被拒绝=5#访问被拒绝
绑定=None#惰性缓存的 Win32 绑定

class Win32系统错误(Exception):#带 Win32 错误码的系统异常
    """带 Win32 细节的系统异常，字段对齐 Node ErrnoException。"""
    def __init__(自身,系统调用,win32码,路径):#构造带 Win32 细节的系统异常
        """构造带 Win32 细节的系统异常。"""
        if win32码==错误文件未找到 or win32码==错误路径未找到:#文件或路径未找到
            码='ENOENT'#映射为 ENOENT
        elif win32码==错误访问被拒绝:#访问被拒绝
            码='EACCES'#映射为 EACCES
        else:#其余错误
            码='EIO'#映射为 EIO
        super().__init__(f'{系统调用} {码} (Win32 {win32码}): {路径}')#对齐上游错误文案
        自身.code=码#Node 错误码
        自身.errno=win32码#数字错误号
        自身.syscall=系统调用#系统调用名
        自身.path=路径#相关路径
        自身.win32Code=win32码#原始 Win32 码

def 转命名空间路径(路径):#对齐 Node path.toNamespacedPath
    """对齐 Node path.toNamespacedPath。"""
    if os.name!='nt':#非 Windows 原样返回
        return 路径#非 Windows
    绝对=os.path.abspath(路径)#绝对路径
    if 绝对.startswith('\\\\?\\') or 绝对.startswith('\\\\.\\'):#已有设备前缀
        return 绝对#已带前缀
    if 绝对.startswith('\\\\'):#UNC 路径
        return '\\\\?\\UNC\\'+绝对[2:]#UNC 前缀
    return '\\\\?\\'+绝对#DOS 设备前缀

def 取win32绑定():#加载或返回已缓存的 Win32 绑定
    """加载或返回已缓存的 Win32 绑定。"""
    global 绑定#惰性缓存
    if 绑定 is not None:#已加载则直接返回
        return 绑定#缓存命中
    内核32=ctypes.WinDLL('kernel32',use_last_error=True)#加载 kernel32
    安全32=ctypes.WinDLL('advapi32',use_last_error=True)#加载 advapi32
    取文件安全=安全32.GetFileSecurityW#读取安全描述符
    取文件安全.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.LPVOID,wintypes.DWORD,ctypes.POINTER(wintypes.DWORD)]#参数类型
    取文件安全.restype=wintypes.BOOL#返回是否成功
    设文件安全=安全32.SetFileSecurityW#写入安全描述符
    设文件安全.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.LPVOID]#参数类型
    设文件安全.restype=wintypes.BOOL#返回是否成功
    替换文件W=内核32.ReplaceFileW#保留 ACL 替换
    替换文件W.argtypes=[wintypes.LPCWSTR,wintypes.LPCWSTR,wintypes.LPCWSTR,wintypes.DWORD,wintypes.LPVOID,wintypes.LPVOID]#参数类型
    替换文件W.restype=wintypes.BOOL#返回是否成功
    def 调用取文件安全(路径,请求信息,描述符,长度,所需):#GetFileSecurityW 包装
        """读取文件安全描述符，并把所需长度写回可变列表。"""
        需要=wintypes.DWORD(所需[0])#所需缓冲区大小
        指针=None#描述符指针
        缓冲=None#可变缓冲
        if 描述符 is not None:#真正读取时分配缓冲
            缓冲=ctypes.create_string_buffer(bytes(描述符),长度)#按当前内容建缓冲
            指针=缓冲#传给 Win32
        成功=取文件安全(路径,请求信息,指针,长度,ctypes.byref(需要))#调用 GetFileSecurityW
        所需[0]=需要.value#写回所需长度
        if 缓冲 is not None and isinstance(描述符,bytearray):#把读到的字节写回调用方
            取出=缓冲.raw[:长度]#取出原始字节
            描述符[:len(取出)]=取出#写回 bytearray
        return 1 if 成功 else 0#对齐上游成功/失败整数
    def 调用设文件安全(路径,安全信息,描述符):#SetFileSecurityW 包装
        """写入文件安全描述符。"""
        缓冲=ctypes.create_string_buffer(bytes(描述符),len(描述符))#描述符缓冲
        成功=设文件安全(路径,安全信息,缓冲)#调用 SetFileSecurityW
        return 1 if 成功 else 0#对齐上游成功/失败整数
    def 调用替换文件(被替换,替换,备份,标志,排除,保留):#ReplaceFileW 包装
        """调用 ReplaceFileW。"""
        成功=替换文件W(被替换,替换,备份,标志,排除,保留)#保留 ACL 替换
        return 1 if 成功 else 0#对齐上游成功/失败整数
    def 取最后错误():#GetLastError 包装
        """读取 ctypes 保存的 LastError。"""
        return ctypes.get_last_error()#最近 Win32 错误码
    绑定={#缓存绑定表
        'getFileSecurityW':调用取文件安全,#读取 DACL
        'setFileSecurityW':调用设文件安全,#写入 DACL
        'replaceFileW':调用替换文件,#安全替换文件
        'getLastError':取最后错误,#读取 LastError
    }#绑定表结束
    return 绑定#返回新加载的绑定

def 读文件Dacl(路径):#读取文件自相对 DACL
    """读取文件的自相对 DACL 安全描述符。"""
    接口=取win32绑定()#拿到 Win32 绑定
    本地路径=转命名空间路径(路径)#转成 Windows 命名空间路径
    所需=[0]#输出所需缓冲区大小
    接口['getFileSecurityW'](本地路径,DACL安全信息,None,0,所需)#先探测所需长度
    if 所需[0]==0:#长度为 0 则失败
        raise Win32系统错误('GetFileSecurityW',接口['getLastError'](),路径)#抛 Win32 错误
    描述符=bytearray(所需[0])#按所需长度分配描述符缓冲
    if 接口['getFileSecurityW'](本地路径,DACL安全信息,描述符,len(描述符),所需)==0:#真正读取 DACL
        raise Win32系统错误('GetFileSecurityW',接口['getLastError'](),路径)#失败则抛 Win32 错误
    return bytes(描述符[:所需[0]])#返回实际长度的描述符

def 复制文件Dacl(源路径,目标路径):#复制并保护 DACL
    """把已有文件的 DACL 复制到另一文件，并保护它不受暂存父目录继承。"""
    描述符=读文件Dacl(源路径)#读取源文件 DACL
    接口=取win32绑定()#拿到 Win32 绑定
    信息=(DACL安全信息|保护DACL安全信息)&0xFFFFFFFF#DACL 加保护标志
    if 接口['setFileSecurityW'](转命名空间路径(目标路径),信息,描述符)==0:#写入目标 DACL
        raise Win32系统错误('SetFileSecurityW',接口['getLastError'](),目标路径)#失败则抛 Win32 错误

def 替换文件(被替换,替换):#保留 ACL 替换文件
    """替换 Windows 文件，同时保留被替换文件的 ACL 及其他替换元数据。"""
    接口=取win32绑定()#拿到 Win32 绑定
    if 接口['replaceFileW'](转命名空间路径(被替换),转命名空间路径(替换),None,0,None,None)==0:#调用 ReplaceFileW
        raise Win32系统错误('ReplaceFileW',接口['getLastError'](),被替换)#失败则抛 Win32 错误
