"""受限进程 spawn：stdio 用匿名管道，STARTUPINFOW 带 STARTF_USESTDHANDLES，在受限令牌下 CreateProcessAsUserW，然后排空管道并等待退出。控制台隔离（CREATE_NO_WINDOW / CREATE_NEW_CONSOLE）故意缺席：在本限制方案下隐藏控制台子进程以 STATUS_DLL_INIT_FAILED (0xC0000142) 死去——已实证；stdio 重定向基于管道，不受影响；子进程共享宿主控制台。"""
import re,time,ctypes#引号判定、让出与缓冲视图
from .ffi import (
    分配指针槽,#指针槽
    分配进程信息,#进程信息
    分配启动信息,#启动信息
    分配无符号32,#DWORD槽
    解码指针,#解码指针
    解码进程信息,#解码进程信息
    解码无符号32,#解码DWORD
    编码启动信息,#编码启动信息
    启动信息输入,#启动字段
    是否空指针,#空指针
    抛上次错误,#BOOL失败
    抛Win32,#ERROR_*失败
)#导入FFI辅助
from . import win32_abi as abi#ABI常量

def 引用参数(参数):#按CommandLineToArgvW引用
    """按 CommandLineToArgvW 解析规则引用一个参数。"""
    if 参数=='':#空串
        return '""'#必须成对引号
    if re.search(r'[\s"]',参数) is None:#无空白无引号
        return 参数#原样
    已引='"'#开口引号
    下标=0#字符下标
    while 下标<len(参数):#逐字符
        反斜杠数=0#连续反斜杠
        while 下标<len(参数) and 参数[下标]=='\\':#数反斜杠
            反斜杠数+=1#加一
            下标+=1#前进
        if 下标==len(参数):#已到末尾
            已引+='\\'*(反斜杠数*2)#加倍尾随反斜杠
        elif 参数[下标]=='"':#遇到引号
            已引+='\\'*(反斜杠数*2+1)+'"'#加倍反斜杠再逃逸引号
            下标+=1#前进过引号
        else:#普通字符
            已引+='\\'*反斜杠数+参数[下标]#原样反斜杠加该字符
            下标+=1#前进
    return 已引+'"'#收尾引号

def 构建命令行(程序,参数们):#拼命令行
    """从程序加 argv 建成 CreateProcess 解析的那一条命令行。"""
    return ' '.join(引用参数(项) for 项 in [程序,*参数们])#逐条引用再空格拼接

def 创建管道(接口):#创建匿名管道
    """创建一对匿名管道端。"""
    读槽=分配指针槽()#读端槽
    写槽=分配指针槽()#写端槽
    if 接口.createPipe(读槽,写槽,None,0)==0:#创建失败
        抛上次错误(接口,'CreatePipe')#抛出
    读=解码指针(读槽)#取出读端
    写=解码指针(写槽)#取出写端
    if 读 is None or 写 is None:#空句柄
        抛上次错误(接口,'CreatePipe','null pipe handle')#空句柄
    return {'read':读,'write':写}#两端

def 设可继承(接口,句柄,标签):#打开句柄继承
    """打开句柄继承位。"""
    if 接口.setHandleInformation(句柄,abi.句柄可继承,abi.句柄可继承)==0:#设置失败
        抛上次错误(接口,'SetHandleInformation',标签)#带标签抛出

def 隔离生成(接口,令牌,选项):#管道stdio隔离spawn
    """在受限令牌下用管道 stdio 创建进程。"""
    标准入=创建管道(接口)#stdin管道
    标准出=创建管道(接口)#stdout管道
    标准误=创建管道(接口)#stderr管道
    设可继承(接口,标准入['read'],'stdin read end')#stdin读端可继承
    设可继承(接口,标准出['write'],'stdout write end')#stdout写端可继承
    设可继承(接口,标准误['write'],'stderr write end')#stderr写端可继承
    启动信息=分配启动信息()#启动信息
    编码启动信息(启动信息,启动信息输入(abi.启动信息W大小,abi.使用标准句柄,标准入['read'],标准出['write'],标准误['write']))#写入stdio字段
    进程信息=分配进程信息()#进程信息
    命令行=构建命令行(选项['command'],选项['args'])#已引用命令行
    已创建=接口.createProcessAsUserW(令牌,None,命令行,None,None,1,0,None,选项['cwd'],启动信息,进程信息)#在受限令牌下创建
    if 已创建==0:#创建失败
        win32码=接口.getLastError()#先记下码
        接口.closeHandle(标准入['read'])#关stdin读
        接口.closeHandle(标准入['write'])#关stdin写
        接口.closeHandle(标准出['read'])#关stdout读
        接口.closeHandle(标准出['write'])#关stdout写
        接口.closeHandle(标准误['read'])#关stderr读
        接口.closeHandle(标准误['write'])#关stderr写
        抛Win32(接口,'CreateProcessAsUserW',win32码,'command: '+选项['command']+', cwd: '+选项['cwd'])#带码抛出
    信息=解码进程信息(进程信息)#解码进程信息
    进程句柄=信息.hProcess#进程句柄
    线程句柄=信息.hThread#线程句柄
    if 进程句柄 is None or 线程句柄 is None:#空句柄
        raise Exception('CreateProcessAsUserW succeeded but returned null process/thread handles (pid '+str(信息.dwProcessId)+')')#成功却空句柄
    接口.closeHandle(标准入['read'])#关宿主stdin读
    接口.closeHandle(标准出['write'])#关宿主stdout写
    接口.closeHandle(标准误['write'])#关宿主stderr写
    接口.closeHandle(标准入['write'])#关宿主stdin写（立刻EOF）
    接口.closeHandle(线程句柄)#关主线程句柄
    return {'pid':信息.dwProcessId,'process':进程句柄,'stdoutRead':标准出['read'],'stderrRead':标准误['read']}#管道spawn结果

def 排空管道(接口,句柄):#排空管道
    """经非阻塞 PeekNamedPipe 轮询把一个管道读端排空成 bytes。"""
    块们=[]#已读块
    while True:#直到EOF
        已读槽=分配无符号32()#已读字节槽
        可用槽=分配无符号32()#可用总量槽
        剩余槽=分配无符号32()#本消息剩余槽
        窥探=接口.peekNamedPipe(句柄,None,0,已读槽,可用槽,剩余槽)#窥探可用
        if 窥探==0:#窥探失败
            win32码=接口.getLastError()#错误码
            if win32码==abi.错误管道断开 or win32码==abi.错误无数据:#子进程关了端
                break#干净EOF
            抛上次错误(接口,'PeekNamedPipe','drain failure after '+str(len(块们))+' chunk(s)')#其余失败
        可用=解码无符号32(可用槽)#可用字节
        if 可用>0:#有数据
            块=bytearray(可用)#读取缓冲
            块视图=(ctypes.c_ubyte*可用).from_buffer(块)#可写视图
            读槽=分配无符号32()#实际读出槽
            if 接口.readFile(句柄,块视图,可用,读槽,None)==0:#读取失败
                抛上次错误(接口,'ReadFile','drain failure after '+str(len(块们))+' chunk(s)')#带块数抛出
            块们.append(bytes(块[0:解码无符号32(读槽)]))#记下已读
        time.sleep(0.001)#让出1ms，避免忙轮询
    接口.closeHandle(句柄)#关掉读端
    return b''.join(块们)#拼接内容

def 等待退出(接口,进程):#等待退出
    """等待进程退出并返回其退出码。"""
    等待结果=接口.waitForSingleObject(进程,abi.无限等待)#无限等待
    if 等待结果==0xFFFFFFFF:#等待失败
        抛上次错误(接口,'WaitForSingleObject')#抛出
    退出码槽=分配无符号32()#退出码槽
    if 接口.getExitCodeProcess(进程,退出码槽)==0:#取码失败
        抛上次错误(接口,'GetExitCodeProcess')#抛出
    接口.closeHandle(进程)#关掉进程句柄
    return 解码无符号32(退出码槽)#退出码

def 创建关闭即杀作业(接口):#创建关闭即杀作业
    """创建关闭即杀作业对象。"""
    作业=接口.createJobObjectW(None,None)#匿名作业
    if 是否空指针(作业):#创建失败
        抛上次错误(接口,'CreateJobObjectW')#抛出
    信息=bytearray(abi.作业扩展限制大小)#扩展限制结构
    信息[abi.作业扩展限制旗标偏移:abi.作业扩展限制旗标偏移+4]=abi.关闭即杀作业.to_bytes(4,'little')#写入LimitFlags
    信息视图=(ctypes.c_ubyte*len(信息)).from_buffer(信息)#可写视图
    if 接口.setInformationJobObject(作业,abi.作业扩展限制类,信息视图,len(信息))==0:#设置失败
        win32码=接口.getLastError()#先记下码
        接口.closeHandle(作业)#关掉作业
        抛Win32(接口,'SetInformationJobObject',win32码)#带码抛出
    return 作业#作业句柄

def 隔离继承生成(接口,令牌,选项):#继承stdio隔离spawn
    """在受限令牌下创建进程，其 stdio 直通到调用方管道。"""
    作业=创建关闭即杀作业(接口)#关闭即杀作业
    标准入=接口.getStdHandle(abi.标准输入句柄)#调用方stdin
    标准出=接口.getStdHandle(abi.标准输出句柄)#调用方stdout
    标准误=接口.getStdHandle(abi.标准错误句柄)#调用方stderr
    if 是否空指针(标准入) or 是否空指针(标准出) or 是否空指针(标准误):#空标准句柄
        接口.closeHandle(作业)#关掉作业
        抛上次错误(接口,'GetStdHandle','null standard handle')#空句柄
    def 使可继承(句柄,标签):#打开继承
        if 接口.setHandleInformation(句柄,abi.句柄可继承,abi.句柄可继承)==0:#设置失败
            抛上次错误(接口,'SetHandleInformation',标签+' (enable inherit)')#带标签抛出
    def 恢复继承(句柄):#关掉继承
        接口.setHandleInformation(句柄,abi.句柄可继承,0)#清继承位，失败故意不检查
    使可继承(标准入,'stdin')#stdin可继承
    使可继承(标准出,'stdout')#stdout可继承
    使可继承(标准误,'stderr')#stderr可继承
    启动信息=分配启动信息()#启动信息
    编码启动信息(启动信息,启动信息输入(abi.启动信息W大小,abi.使用标准句柄,标准入,标准出,标准误))#写入stdio字段
    进程信息=分配进程信息()#进程信息
    命令行=构建命令行(选项['command'],选项['args'])#已引用命令行
    已创建=接口.createProcessAsUserW(令牌,None,命令行,None,None,1,abi.挂起创建,None,选项['cwd'],启动信息,进程信息)#挂起创建
    恢复继承(标准入)#恢复stdin继承
    恢复继承(标准出)#恢复stdout继承
    恢复继承(标准误)#恢复stderr继承
    if 已创建==0:#创建失败
        win32码=接口.getLastError()#先记下码
        接口.closeHandle(作业)#关掉作业
        抛Win32(接口,'CreateProcessAsUserW',win32码,'command: '+选项['command']+', cwd: '+选项['cwd'])#带码抛出
    信息=解码进程信息(进程信息)#解码进程信息
    进程句柄=信息.hProcess#进程句柄
    线程句柄=信息.hThread#线程句柄
    if 进程句柄 is None or 线程句柄 is None:#空句柄
        接口.closeHandle(作业)#关掉作业
        raise Exception('CreateProcessAsUserW succeeded but returned null process/thread handles (pid '+str(信息.dwProcessId)+')')#成功却空句柄
    if 接口.assignProcessToJobObject(作业,进程句柄)==0:#指派作业失败
        win32码=接口.getLastError()#先记下码
        接口.terminateProcess(进程句柄,1)#终止挂起子进程
        接口.closeHandle(线程句柄)#关线程
        接口.closeHandle(进程句柄)#关进程
        接口.closeHandle(作业)#关作业
        抛Win32(接口,'AssignProcessToJobObject',win32码,'pid '+str(信息.dwProcessId))#带码抛出
    if 接口.resumeThread(线程句柄)==0xFFFFFFFF:#恢复失败
        win32码=接口.getLastError()#先记下码
        接口.closeHandle(线程句柄)#关线程
        接口.closeHandle(进程句柄)#关进程
        接口.closeHandle(作业)#关作业（关闭即杀）
        抛Win32(接口,'ResumeThread',win32码,'pid '+str(信息.dwProcessId))#带码抛出
    接口.closeHandle(线程句柄)#关主线程句柄
    return {'pid':信息.dwProcessId,'process':进程句柄,'job':作业}#继承spawn结果
