"""Windows IFileOpenDialog 文件夹选择：ctypes 调用 shell32/ole32 COM。

对齐上游 win32-dialog 的对外契约（选定路径或取消 None，中止则抛错）。Python 侧在调用线程直接 COM，不再派生子进程工人。
"""
import ctypes#Win32 COM
from ctypes import wintypes#Windows 类型

__all__=['选Win32目录','对话框标题']#仅中文公开名

对话框标题='Select Workspace Directory'#与 zenity/osascript 同一文案

# COM / Shell 常量
COINIT_APARTMENTTHREADED=0x2#STA
CLSCTX_INPROC_SERVER=0x1#进程内
FOS_PICKFOLDERS=0x20#只选文件夹
FOS_FORCEFILESYSTEM=0x40#只要文件系统项
SIGDN_FILESYSPATH=0x80058000#文件系统路径
S_OK=0#成功
S_FALSE=1#假成功/取消类
ERROR_CANCELLED=1223#用户取消

class GUID(ctypes.Structure):#COM GUID
    """COM GUID 结构。"""
    _fields_=[('Data1',wintypes.DWORD),('Data2',wintypes.WORD),('Data3',wintypes.WORD),('Data4',wintypes.BYTE*8)]#四段

def _guid(文字):#从标准字符串构造 GUID
    """解析 {xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx}。"""
    文字=文字.strip('{}')#去花括号
    段=文字.split('-')#五段
    数据4=bytes.fromhex(段[3]+段[4])#后两段拼成 8 字节
    return GUID(int(段[0],16),int(段[1],16),int(段[2],16),(wintypes.BYTE*8)(*数据4))#构造

CLSID_FileOpenDialog=_guid('DC1C5A9C-E88A-4DDE-A5A1-60F82A20AEF7')#文件打开对话框类
IID_IFileOpenDialog=_guid('D57C7288-D4AD-4768-BE02-9D969532D960')#打开对话框接口

def 选Win32目录(信号):#打开现代 Win32 文件夹选择器
    """在调用线程打开 IFileOpenDialog。返回选定路径；用户取消为 None；已中止则抛错。"""
    if getattr(信号,'aborted',False) or getattr(信号,'已中止',False):#已经中止
        raise Exception('native directory picker aborted')#不开对话框
    ole32=ctypes.windll.ole32#OLE（仅 win32 导入路径到达此处）
    结果=ole32.CoInitializeEx(None,COINIT_APARTMENTTHREADED)#初始化 COM STA
    if 结果 not in (S_OK,S_FALSE):#初始化失败
        raise Exception('win32 folder dialog failed: CoInitializeEx '+hex(结果 & 0xffffffff))#COM 失败
    对话框=ctypes.c_void_p()#IFileOpenDialog*
    try:#创建并显示
        创建=ole32.CoCreateInstance(ctypes.byref(CLSID_FileOpenDialog),None,CLSCTX_INPROC_SERVER,ctypes.byref(IID_IFileOpenDialog),ctypes.byref(对话框))#创建实例
        if 创建!=S_OK:#创建失败
            raise Exception('win32 folder dialog failed: CoCreateInstance '+hex(创建 & 0xffffffff))#创建失败
        虚表=ctypes.cast(对话框,ctypes.POINTER(ctypes.c_void_p)).contents#第一个指针是 vtbl
        方法们=ctypes.cast(虚表,ctypes.POINTER(ctypes.c_void_p))#方法表
        SetTitle=ctypes.WINFUNCTYPE(ctypes.HRESULT,ctypes.c_void_p,wintypes.LPCWSTR)(方法们[17])#SetTitle 槽
        SetOptions=ctypes.WINFUNCTYPE(ctypes.HRESULT,ctypes.c_void_p,ctypes.c_uint)(方法们[9])#SetOptions
        GetOptions=ctypes.WINFUNCTYPE(ctypes.HRESULT,ctypes.c_void_p,ctypes.POINTER(ctypes.c_uint))(方法们[10])#GetOptions
        Show=ctypes.WINFUNCTYPE(ctypes.HRESULT,ctypes.c_void_p,wintypes.HWND)(方法们[3])#Show
        GetResult=ctypes.WINFUNCTYPE(ctypes.HRESULT,ctypes.c_void_p,ctypes.POINTER(ctypes.c_void_p))(方法们[20])#GetResult
        选项=ctypes.c_uint()#当前选项
        GetOptions(对话框,ctypes.byref(选项))#读选项
        SetOptions(对话框,选项.value|FOS_PICKFOLDERS|FOS_FORCEFILESYSTEM)#只选文件夹
        SetTitle(对话框,对话框标题)#标题
        if getattr(信号,'aborted',False) or getattr(信号,'已中止',False):#显示前中止
            raise Exception('native directory picker aborted')#拒绝
        显示=Show(对话框,None)#模态显示
        if getattr(信号,'aborted',False) or getattr(信号,'已中止',False):#显示后发现中止
            raise Exception('native directory picker aborted')#中止优先
        if 显示==ERROR_CANCELLED or (显示 & 0xffffffff)==0x800704C7:#用户取消 HRESULT
            return None#取消
        if 显示!=S_OK:#其它失败
            raise Exception('win32 folder dialog failed: Show '+hex(显示 & 0xffffffff))#显示失败
        项=ctypes.c_void_p()#IShellItem*
        取结果=GetResult(对话框,ctypes.byref(项))#取选中项
        if 取结果!=S_OK:#无结果
            return None#当取消
        try:#取文件系统路径
            项表=ctypes.cast(ctypes.cast(项,ctypes.POINTER(ctypes.c_void_p)).contents,ctypes.POINTER(ctypes.c_void_p))#项 vtbl
            GetDisplayName=ctypes.WINFUNCTYPE(ctypes.HRESULT,ctypes.c_void_p,ctypes.c_uint,ctypes.POINTER(wintypes.LPWSTR))(项表[5])#GetDisplayName
            项Release=ctypes.WINFUNCTYPE(ctypes.c_ulong,ctypes.c_void_p)(项表[2])#Release
            缓冲=wintypes.LPWSTR()#输出路径
            名结果=GetDisplayName(项,SIGDN_FILESYSPATH,ctypes.byref(缓冲))#文件系统路径
            if 名结果!=S_OK or not 缓冲:#取名失败
                return None#当取消
            路径=缓冲.value#Python 字符串
            ole32.CoTaskMemFree(缓冲)#释放 COM 串
            return 路径#选定路径
        finally:#释放 Shell 项
            项Release(项)#Release
    finally:#释放对话框并反初始化
        if 对话框:#有实例
            虚表=ctypes.cast(对话框,ctypes.POINTER(ctypes.c_void_p)).contents#vtbl
            方法们=ctypes.cast(虚表,ctypes.POINTER(ctypes.c_void_p))#方法
            ctypes.WINFUNCTYPE(ctypes.c_ulong,ctypes.c_void_p)(方法们[2])(对话框)#Release
        ole32.CoUninitialize()#反初始化
