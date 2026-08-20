"""Win32 ACL 沙盒后端的惰性 ctypes 绑定。非 Windows 进程永远不会打开 Win32 库。结构布局在加载时对照 abi 常量断言。"""
import ctypes#Win32 FFI
from ctypes import wintypes#Windows类型
from .错误 import Win32错误#带API名与错误码的失败
from . import win32_abi as abi#头文件探针钉死的尺寸与常量

class 启动信息输入:#stdio相关字段
    """写入已清零 STARTUPINFOW 的字段子集。"""
    def __init__(自身,cb,dwFlags,hStdInput,hStdOutput,hStdError):#记下字段
        """记下结构尺寸、旗标与标准句柄。"""
        自身.cb=cb#结构尺寸
        自身.dwFlags=dwFlags#STARTF_*标志
        自身.hStdInput=hStdInput#标准输入
        自身.hStdOutput=hStdOutput#标准输出
        自身.hStdError=hStdError#标准错误

class 进程信息输出:#CreateProcessAsUserW交出的句柄与id
    """解码后的 PROCESS_INFORMATION。"""
    def __init__(自身,hProcess,hThread,dwProcessId,dwThreadId):#记下字段
        """记下句柄与 id。"""
        自身.hProcess=hProcess#进程句柄
        自身.hThread=hThread#主线程句柄
        自身.dwProcessId=dwProcessId#进程id
        自身.dwThreadId=dwThreadId#线程id

class STARTUPINFOW(ctypes.Structure):#与winbase.h对齐
    """STARTUPINFOW 布局；尺寸对照 abi.启动信息W大小 断言。"""
    _fields_=(
        ('cb',wintypes.DWORD),#结构尺寸
        ('lpReserved',wintypes.LPWSTR),#保留
        ('lpDesktop',wintypes.LPWSTR),#桌面
        ('lpTitle',wintypes.LPWSTR),#标题
        ('dwX',wintypes.DWORD),#窗口X
        ('dwY',wintypes.DWORD),#窗口Y
        ('dwXSize',wintypes.DWORD),#窗口宽
        ('dwYSize',wintypes.DWORD),#窗口高
        ('dwXCountChars',wintypes.DWORD),#缓冲列
        ('dwYCountChars',wintypes.DWORD),#缓冲行
        ('dwFillAttribute',wintypes.DWORD),#填充属性
        ('dwFlags',wintypes.DWORD),#STARTF_*
        ('wShowWindow',wintypes.WORD),#ShowWindow
        ('cbReserved2',wintypes.WORD),#保留2长度
        ('lpReserved2',ctypes.POINTER(ctypes.c_ubyte)),#保留2
        ('hStdInput',wintypes.HANDLE),#stdin
        ('hStdOutput',wintypes.HANDLE),#stdout
        ('hStdError',wintypes.HANDLE),#stderr
    )#字段结束

class PROCESS_INFORMATION(ctypes.Structure):#与processthreadsapi.h对齐
    """PROCESS_INFORMATION 布局；尺寸对照 abi.进程信息大小 断言。"""
    _fields_=(
        ('hProcess',wintypes.HANDLE),#进程句柄
        ('hThread',wintypes.HANDLE),#主线程句柄
        ('dwProcessId',wintypes.DWORD),#进程id
        ('dwThreadId',wintypes.DWORD),#线程id
    )#字段结束

if ctypes.sizeof(STARTUPINFOW)!=abi.启动信息W大小:#ctypes算出的尺寸必须贴合头文件探针
    raise Exception('STARTUPINFOW layout mismatch: ctypes computed '+str(ctypes.sizeof(STARTUPINFOW))+', header probe says '+str(abi.启动信息W大小))#加载失败
if ctypes.sizeof(PROCESS_INFORMATION)!=abi.进程信息大小:#同上
    raise Exception('PROCESS_INFORMATION layout mismatch: ctypes computed '+str(ctypes.sizeof(PROCESS_INFORMATION))+', header probe says '+str(abi.进程信息大小))#加载失败

def 是否空指针(值):#NULL判断
    """对 NULL 指针为真（None 或 0）。"""
    return 值 is None or 值==0#两种空形态

def 是否无效句柄(句柄):#无效句柄
    """对 CreateFileW 的 INVALID_HANDLE_VALUE 失败标记为真。"""
    if 是否空指针(句柄):#NULL也当失败
        return True#失败
    return 句柄==0xFFFFFFFFFFFFFFFF or 句柄==-1#全1/-1

def 分配指针槽():#void**槽
    """分配一个指针大小的槽（给 `T **` 出参）。"""
    return ctypes.c_void_p()#一个指针槽

def 分配无符号32():#DWORD出参
    """分配一个 uint32 槽。"""
    return ctypes.c_uint32(0)#一个DWORD

def 编码无符号32(槽,值):#写DWORD
    """把一个 uint32 值写入槽指针。"""
    槽.value=值&0xFFFFFFFF#按uint32写入

def 解码指针(槽):#读void*
    """解码指针大小槽里存的指针（NULL 变成 None）。"""
    值=槽.value#取出
    if 是否空指针(值):#NULL
        return None#空
    return 值#非空指针

def 解码无符号32(槽):#读DWORD
    """在槽指针处解码一个 uint32。"""
    return int(槽.value)#JS number等价

def 指针地址(指针):#取地址
    """把指针转成其数值地址（用于原始结构打包）。"""
    if 指针 is None:#空
        return 0#零地址
    return int(指针)#数值地址

def 分配字节(长度):#uint8数组
    """分配一块原始字节（用于 SID 拷贝和变长数组）。"""
    return (ctypes.c_ubyte*长度)()#length字节

def 分配重叠结构():#32字节OVERLAPPED
    """分配一个已清零的 OVERLAPPED（x64 上 32 字节）。"""
    return 分配字节(32)#x64布局

def 解码缓冲内指针(缓冲,偏移):#缓冲内指针
    """解码 `缓冲[偏移]` 处内存里存的指针值。"""
    视图=memoryview(缓冲)[偏移:偏移+8]#八字节
    地址=int.from_bytes(视图,'little')#小端地址
    if 是否空指针(地址):#NULL
        return None#空
    return 地址#非空

def 解码偏移无符号8(指针,偏移):#读一字节
    """在原生指针加字节偏移处解码一个 uint8。"""
    return ctypes.c_ubyte.from_address(int(指针)+偏移).value#0-255

def 解码偏移无符号16(指针,偏移):#读WORD
    """在原生指针加字节偏移处解码一个 uint16。"""
    return ctypes.c_uint16.from_address(int(指针)+偏移).value#0-65535

def 解码偏移无符号32(指针,偏移):#读DWORD
    """在原生指针加字节偏移处解码一个 uint32。"""
    return ctypes.c_uint32.from_address(int(指针)+偏移).value#数值

def 同SID于(左,左偏移,右,右偏移):#有界SID相等
    """经有界偏移读取逐字段比较两个 SID。"""
    左修订=解码偏移无符号8(左,左偏移)#修订
    右修订=解码偏移无符号8(右,右偏移)#修订
    if 左修订!=右修订:#修订不同
        return False#不等
    左个数=解码偏移无符号8(左,左偏移+1)#子权威个数
    右个数=解码偏移无符号8(右,右偏移+1)#子权威个数
    if 左个数!=右个数 or 左个数>abi.最大子权威:#个数不同或不可信
        return False#不等
    for 下标 in range(6):#6字节IdentifierAuthority
        if 解码偏移无符号8(左,左偏移+2+下标)!=解码偏移无符号8(右,右偏移+2+下标):#权威字节不同
            return False#不等
    for 下标 in range(左个数):#每个DWORD子权威
        if 解码偏移无符号32(左,左偏移+8+下标*4)!=解码偏移无符号32(右,右偏移+8+下标*4):#子权威不同
            return False#不等
    return True#字段全同

def 分配启动信息():#STARTUPINFOW
    """分配一个已清零的 STARTUPINFOW。"""
    return STARTUPINFOW()#一个结构

def 编码启动信息(启动信息,字段):#写stdio字段
    """把与 stdio 相关的字段写入已清零的 STARTUPINFOW。"""
    启动信息.cb=字段.cb#结构尺寸
    启动信息.dwFlags=字段.dwFlags#旗标
    启动信息.hStdInput=字段.hStdInput#stdin
    启动信息.hStdOutput=字段.hStdOutput#stdout
    启动信息.hStdError=字段.hStdError#stderr

def 分配进程信息():#PROCESS_INFORMATION
    """分配一个已清零的 PROCESS_INFORMATION。"""
    return PROCESS_INFORMATION()#一个结构

def 解码进程信息(进程信息):#读出参
    """在 CreateProcessAsUserW 之后解码 PROCESS_INFORMATION。"""
    进程=进程信息.hProcess#进程句柄
    线程=进程信息.hThread#线程句柄
    if 是否空指针(进程):#空进程
        进程=None#空
    if 是否空指针(线程):#空线程
        线程=None#空
    return 进程信息输出(进程,线程,进程信息.dwProcessId,进程信息.dwThreadId)#句柄与id

class Win32绑定表:#按用途分组的stdcall
    """惰性 ctypes 绑定表：ACL 后端用到的每一个 Win32 调用。"""
    def __init__(自身):#首次绑定DLL
        """加载 kernel32/advapi32 并绑定全部调用。"""
        核=ctypes.WinDLL('kernel32',use_last_error=True)#kernel32
        安=ctypes.WinDLL('advapi32',use_last_error=True)#advapi32
        自身._核=核#记下
        自身._安=安#记下
        核.OpenProcess.restype=wintypes.HANDLE#按pid打开进程
        核.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]#参数
        安.OpenProcessToken.restype=wintypes.BOOL#打开进程令牌
        安.OpenProcessToken.argtypes=[wintypes.HANDLE,wintypes.DWORD,ctypes.POINTER(wintypes.HANDLE)]#参数
        核.CloseHandle.restype=wintypes.BOOL#关句柄
        核.CloseHandle.argtypes=[wintypes.HANDLE]#参数
        核.GetLastError.restype=wintypes.DWORD#上一错误码
        核.GetLastError.argtypes=[]#无参
        核.FormatMessageW.restype=wintypes.DWORD#格式化系统消息
        核.FormatMessageW.argtypes=[wintypes.DWORD,wintypes.LPCVOID,wintypes.DWORD,wintypes.DWORD,wintypes.LPWSTR,wintypes.DWORD,wintypes.LPVOID]#参数
        核.LocalAlloc.restype=ctypes.c_void_p#本地堆分配
        核.LocalAlloc.argtypes=[wintypes.UINT,ctypes.c_size_t]#参数
        核.LocalFree.restype=ctypes.c_void_p#本地堆释放
        核.LocalFree.argtypes=[ctypes.c_void_p]#参数
        安.ConvertStringSidToSidW.restype=wintypes.BOOL#SDDL→SID
        安.ConvertStringSidToSidW.argtypes=[wintypes.LPCWSTR,ctypes.POINTER(ctypes.c_void_p)]#参数
        安.CreateWellKnownSid.restype=wintypes.BOOL#知名SID
        安.CreateWellKnownSid.argtypes=[ctypes.c_int,ctypes.c_void_p,ctypes.c_void_p,ctypes.POINTER(wintypes.DWORD)]#参数
        安.IsValidSid.restype=wintypes.BOOL#SID是否合法
        安.IsValidSid.argtypes=[ctypes.c_void_p]#参数
        安.GetLengthSid.restype=wintypes.DWORD#SID字节长度
        安.GetLengthSid.argtypes=[ctypes.c_void_p]#参数
        安.CopySid.restype=wintypes.BOOL#拷SID
        安.CopySid.argtypes=[wintypes.DWORD,ctypes.c_void_p,ctypes.c_void_p]#参数
        安.GetTokenInformation.restype=wintypes.BOOL#读令牌信息
        安.GetTokenInformation.argtypes=[wintypes.HANDLE,ctypes.c_int,ctypes.c_void_p,wintypes.DWORD,ctypes.POINTER(wintypes.DWORD)]#参数
        安.SetTokenInformation.restype=wintypes.BOOL#写令牌信息
        安.SetTokenInformation.argtypes=[wintypes.HANDLE,ctypes.c_int,ctypes.c_void_p,wintypes.DWORD]#参数
        安.CreateRestrictedToken.restype=wintypes.BOOL#造受限令牌
        安.CreateRestrictedToken.argtypes=[wintypes.HANDLE,wintypes.DWORD,wintypes.DWORD,ctypes.c_void_p,wintypes.DWORD,ctypes.c_void_p,wintypes.DWORD,ctypes.c_void_p,ctypes.POINTER(wintypes.HANDLE)]#参数
        安.SetEntriesInAclW.restype=wintypes.DWORD#往ACL加ACE
        安.SetEntriesInAclW.argtypes=[wintypes.ULONG,ctypes.c_void_p,ctypes.c_void_p,ctypes.POINTER(ctypes.c_void_p)]#参数
        安.SetNamedSecurityInfoW.restype=wintypes.DWORD#写命名对象安全描述符
        安.SetNamedSecurityInfoW.argtypes=[wintypes.LPWSTR,ctypes.c_int,wintypes.DWORD,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p]#参数
        安.GetNamedSecurityInfoW.restype=wintypes.DWORD#读命名对象安全描述符
        安.GetNamedSecurityInfoW.argtypes=[wintypes.LPWSTR,ctypes.c_int,wintypes.DWORD,ctypes.POINTER(ctypes.c_void_p),ctypes.POINTER(ctypes.c_void_p),ctypes.POINTER(ctypes.c_void_p),ctypes.POINTER(ctypes.c_void_p),ctypes.POINTER(ctypes.c_void_p)]#参数
        核.GetTempPathW.restype=wintypes.DWORD#临时目录
        核.GetTempPathW.argtypes=[wintypes.DWORD,wintypes.LPWSTR]#参数
        核.CreateFileW.restype=wintypes.HANDLE#打开/创建文件
        核.CreateFileW.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,ctypes.c_void_p,wintypes.DWORD,wintypes.DWORD,wintypes.HANDLE]#参数
        核.LockFileEx.restype=wintypes.BOOL#字节范围锁
        核.LockFileEx.argtypes=[wintypes.HANDLE,wintypes.DWORD,wintypes.DWORD,wintypes.DWORD,wintypes.DWORD,ctypes.c_void_p]#参数
        核.UnlockFileEx.restype=wintypes.BOOL#解锁
        核.UnlockFileEx.argtypes=[wintypes.HANDLE,wintypes.DWORD,wintypes.DWORD,wintypes.DWORD,ctypes.c_void_p]#参数
        核.CreatePipe.restype=wintypes.BOOL#匿名管道
        核.CreatePipe.argtypes=[ctypes.POINTER(wintypes.HANDLE),ctypes.POINTER(wintypes.HANDLE),ctypes.c_void_p,wintypes.DWORD]#参数
        核.SetHandleInformation.restype=wintypes.BOOL#句柄继承标志
        核.SetHandleInformation.argtypes=[wintypes.HANDLE,wintypes.DWORD,wintypes.DWORD]#参数
        安.CreateProcessAsUserW.restype=wintypes.BOOL#以用户令牌创建进程
        安.CreateProcessAsUserW.argtypes=[wintypes.HANDLE,wintypes.LPCWSTR,wintypes.LPWSTR,ctypes.c_void_p,ctypes.c_void_p,wintypes.BOOL,wintypes.DWORD,ctypes.c_void_p,wintypes.LPCWSTR,ctypes.POINTER(STARTUPINFOW),ctypes.POINTER(PROCESS_INFORMATION)]#参数
        核.SetEnvironmentVariableW.restype=wintypes.BOOL#设环境变量
        核.SetEnvironmentVariableW.argtypes=[wintypes.LPCWSTR,wintypes.LPCWSTR]#参数
        核.ReadFile.restype=wintypes.BOOL#读文件/管道
        核.ReadFile.argtypes=[wintypes.HANDLE,ctypes.c_void_p,wintypes.DWORD,ctypes.POINTER(wintypes.DWORD),ctypes.c_void_p]#参数
        核.PeekNamedPipe.restype=wintypes.BOOL#窥管道积压
        核.PeekNamedPipe.argtypes=[wintypes.HANDLE,ctypes.c_void_p,wintypes.DWORD,ctypes.POINTER(wintypes.DWORD),ctypes.POINTER(wintypes.DWORD),ctypes.POINTER(wintypes.DWORD)]#参数
        核.WaitForSingleObject.restype=wintypes.DWORD#等句柄
        核.WaitForSingleObject.argtypes=[wintypes.HANDLE,wintypes.DWORD]#参数
        核.GetExitCodeProcess.restype=wintypes.BOOL#读退出码
        核.GetExitCodeProcess.argtypes=[wintypes.HANDLE,ctypes.POINTER(wintypes.DWORD)]#参数
        核.ResumeThread.restype=wintypes.DWORD#恢复挂起线程
        核.ResumeThread.argtypes=[wintypes.HANDLE]#参数
        核.CreateJobObjectW.restype=wintypes.HANDLE#作业对象
        核.CreateJobObjectW.argtypes=[ctypes.c_void_p,wintypes.LPCWSTR]#参数
        核.SetInformationJobObject.restype=wintypes.BOOL#设作业限制
        核.SetInformationJobObject.argtypes=[wintypes.HANDLE,ctypes.c_int,ctypes.c_void_p,wintypes.DWORD]#参数
        核.AssignProcessToJobObject.restype=wintypes.BOOL#进程进作业
        核.AssignProcessToJobObject.argtypes=[wintypes.HANDLE,wintypes.HANDLE]#参数
        核.TerminateProcess.restype=wintypes.BOOL#杀进程
        核.TerminateProcess.argtypes=[wintypes.HANDLE,wintypes.UINT]#参数
        核.SetConsoleCtrlHandler.restype=wintypes.BOOL#Ctrl+C处理
        核.SetConsoleCtrlHandler.argtypes=[ctypes.c_void_p,wintypes.BOOL]#参数
        核.GetStdHandle.restype=wintypes.HANDLE#标准句柄
        核.GetStdHandle.argtypes=[wintypes.DWORD]#参数

    def openProcess(自身,desiredAccess,inheritHandle,pid):#OpenProcess
        """按 pid 打开进程。"""
        return 自身._核.OpenProcess(desiredAccess,inheritHandle,pid)#打开

    def openProcessToken(自身,process,desiredAccess,tokenHandle):#OpenProcessToken
        """打开进程令牌。"""
        return 自身._安.OpenProcessToken(process,desiredAccess,ctypes.byref(tokenHandle))#打开

    def closeHandle(自身,handle):#CloseHandle
        """关句柄。"""
        return 自身._核.CloseHandle(handle)#关闭

    def getLastError(自身):#GetLastError
        """上一错误码。"""
        return ctypes.get_last_error()#立刻读

    def formatMessageW(自身,flags,source,messageId,languageId,buffer,size,args):#FormatMessageW
        """格式化系统消息。"""
        return 自身._核.FormatMessageW(flags,source,messageId,languageId,buffer,size,args)#格式化

    def localAlloc(自身,flags,bytes_):#LocalAlloc
        """本地堆分配。"""
        return 自身._核.LocalAlloc(flags,bytes_)#分配

    def localFree(自身,memory):#LocalFree
        """本地堆释放。"""
        return 自身._核.LocalFree(memory)#释放

    def convertStringSidToSidW(自身,stringSid,sid):#ConvertStringSidToSidW
        """SDDL → SID。"""
        return 自身._安.ConvertStringSidToSidW(stringSid,ctypes.byref(sid))#转换

    def createWellKnownSid(自身,type_,domainSid,sid,size):#CreateWellKnownSid
        """知名 SID。"""
        return 自身._安.CreateWellKnownSid(type_,domainSid,sid,ctypes.byref(size))#创建

    def isValidSid(自身,sid):#IsValidSid
        """SID 是否合法。"""
        return 自身._安.IsValidSid(sid)#校验

    def getLengthSid(自身,sid):#GetLengthSid
        """SID 字节长度。"""
        return 自身._安.GetLengthSid(sid)#长度

    def copySid(自身,length,destination,source):#CopySid
        """拷 SID。"""
        return 自身._安.CopySid(length,destination,source)#拷贝

    def getTokenInformation(自身,token,cls,info,length,needed):#GetTokenInformation
        """读令牌信息。"""
        缓冲=None if info is None else ctypes.cast(info,ctypes.c_void_p)#空或指针
        return 自身._安.GetTokenInformation(token,cls,缓冲,length,ctypes.byref(needed))#读取

    def setTokenInformation(自身,token,cls,info,length):#SetTokenInformation
        """写令牌信息。"""
        return 自身._安.SetTokenInformation(token,cls,ctypes.cast(info,ctypes.c_void_p),length)#写入

    def createRestrictedToken(自身,existing,flags,disableCount,disableSids,deletePrivilegeCount,privilegesToDelete,restrictCount,restrictingSids,newToken):#CreateRestrictedToken
        """造受限令牌。"""
        return 自身._安.CreateRestrictedToken(existing,flags,disableCount,disableSids,deletePrivilegeCount,privilegesToDelete,restrictCount,restrictingSids,ctypes.byref(newToken))#创建

    def setEntriesInAclW(自身,count,entries,oldAcl,newAcl):#SetEntriesInAclW
        """往 ACL 加 ACE。"""
        if entries is None:#无条目缓冲
            条目指针=None#空
        elif isinstance(entries,(bytearray,bytes)):#字节缓冲
            视图=(ctypes.c_ubyte*len(entries)).from_buffer(entries if isinstance(entries,bytearray) else bytearray(entries))#可写视图
            条目指针=ctypes.cast(视图,ctypes.c_void_p)#指针
        else:#已是ctypes缓冲
            条目指针=ctypes.cast(entries,ctypes.c_void_p)#指针
        return 自身._安.SetEntriesInAclW(count,条目指针,oldAcl,ctypes.byref(newAcl))#合并

    def setNamedSecurityInfoW(自身,path,objectType,information,owner,group,dacl,sacl):#SetNamedSecurityInfoW
        """写命名对象安全描述符。"""
        return 自身._安.SetNamedSecurityInfoW(path,objectType,information,owner,group,dacl,sacl)#写入

    def getNamedSecurityInfoW(自身,path,objectType,information,owner,group,dacl,sacl,descriptor):#GetNamedSecurityInfoW
        """读命名对象安全描述符。"""
        return 自身._安.GetNamedSecurityInfoW(path,objectType,information,ctypes.byref(owner),ctypes.byref(group),ctypes.byref(dacl),ctypes.byref(sacl),ctypes.byref(descriptor))#读取

    def getTempPathW(自身,length,buffer):#GetTempPathW
        """临时目录。"""
        return 自身._核.GetTempPathW(length,buffer)#读取

    def createFileW(自身,fileName,desiredAccess,shareMode,attributes,creationDisposition,flagsAndAttributes,templateFile):#CreateFileW
        """打开/创建文件。"""
        return 自身._核.CreateFileW(fileName,desiredAccess,shareMode,attributes,creationDisposition,flagsAndAttributes,templateFile)#打开

    def lockFileEx(自身,file,flags,reserved,bytesLow,bytesHigh,overlapped):#LockFileEx
        """字节范围锁。"""
        return 自身._核.LockFileEx(file,flags,reserved,bytesLow,bytesHigh,overlapped)#加锁

    def unlockFileEx(自身,file,reserved,bytesLow,bytesHigh,overlapped):#UnlockFileEx
        """解锁。"""
        return 自身._核.UnlockFileEx(file,reserved,bytesLow,bytesHigh,overlapped)#解锁

    def createPipe(自身,readHandle,writeHandle,attributes,size):#CreatePipe
        """匿名管道。"""
        return 自身._核.CreatePipe(ctypes.byref(readHandle),ctypes.byref(writeHandle),attributes,size)#创建

    def setHandleInformation(自身,handle,mask,flags):#SetHandleInformation
        """句柄继承标志。"""
        return 自身._核.SetHandleInformation(handle,mask,flags)#设置

    def createProcessAsUserW(自身,token,applicationName,commandLine,processAttributes,threadAttributes,inheritHandles,creationFlags,environment,currentDirectory,startupInfo,processInfo):#CreateProcessAsUserW
        """以用户令牌创建进程。"""
        命令=ctypes.create_unicode_buffer(commandLine)#可变命令行缓冲
        return 自身._安.CreateProcessAsUserW(token,applicationName,命令,processAttributes,threadAttributes,inheritHandles,creationFlags,environment,currentDirectory,ctypes.byref(startupInfo),ctypes.byref(processInfo))#创建

    def setEnvironmentVariableW(自身,name,value):#SetEnvironmentVariableW
        """设环境变量。"""
        return 自身._核.SetEnvironmentVariableW(name,value)#设置

    def readFile(自身,file,buffer,count,bytesRead,overlapped):#ReadFile
        """读文件/管道。"""
        return 自身._核.ReadFile(file,ctypes.cast(buffer,ctypes.c_void_p),count,ctypes.byref(bytesRead),overlapped)#读取

    def peekNamedPipe(自身,pipe,buffer,size,bytesRead,totalAvail,leftThisMessage):#PeekNamedPipe
        """窥管道积压。"""
        return 自身._核.PeekNamedPipe(pipe,buffer,size,ctypes.byref(bytesRead),ctypes.byref(totalAvail),ctypes.byref(leftThisMessage))#窥探

    def waitForSingleObject(自身,handle,milliseconds):#WaitForSingleObject
        """等句柄。"""
        return 自身._核.WaitForSingleObject(handle,milliseconds)#等待

    def getExitCodeProcess(自身,process,exitCode):#GetExitCodeProcess
        """读退出码。"""
        return 自身._核.GetExitCodeProcess(process,ctypes.byref(exitCode))#取码

    def resumeThread(自身,thread):#ResumeThread
        """恢复挂起线程。"""
        return 自身._核.ResumeThread(thread)#恢复

    def createJobObjectW(自身,attributes,name):#CreateJobObjectW
        """作业对象。"""
        return 自身._核.CreateJobObjectW(attributes,name)#创建

    def setInformationJobObject(自身,job,cls,information,length):#SetInformationJobObject
        """设作业限制。"""
        return 自身._核.SetInformationJobObject(job,cls,ctypes.cast(information,ctypes.c_void_p),length)#设置

    def assignProcessToJobObject(自身,job,process):#AssignProcessToJobObject
        """进程进作业。"""
        return 自身._核.AssignProcessToJobObject(job,process)#指派

    def terminateProcess(自身,process,exitCode):#TerminateProcess
        """杀进程。"""
        return 自身._核.TerminateProcess(process,exitCode)#终止

    def setConsoleCtrlHandler(自身,handler,add):#SetConsoleCtrlHandler
        """Ctrl+C 处理。"""
        return 自身._核.SetConsoleCtrlHandler(handler,add)#设置

    def getStdHandle(自身,stdHandle):#GetStdHandle
        """标准句柄。"""
        return 自身._核.GetStdHandle(stdHandle&0xFFFFFFFF)#读取

_缓存=None#惰性绑定表

def 绑定表():#首次调用才load DLL
    """解析惰性 Win32 绑定。"""
    global _缓存#可变缓存
    if _缓存 is not None:#已加载
        return _缓存#已有
    _缓存=Win32绑定表()#一次填完整张表
    return _缓存#同一张表

def 解析绑定():#异步外观兼容；底层同步
    """解析惰性 Win32 绑定（同步兑现）。"""
    return 绑定表()#底层load是同步的

def 同步解析绑定():#同步路径
    """同步解析惰性 Win32 绑定。"""
    return 绑定表()#与解析绑定同一张表

def 错误文本(接口,win32码):#系统消息
    """经 FormatMessageW 把 Win32 错误码变成可读文本。"""
    缓冲=ctypes.create_unicode_buffer(512)#宽字符缓冲
    长度=接口.formatMessageW(abi.格式化系统消息|abi.格式化忽略插入,None,win32码,0,缓冲,512,None)#写入buffer
    if 长度==0:#格式化失败
        return ''#空
    return 缓冲.value.strip()#去掉尾空白

def 取临时路径(接口):#MAX_PATH临时目录
    """经 GetTempPathW 读进程临时目录。"""
    容量=abi.最大路径+1#字符容量
    缓冲=ctypes.create_unicode_buffer(容量)#宽字符+NUL
    长度=接口.getTempPathW(容量,缓冲)#字符数
    if 长度==0:#失败
        抛上次错误(接口,'GetTempPathW')#抛出
    if 长度>容量:#所需长度超出缓冲
        raise Win32错误('GetTempPathW',abi.错误缓冲不足,'required '+str(长度)+' chars exceed the '+str(容量)+'-char buffer; nothing was written')#不得解码空缓冲
    return 缓冲.value#路径

def 抛上次错误(接口,名称,细节=None):#BOOL失败
    """为 BOOL 风格 API 失败抛出 Win32Error。"""
    win32码=接口.getLastError()#必须立刻读
    raise Win32错误(名称,win32码,细节 if 细节 is not None else 错误文本(接口,win32码))#带系统文本

def 抛Win32(接口,名称,win32码,细节=None):#ERROR_*返回值
    """为 HRESULT 风格 API 返回值抛出 Win32Error。"""
    raise Win32错误(名称,win32码,细节 if 细节 is not None else 错误文本(接口,win32码))#码已在手
