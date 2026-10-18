'Win32 文件夹对话框的本机绑定。模块到处都能导入，DLL 只在真正调用时加载'
import ctypes,re
from types import SimpleNamespace as 简单命名空间#绑定与对话框对象
from .异常 import 目录选择器原生错误#失败

全匹配=re.fullmatch#整段匹配
忽略大小写=re.I#忽略大小写
十六进制=bytes.fromhex#十六进制字节
空指针=ctypes.c_void_p#指针
指针列=ctypes.POINTER(空指针)#指针数组
长整=ctypes.c_long#有符号 32 位
无符号长=ctypes.c_ulong#无符号 32 位
无符号整=ctypes.c_uint32#无符号 32 位
字节类型=ctypes.c_ubyte#字节
整型=ctypes.c_int#整数
指针大小=ctypes.c_size_t#指针宽无符号
有符号大小=ctypes.c_ssize_t#指针宽有符号
宽字符=ctypes.c_wchar_p#UTF-16 字符串
函数类型=ctypes.WINFUNCTYPE#stdcall 函数
转换=ctypes.cast#按类型重看指针
取地址=ctypes.byref#取地址
宽字符串于=ctypes.wstring_at#读到 NUL 的 UTF-16
创建缓冲=ctypes.create_string_buffer#字节缓冲
尺寸=ctypes.sizeof#类型宽度

套间线程=0x2#COINIT_APARTMENTTHREADED
进程内服务=0x1#CLSCTX_INPROC_SERVER
文件系统路径=0x80058000#SIGDN_FILESYSPATH
DPI上下文=(-4,-3,-2)#per-monitor-v2、per-monitor、system-aware
关闭消息=0x10#WM_CLOSE
菜单键=0x12#VK_MENU
键抬起=0x2#KEYEVENTF_KEYUP
释放槽=2#IUnknown::Release
显示槽=3#IModalWindow::Show
选项槽=9#IFileDialog::SetOptions
标题槽=17#IFileDialog::SetTitle
结果槽=20#IFileDialog::GetResult
显示名槽=5#IShellItem::GetDisplayName


def 解析GUID(文本):
    '把 xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx 编成 16 字节小端'
    表达式=r'([0-9a-f]{8})-([0-9a-f]{4})-([0-9a-f]{4})-([0-9a-f]{4})-([0-9a-f]{12})'#规范形式
    匹配=全匹配(表达式,文本,忽略大小写)#五段
    数据1=int(匹配.group(1),16).to_bytes(4,'little')#Data1
    数据2=int(匹配.group(2),16).to_bytes(2,'little')#Data2
    数据3=int(匹配.group(3),16).to_bytes(2,'little')#Data3
    数据4=十六进制(匹配.group(4)+匹配.group(5))#Data4
    return 数据1+数据2+数据3+数据4#16 字节


文件打开对话框类=解析GUID('dc1c5a9c-e88a-4dde-a5a1-60f82a20aef7')#CLSID_FileOpenDialog
文件打开对话框接口=解析GUID('d57c7288-d4ad-4768-be02-9d969532d960')#IID_IFileOpenDialog


def 加载动态库(名):
    '加载 DLL。只在真正调用时执行，非 Windows 导入本模块不会碰到它'
    return ctypes.WinDLL(名)#stdcall


def 加载绑定():
    '加载 ole32、user32、kernel32，返回这一线程用的对话框绑定'
    ################################
    #库与 COM 函数
    ################################
    组件对象库=加载动态库('ole32.dll')#COM
    窗口库=加载动态库('user32.dll')#窗口与键盘
    核心库=加载动态库('kernel32.dll')#线程号
    初始化COM=组件对象库.CoInitializeEx#CoInitializeEx
    初始化COM.argtypes=[空指针,无符号整]#参数
    初始化COM.restype=长整#HRESULT
    反初始化COM=组件对象库.CoUninitialize#CoUninitialize
    反初始化COM.argtypes=[]#无参
    反初始化COM.restype=None#无返回
    创建实例=组件对象库.CoCreateInstance#CoCreateInstance
    创建实例.argtypes=[空指针,空指针,无符号整,空指针,指针列]#参数
    创建实例.restype=长整#HRESULT
    释放任务内存=组件对象库.CoTaskMemFree#CoTaskMemFree
    释放任务内存.argtypes=[空指针]#参数
    释放任务内存.restype=None#无返回
    当前线程=核心库.GetCurrentThreadId#GetCurrentThreadId
    当前线程.argtypes=[]#无参
    当前线程.restype=无符号整#线程号
    键盘=窗口库.keybd_event#keybd_event
    键盘.argtypes=[字节类型,字节类型,无符号整,指针大小]#参数
    键盘.restype=None#无返回
    ################################
    #虚表原型
    ################################
    显示原型=函数类型(长整,空指针,空指针)#Show
    选项原型=函数类型(长整,空指针,无符号整)#SetOptions
    标题原型=函数类型(长整,空指针,宽字符)#SetTitle
    结果原型=函数类型(长整,空指针,指针列)#GetResult
    显示名原型=函数类型(长整,空指针,无符号整,指针列)#GetDisplayName
    释放原型=函数类型(无符号长,空指针)#Release

    def 取槽(对象,槽,原型):
        '按下标取出虚表函数。对象第一个指针是虚表'
        虚表=转换(对象,指针列)[0]#虚表
        函数指针=转换(虚表,指针列)[槽]#槽位
        return 原型(函数指针)#可调用

    def 设置线程DPI():
        '尽量要最高的线程 DPI。没有符号或全部被拒绝时仍然继续'
        try:#1607 之后才有这个符号
            设置=窗口库.SetThreadDpiAwarenessContext#函数
        except AttributeError:#更老的系统
            return#对话框仍可用，只是可能发糊
        设置.argtypes=[空指针]#参数
        设置.restype=空指针#先前上下文
        宽=尺寸(空指针)*8#指针位数
        掩码=(1<<宽)-1#无符号掩码
        for 上下文 in DPI上下文:#从最好到可用
            try:#调用时才知道符号在不在
                先前=设置(空指针(上下文 & 掩码))#尝试
            except (AttributeError,OverflowError):#没有符号，或伪句柄塞不进指针
                return#继续，对话框可能发糊
            if 先前 is not None and 先前!=0:#被接受
                return#停

    def 初始化套间():
        'CoInitializeEx，STA。S_FALSE 重入也算成功'
        return 初始化COM(None,套间线程)#HRESULT

    def 反初始化():
        '与成功的 CoInitializeEx 配对'
        反初始化COM()#CoUninitialize

    def 当前线程号():
        '本线程的系统线程号，驱动用它从外面关窗口'
        return int(当前线程())#线程号

    def 按Alt抢前台():
        '合成一次 Alt 按下再抬起，让后台拉起的进程能把对话框放到前台'
        键盘(菜单键,0,0,0)#按下
        键盘(菜单键,0,键抬起,0)#抬起

    def 创建文件夹对话框():
        'CoCreateInstance。失败抛错'
        类缓冲=创建缓冲(文件打开对话框类)#CLSID
        接口缓冲=创建缓冲(文件打开对话框接口)#IID
        类指针=转换(类缓冲,空指针)#CLSID 指针
        接口指针=转换(接口缓冲,空指针)#IID 指针
        出=空指针()#对象
        码=创建实例(类指针,None,进程内服务,接口指针,取地址(出))#创建
        if 码<0:#失败
            文案='CoCreateInstance(FileOpenDialog) failed: HRESULT 0x'+format(码 & 0xFFFFFFFF,'x')#带码
            raise 目录选择器原生错误(文案)#失败
        对话框=出.value#对象指针

        def 设置选项(选项):
            'IFileDialog::SetOptions'
            return 取槽(对话框,选项槽,选项原型)(对话框,选项)#HRESULT

        def 设置标题(标题):
            'IFileDialog::SetTitle'
            return 取槽(对话框,标题槽,标题原型)(对话框,标题)#HRESULT

        def 显示():
            'IModalWindow::Show，无所有者。阻塞到人选完或关掉'
            return 取槽(对话框,显示槽,显示原型)(对话框,None)#HRESULT

        def 结果路径():
            'GetResult 再 GetDisplayName。成功时带 path'
            项出=空指针()#IShellItem
            取项=取槽(对话框,结果槽,结果原型)(对话框,取地址(项出))#GetResult
            if 取项<0:#失败
                return {'hr':取项}#只有码
            try:#用完释放 shell item
                名出=空指针()#宽字符串
                取名调用=取槽(项出.value,显示名槽,显示名原型)#GetDisplayName
                取名=取名调用(项出.value,文件系统路径,取地址(名出))#调用
                if 取名<0:#失败
                    return {'hr':取名}#只有码
                路径=宽字符串于(名出.value)#UTF-16
                释放任务内存(名出)#释放 COM 字符串
                return {'hr':取名,'path':路径}#路径
            finally:#释放 item
                取槽(项出.value,释放槽,释放原型)(项出.value)#Release

        def 释放():
            '丢掉对话框的 COM 引用'
            取槽(对话框,释放槽,释放原型)(对话框)#Release

        对话框对象=简单命名空间()#这一次创建出来的对话框
        对话框对象.设置选项=设置选项#SetOptions
        对话框对象.设置标题=设置标题#SetTitle
        对话框对象.显示=显示#Show
        对话框对象.结果路径=结果路径#GetResult
        对话框对象.释放=释放#Release
        return 对话框对象#交给顺序

    绑定对象=简单命名空间()#这一线程的本机面
    绑定对象.设置线程DPI=设置线程DPI#DPI
    绑定对象.初始化套间=初始化套间#STA
    绑定对象.反初始化=反初始化#CoUninitialize
    绑定对象.创建文件夹对话框=创建文件夹对话框#CoCreateInstance
    绑定对象.当前线程号=当前线程号#线程号
    绑定对象.按Alt抢前台=按Alt抢前台#Alt
    return 绑定对象#交给顺序


def 关闭线程窗口(线程号):
    '给该线程每个窗口投 WM_CLOSE。Show 被关掉后返回取消码'
    窗口库=加载动态库('user32.dll')#窗口
    投递=窗口库.PostMessageW#PostMessageW
    投递.argtypes=[空指针,无符号整,指针大小,有符号大小]#参数
    投递.restype=整型#是否投出
    枚举=窗口库.EnumThreadWindows#EnumThreadWindows
    枚举原型=函数类型(整型,空指针,空指针)#枚举回调
    枚举.argtypes=[无符号整,枚举原型,有符号大小]#参数
    枚举.restype=整型#是否枚举完

    def 回调(窗口,参数):
        '给这个窗口投关闭消息，并继续枚举'
        投递(窗口,关闭消息,0,0)#WM_CLOSE
        return 1#继续

    回调对象=枚举原型(回调)#在枚举期间保持引用
    try:#枚举
        枚举(线程号,回调对象,0)#每个窗口
    finally:#用完丢掉回调
        del 回调对象#不再需要
