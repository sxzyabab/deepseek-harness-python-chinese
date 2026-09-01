"""Windows ACL 沙箱使用的 Win32 进程、标准 IO 与作业对象原语。"""
import ctypes,os,struct,time#FFI、平台、结构打包与退避
__all__=[#仅中文公开名
    '错误缓冲不足','Win32错误','分配指针槽','分配uint32','解码指针','解码uint32',
    '扩展win32进程绑定','是否空指针','抛上次错误','抛win32错误',
    '引用参数','构建命令行','生成继承作业进程','生成管道进程','等待进程退出','排空管道',
]#公开面结束

错误缓冲不足=122#ERROR_INSUFFICIENT_BUFFER
使用标准句柄=0x00000100#STARTF_USESTDHANDLES
句柄可继承=0x1#HANDLE_FLAG_INHERIT
无限等待=0xFFFFFFFF#INFINITE
挂起创建=0x4#CREATE_SUSPENDED
标准输入句柄=-10#STD_INPUT_HANDLE
标准输出句柄=-11#STD_OUTPUT_HANDLE
标准错误句柄=-12#STD_ERROR_HANDLE
格式化系统消息=0x00001000#FORMAT_MESSAGE_FROM_SYSTEM
格式化忽略插入=0x00000200#FORMAT_MESSAGE_IGNORE_INSERTS
管道断开错误=109#ERROR_BROKEN_PIPE
无数据错误=232#ERROR_NO_DATA
关闭即杀作业=0x00002000#JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
作业扩展限制类=9#JobObjectExtendedLimitInformation
作业扩展限制大小=144#JOBOBJECT_EXTENDED_LIMIT_INFORMATION
作业扩展限制旗标偏移=16#JOBOBJECT_EXTENDED_LIMIT_FLAGS_OFFSET
启动信息w大小=104#STARTUPINFOW_SIZE
进程信息大小=24#PROCESS_INFORMATION_SIZE

class Win32错误(Exception):#Win32 调用失败
    """Win32 调用失败，携带 API 名与错误码。"""
    def __init__(自身,接口,win32码,细节=None):#记下失败上下文
        """记下失败 API、Win32 码与可选细节。"""
        后缀='' if 细节 is None else ': '+细节#细节后缀
        super().__init__(接口+' failed (Win32 '+str(win32码)+')'+后缀)#英文诊断
        自身.name='Win32Error'#错误名
        自身.api=接口#失败 API
        自身.win32Code=win32码#Win32 码

def 是否空指针(值):#指针是否为空
    """指针是否为 null、未定义或地址零。"""
    return 值 is None or 值==0#空指针

def _取绑定():#惰性加载 Win32 绑定
    """惰性加载 kernel32/advapi32 绑定表。"""
    if os.name!='nt':#非 Windows
        raise Win32错误('platform',0,'win32-process requires Windows')#平台不支持
    return {'kernel32':ctypes.windll.kernel32,'advapi32':ctypes.windll.advapi32}#共享上下文

_缓存绑定=None#缓存绑定表
_缓存进程表=None#缓存进程 API 表

def _绑定():#获取缓存绑定
    """获取缓存的 Win32 绑定表。"""
    global _缓存绑定#模块缓存
    if _缓存绑定 is None:#尚未加载
        _缓存绑定=_取绑定()#加载
    return _缓存绑定#返回

def 分配指针槽():#分配指针大小 out 参数
    """分配一个指针大小的 out 参数槽。"""
    return ctypes.c_void_p()#指针槽

def 分配uint32():#分配 uint32 out 参数
    """分配一个 uint32 out 参数槽。"""
    return ctypes.c_uint32()#uint32 槽

def 解码指针(槽):#解码指针 out 参数
    """解码指针 out 参数；地址零视为 null。"""
    值=槽.value#读值
    return None if 是否空指针(值) else 值#空则 null

def 解码uint32(槽):#解码 uint32 out 参数
    """解码 uint32 out 参数。"""
    return int(槽.value)#无符号值

def 错误文本(接口表,win32码):#格式化 Win32 错误
    """通过 FormatMessageW 格式化 Win32 错误文本。"""
    缓冲=ctypes.create_unicode_buffer(512)#消息缓冲
    长度=接口表['formatMessageW'](格式化系统消息|格式化忽略插入,None,win32码,0,缓冲,512,None)#取系统消息
    return 缓冲.value.strip() if 长度 else ''#去空白

def 抛上次错误(接口表,名称,细节=None):#抛 GetLastError
    """抛出当前 GetLastError 值。"""
    码=接口表['getLastError']()#最后错误
    raise Win32错误(名称,码,细节 if 细节 is not None else 错误文本(接口表,码))#抛出

def 抛win32错误(接口表,名称,win32码,细节=None):#抛显式 Win32 码
    """抛出显式捕获的 Win32 错误码。"""
    raise Win32错误(名称,win32码,细节 if 细节 is not None else 错误文本(接口表,win32码))#抛出

def _进程绑定():#构建基础进程绑定
    """构建基础 Win32 进程绑定表。"""
    global _缓存进程表#模块缓存
    if _缓存进程表 is not None:#已缓存
        return _缓存进程表#直接返回
    上下文=_绑定()#共享库
    内核=上下文['kernel32']#kernel32
    高级=上下文['advapi32']#advapi32
    _缓存进程表={#基础表
        'closeHandle':内核.CloseHandle,#关闭句柄
        'getLastError':内核.GetLastError,#最后错误
        'formatMessageW':内核.FormatMessageW,#格式化消息
        'createPipe':内核.CreatePipe,#创建管道
        'setHandleInformation':内核.SetHandleInformation,#句柄继承
        'createProcessAsUserW':高级.CreateProcessAsUserW,#受限令牌创建进程
        'readFile':内核.ReadFile,#读文件/管道
        'peekNamedPipe':内核.PeekNamedPipe,#窥视命名管道
        'waitForSingleObject':内核.WaitForSingleObject,#等待对象
        'getExitCodeProcess':内核.GetExitCodeProcess,#进程退出码
        'createJobObjectW':内核.CreateJobObjectW,#创建作业
        'setInformationJobObject':内核.SetInformationJobObject,#设置作业信息
        'assignProcessToJobObject':内核.AssignProcessToJobObject,#分配进程到作业
        'resumeThread':内核.ResumeThread,#恢复线程
        'terminateProcess':内核.TerminateProcess,#终止进程
        'getStdHandle':内核.GetStdHandle,#标准句柄
    }#结束基础表
    return _缓存进程表#返回

def 扩展win32进程绑定(创建扩展):#扩展共享绑定表
    """用调用方拥有的 Win32 API 族扩展共享进程表。"""
    表=dict(_进程绑定())#复制基础表
    表.update(创建扩展(_绑定()))#合并扩展
    return 表#合并后的表

def 引用参数(参数):#按 CommandLineToArgvW 规则引用一个参数
    """按 CommandLineToArgvW 规则引用一个 argv 项。"""
    if 参数=='':#空串
        return '""'#空引号
    if not any(字符 in 参数 for 字符 in ' \t\n\r"'):#无需引用
        return 参数#原样
    引用='"';索引=0#构造引号串
    while 索引<len(参数):#逐字符
        反斜杠=0#连续反斜杠计数
        while 索引<len(参数) and 参数[索引]=='\\':#数反斜杠
            反斜杠+=1;索引+=1#前进
        if 索引==len(参数):#结尾反斜杠
            引用+='\\'*(反斜杠*2)#加倍
        elif 参数[索引]=='"':#转义引号
            引用+='\\'*(反斜杠*2+1)+'"';索引+=1#写入
        else:#普通字符
            引用+='\\'*反斜杠+参数[索引];索引+=1#写入
    return 引用+'"'#闭合

def 构建命令行(程序,参数们):#构建 CreateProcess 命令行
    """构建 CreateProcessAsUserW 可接受的命令行。"""
    return ' '.join([引用参数(程序),*[引用参数(项) for 项 in 参数们]])#拼接

def _尽力关闭(接口表,句柄):#尽力关闭句柄
    """尽力关闭句柄，忽略空句柄。"""
    if not 是否空指针(句柄):#有句柄
        接口表['closeHandle'](句柄)#关闭

def _创建管道(接口表,拥有):#创建匿名管道对
    """创建匿名管道对并登记所有权。"""
    读槽=分配指针槽();写槽=分配指针槽()#out 参数
    if 接口表['createPipe'](ctypes.byref(读槽),ctypes.byref(写槽),None,0)==0:#创建失败
        抛上次错误(接口表,'CreatePipe')#抛出
    读=解码指针(读槽);写=解码指针(写槽)#解码
    if 读 is None or 写 is None:#空句柄
        _尽力关闭(接口表,读);_尽力关闭(接口表,写)#清理
        抛上次错误(接口表,'CreatePipe','null pipe handle')#抛出
    拥有.add(读);拥有.add(写)#登记所有权
    return {'read':读,'write':写}#管道对

def _编码启动信息(标准输入,标准输出,标准错误):#编码 STARTUPINFOW
    """编码带 stdio 的 STARTUPINFOW。"""
    缓冲=bytearray(启动信息w大小)#零缓冲
    struct.pack_into('I',缓冲,0,启动信息w大小)#cb
    struct.pack_into('I',缓冲,44,使用标准句柄)#dwFlags 偏移按 x64 STARTUPINFOW
    struct.pack_into('Q',缓冲,56,int(标准输入) if 标准输入 is not None else 0)#hStdInput
    struct.pack_into('Q',缓冲,64,int(标准输出) if 标准输出 is not None else 0)#hStdOutput
    struct.pack_into('Q',缓冲,72,int(标准错误) if 标准错误 is not None else 0)#hStdError
    return 缓冲#结构缓冲

def _创建受限进程(接口表,选项,命令行,创建标志,启动信息,进程信息):#CreateProcessAsUserW 包装
    """受限令牌创建进程；显式环境块在 ctypes 下会触发 ERROR_INVALID_PARAMETER，因此 lpEnvironment 保持 NULL。"""
    return 接口表['createProcessAsUserW'](选项['token'],None,命令行,None,None,1,创建标志,None,选项['cwd'],启动信息,进程信息)#创建

def 生成管道进程(接口表,选项):#生成带管道 stdout/stderr 的进程
    """用匿名管道 stdout/stderr 与立即 stdin EOF 生成进程。"""
    拥有=set()#拥有句柄
    try:#创建管道与进程
        标准输入=_创建管道(接口表,拥有);标准输出=_创建管道(接口表,拥有);标准错误=_创建管道(接口表,拥有)#三组管道
        for 句柄,标签 in [(标准输入['read'],'stdin read end'),(标准输出['write'],'stdout write end'),(标准错误['write'],'stderr write end')]:#继承端
            if 接口表['setHandleInformation'](句柄,句柄可继承,句柄可继承)==0:#设置继承
                抛上次错误(接口表,'SetHandleInformation',标签)#抛出
        启动=_编码启动信息(标准输入['read'],标准输出['write'],标准错误['write'])#STARTUPINFOW
        进程信息=ctypes.create_string_buffer(进程信息大小)#PROCESS_INFORMATION
        命令行=构建命令行(选项['command'],选项['args'])#命令行
        if _创建受限进程(接口表,选项,命令行,0,启动,进程信息)==0:#创建失败
            抛win32错误(接口表,'CreateProcessAsUserW',接口表['getLastError'](),'command: '+选项['command']+', cwd: '+选项['cwd'])#抛出
        进程句柄,线程句柄,进程id,线程id=struct.unpack_from('PPII',进程信息.raw)#解码
        if 是否空指针(进程句柄) or 是否空指针(线程句柄):#空句柄
            if not 是否空指针(进程句柄):接口表['terminateProcess'](进程句柄,1)#终止
            _尽力关闭(接口表,线程句柄);_尽力关闭(接口表,进程句柄)#清理
            raise Exception('CreateProcessAsUserW succeeded but returned null process/thread handles (pid '+str(进程id)+')')#异常
        for 句柄 in (标准输入['read'],标准输入['write'],标准输出['write'],标准错误['write']):#关闭写端/多余读端
            if 句柄 in 拥有:拥有.remove(句柄);_尽力关闭(接口表,句柄)#关闭
        _尽力关闭(接口表,线程句柄)#线程句柄不再需要
        return {'pid':进程id,'process':进程句柄,'stdoutRead':标准输出['read'],'stderrRead':标准错误['read']}#调用方拥有
    except BaseException:#失败清理
        for 句柄 in list(拥有):_尽力关闭(接口表,句柄)#关闭全部拥有句柄
        raise#再抛

def 排空管道(接口表,句柄):#排空一条匿名管道
    """排空匿名管道直到写端关闭；总是关闭读端。"""
    块们=[];计数槽=分配uint32()#缓冲与计数
    try:#读直到 EOF
        while True:#循环窥视/读取
            if 接口表['peekNamedPipe'](句柄,None,0,None,ctypes.byref(计数槽),None)==0:#窥视失败
                码=接口表['getLastError']()#错误码
                if 码 in (管道断开错误,无数据错误):break#正常 EOF
                抛上次错误(接口表,'PeekNamedPipe','drain failure after '+str(len(块们))+' chunk(s)')#失败
            可用=解码uint32(计数槽)#可读字节
            if 可用>0:#有数据
                缓冲=ctypes.create_string_buffer(可用)#读缓冲
                if 接口表['readFile'](句柄,缓冲,可用,ctypes.byref(计数槽),None)==0:#读失败
                    抛上次错误(接口表,'ReadFile','drain failure after '+str(len(块们))+' chunk(s)')#失败
                块们.append(缓冲.raw[:解码uint32(计数槽)])#记下块
            time.sleep(0.001)#退避 1ms
        return b''.join(块们)#完整字节
    finally:#总是关闭
        _尽力关闭(接口表,句柄)#关闭读端

def 等待进程退出(接口表,进程):#等待进程并关闭句柄
    """等待进程退出并总是关闭其句柄。"""
    退出槽=分配uint32()#退出码槽
    try:#等待并取码
        if 接口表['waitForSingleObject'](进程,无限等待)==0xFFFFFFFF:#等待失败
            抛上次错误(接口表,'WaitForSingleObject')#抛出
        if 接口表['getExitCodeProcess'](进程,ctypes.byref(退出槽))==0:#取码失败
            抛上次错误(接口表,'GetExitCodeProcess')#抛出
        return 解码uint32(退出槽)#退出码
    finally:#总是关闭
        _尽力关闭(接口表,进程)#关闭进程句柄

def _创建关闭即杀作业(接口表):#创建 kill-on-close 作业
    """创建 kill-on-close 作业对象。"""
    作业=接口表['createJobObjectW'](None,None)#匿名作业
    if 是否空指针(作业):抛上次错误(接口表,'CreateJobObjectW')#失败
    信息=bytearray(作业扩展限制大小)#扩展限制
    struct.pack_into('I',信息,作业扩展限制旗标偏移,关闭即杀作业)#LimitFlags
    缓冲=(ctypes.c_char*作业扩展限制大小).from_buffer(信息)#ctypes 缓冲
    if 接口表['setInformationJobObject'](作业,作业扩展限制类,缓冲,len(信息))==0:#设置失败
        码=接口表['getLastError']();_尽力关闭(接口表,作业);抛win32错误(接口表,'SetInformationJobObject',码)#抛出
    return 作业#作业句柄

def 生成继承作业进程(接口表,选项):#挂起创建、加入作业、再恢复
    """挂起创建子进程，分配到 kill-on-close 作业，再恢复运行。"""
    作业=_创建关闭即杀作业(接口表)#作业
    def 取标准句柄(选择器,标签):#取标准句柄
        句柄=接口表['getStdHandle'](选择器)#系统标准句柄
        if not 是否空指针(句柄):return 句柄#有效
        码=接口表['getLastError']();_尽力关闭(接口表,作业);抛win32错误(接口表,'GetStdHandle',码,'null '+标签+' handle')#失败
    标准输入=取标准句柄(标准输入句柄,'stdin');标准输出=取标准句柄(标准输出句柄,'stdout');标准错误=取标准句柄(标准错误句柄,'stderr')#stdio
    已启用=[];创建结果=0;失败码=0#状态
    try:#暂时恢复继承位并创建
        for 句柄,标签 in [(标准输入,'stdin'),(标准输出,'stdout'),(标准错误,'stderr')]:#三路 stdio
            if 接口表['setHandleInformation'](句柄,句柄可继承,句柄可继承)==0:抛上次错误(接口表,'SetHandleInformation',标签+' (enable inherit)')#失败
            已启用.append(句柄)#记下
        启动信息=_编码启动信息(标准输入,标准输出,标准错误)#STARTUPINFOW
        进程信息=ctypes.create_string_buffer(进程信息大小)#PROCESS_INFORMATION
        创建结果=_创建受限进程(接口表,选项,构建命令行(选项['command'],选项['args']),挂起创建,启动信息,进程信息)#挂起创建
        if 创建结果==0:失败码=接口表['getLastError']()#记失败码
    except BaseException as 错误:#创建前失败
        _尽力关闭(接口表,作业);raise 错误#清理作业并抛出
    finally:#恢复继承位
        for 句柄 in 已启用:接口表['setHandleInformation'](句柄,句柄可继承,0)#尽力恢复
    if 创建结果==0:#创建失败
        _尽力关闭(接口表,作业);抛win32错误(接口表,'CreateProcessAsUserW',失败码,'command: '+选项['command']+', cwd: '+选项['cwd'])#抛出
    进程句柄,线程句柄,进程id,线程id=struct.unpack_from('PPII',进程信息.raw)#解码
    if 是否空指针(进程句柄) or 是否空指针(线程句柄):#空句柄
        if not 是否空指针(进程句柄):接口表['terminateProcess'](进程句柄,1)#终止
        _尽力关闭(接口表,作业);_尽力关闭(接口表,线程句柄);_尽力关闭(接口表,进程句柄)#清理
        raise Exception('CreateProcessAsUserW succeeded but returned null process/thread handles (pid '+str(进程id)+')')#异常
    if 接口表['assignProcessToJobObject'](作业,进程句柄)==0:#加入作业失败
        码=接口表['getLastError']();接口表['terminateProcess'](进程句柄,1);_尽力关闭(接口表,线程句柄);_尽力关闭(接口表,进程句柄);_尽力关闭(接口表,作业);抛win32错误(接口表,'AssignProcessToJobObject',码,'pid '+str(进程id))#失败
    if 接口表['resumeThread'](线程句柄)==0xFFFFFFFF:#恢复失败
        码=接口表['getLastError']();_尽力关闭(接口表,线程句柄);_尽力关闭(接口表,进程句柄);_尽力关闭(接口表,作业);抛win32错误(接口表,'ResumeThread',码,'pid '+str(进程id))#失败
    _尽力关闭(接口表,线程句柄)#线程句柄不再需要
    return {'pid':进程id,'process':进程句柄,'job':作业}#调用方拥有
