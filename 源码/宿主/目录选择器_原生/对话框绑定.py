'Win32 文件夹对话框的 ctypes 绑定。只在真正调用时加载 DLL'
import ctypes#本机调用
from ctypes import wintypes#Windows 类型

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

class GUID(ctypes.Structure):#内存中的 GUID
    'CoCreateInstance 要的 16 字节布局'
    _fields_=[#字段
        ('数据1',wintypes.DWORD),#Data1
        ('数据2',wintypes.WORD),#Data2
        ('数据3',wintypes.WORD),#Data3
        ('数据4',wintypes.BYTE*8),#Data4
    ]#结束

def 解析GUID(文本):#规范 GUID 字符串
    'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'
    段=文本.split('-')#五段
    尾=bytes.fromhex(段[3]+段[4])#后 8 字节
    return GUID(int(段[0],16),int(段[1],16),int(段[2],16),(wintypes.BYTE*8)(*尾))#结构

文件打开对话框类=解析GUID('dc1c5a9c-e88a-4dde-a5a1-60f82a20aef7')#CLSID_FileOpenDialog
文件打开对话框接口=解析GUID('d57c7288-d4ad-4768-be02-9d969532d960')#IID_IFileOpenDialog

显示原型=ctypes.WINFUNCTYPE(ctypes.c_long,ctypes.c_void_p,ctypes.c_void_p)#Show
选项原型=ctypes.WINFUNCTYPE(ctypes.c_long,ctypes.c_void_p,ctypes.c_uint32)#SetOptions
标题原型=ctypes.WINFUNCTYPE(ctypes.c_long,ctypes.c_void_p,ctypes.c_wchar_p)#SetTitle
结果原型=ctypes.WINFUNCTYPE(ctypes.c_long,ctypes.c_void_p,ctypes.POINTER(ctypes.c_void_p))#GetResult
显示名原型=ctypes.WINFUNCTYPE(ctypes.c_long,ctypes.c_void_p,ctypes.c_int32,ctypes.POINTER(ctypes.c_void_p))#GetDisplayName
释放原型=ctypes.WINFUNCTYPE(ctypes.c_ulong,ctypes.c_void_p)#Release
枚举原型=ctypes.WINFUNCTYPE(ctypes.c_int,ctypes.c_void_p,ctypes.c_void_p)#EnumWindowsProc

def 取槽(对象,槽,原型):#绑定虚表槽
    '对象第一个指针是虚表'
    虚表=ctypes.cast(对象,ctypes.POINTER(ctypes.c_void_p))[0]#虚表
    函数=ctypes.cast(虚表,ctypes.POINTER(ctypes.c_void_p))[槽]#槽
    return 原型(函数)#可调用

def 句柄值(数):#把负的伪句柄收成指针宽
    'SetThreadDpiAwarenessContext 吃的是指针宽常量'
    宽=ctypes.sizeof(ctypes.c_void_p)*8#位数
    return ctypes.c_void_p(数 & ((1<<宽)-1))#无符号指针

class 文件夹对话框:#一次创建出来的对话框
    '虚表调用'
    def __init__(自身,指针):#记下 COM 指针
        '指针在释放前有效'
        自身.指针=指针#对象

    def 设置选项(自身,选项):#SetOptions
        '返回 HRESULT'
        return 取槽(自身.指针,选项槽,选项原型)(自身.指针,选项)#调用

    def 设置标题(自身,标题):#SetTitle
        '返回 HRESULT'
        return 取槽(自身.指针,标题槽,标题原型)(自身.指针,标题)#调用

    def 显示(自身):#Show，无所有者
        '阻塞到人选完或关掉'
        return 取槽(自身.指针,显示槽,显示原型)(自身.指针,None)#调用

    def 结果路径(自身):#GetResult 再 GetDisplayName
        '成功时带 path'
        项出=ctypes.c_void_p()#IShellItem
        取项=取槽(自身.指针,结果槽,结果原型)(自身.指针,ctypes.byref(项出))#GetResult
        if 取项<0:#失败
            return {'hr':取项}#只有码
        try:#用完释放 shell item
            名出=ctypes.c_void_p()#宽字符串
            取名=取槽(项出,显示名槽,显示名原型)(项出,文件系统路径,ctypes.byref(名出))#GetDisplayName
            if 取名<0:#失败
                return {'hr':取名}#只有码
            路径=ctypes.wstring_at(名出)#UTF-16
            ctypes.windll.ole32.CoTaskMemFree(名出)#释放 COM 字符串
            return {'hr':取名,'path':路径}#路径
        finally:#释放 item
            取槽(项出,释放槽,释放原型)(项出)#Release

    def 释放(自身):#Release 对话框
        '丢掉 COM 引用'
        取槽(自身.指针,释放槽,释放原型)(自身.指针)#Release

class 绑定:#给运行文件夹对话框用的本机面
    '加载 ole32、user32、kernel32'
    def __init__(自身):#加载 DLL
        '函数签名在这里定死'
        自身.ole32=ctypes.WinDLL('ole32')#COM
        自身.user32=ctypes.WinDLL('user32')#窗口与键盘
        自身.kernel32=ctypes.WinDLL('kernel32')#线程号
        自身.ole32.CoInitializeEx.argtypes=[ctypes.c_void_p,ctypes.c_uint32]#参数
        自身.ole32.CoInitializeEx.restype=ctypes.c_long#HRESULT
        自身.ole32.CoUninitialize.argtypes=[]#无参
        自身.ole32.CoCreateInstance.argtypes=[#创建
            ctypes.POINTER(GUID),ctypes.c_void_p,ctypes.c_uint32,ctypes.POINTER(GUID),ctypes.POINTER(ctypes.c_void_p),
        ]#结束
        自身.ole32.CoCreateInstance.restype=ctypes.c_long#HRESULT
        自身.kernel32.GetCurrentThreadId.restype=ctypes.c_uint32#线程号
        自身.user32.keybd_event.argtypes=[ctypes.c_ubyte,ctypes.c_ubyte,ctypes.c_uint32,ctypes.c_size_t]#键盘

    def 设置线程DPI(自身):#尽量要最高的线程 DPI
        '符号不存在或全部被拒绝时仍然继续，对话框只是可能发糊'
        try:#1607 之后才有
            设置=自身.user32.SetThreadDpiAwarenessContext#函数
        except AttributeError:#更老的系统
            return#不设
        设置.argtypes=[ctypes.c_void_p]#参数
        设置.restype=ctypes.c_void_p#先前上下文
        for 上下文 in DPI上下文:#从最好到可用
            if 设置(句柄值(上下文)) not in (None,0):#被接受
                return#停

    def 初始化套间(自身):#CoInitializeEx STA
        'S_FALSE 重入也算成功'
        return 自身.ole32.CoInitializeEx(None,套间线程)#HRESULT

    def 反初始化(自身):#CoUninitialize
        '与成功的 CoInitializeEx 配对'
        自身.ole32.CoUninitialize()#调用

    def 当前线程号(自身):#GetCurrentThreadId
        '驱动用它从外面关窗口'
        return int(自身.kernel32.GetCurrentThreadId())#线程号

    def 按Alt抢前台(自身):#合成一次 Alt 按下再抬起
        '让后台拉起的进程能把对话框放到前台'
        自身.user32.keybd_event(菜单键,0,0,0)#按下
        自身.user32.keybd_event(菜单键,0,键抬起,0)#抬起

    def 创建文件夹对话框(自身):#CoCreateInstance
        '失败抛错'
        出=ctypes.c_void_p()#对象
        码=自身.ole32.CoCreateInstance(#创建
            ctypes.byref(文件打开对话框类),None,进程内服务,ctypes.byref(文件打开对话框接口),ctypes.byref(出),
        )#结束
        if 码<0:#失败
            raise OSError('CoCreateInstance(FileOpenDialog) failed: HRESULT 0x'+format(码 & 0xFFFFFFFF,'x'))#抛
        return 文件夹对话框(出)#包装

def 加载绑定():#生产用绑定
    '返回绑定对象'
    return 绑定()#新建

def 关闭线程窗口(线程号):#给该线程每个窗口投 WM_CLOSE
    'Show 被关掉后返回取消码'
    user32=ctypes.WinDLL('user32')#窗口
    user32.PostMessageW.argtypes=[ctypes.c_void_p,ctypes.c_uint32,ctypes.c_size_t,ctypes.c_ssize_t]#参数
    user32.PostMessageW.restype=ctypes.c_int#是否投出
    def 回调(窗口,_参数):#每个窗口
        '投关闭消息并继续枚举'
        user32.PostMessageW(窗口,关闭消息,0,0)#关闭
        return 1#继续
    函数=枚举原型(回调)#保持引用
    user32.EnumThreadWindows(线程号,函数,0)#枚举
