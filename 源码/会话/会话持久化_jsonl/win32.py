"""JSONL 后端的 Windows 耐久命名空间辅助（ctypes 最小 MoveFileEx）。"""
import ctypes#Win32
import os#路径
import sys#平台
from ctypes import wintypes#Win32 类型

MOVEFILE_WRITE_THROUGH=0x00000008#写穿标志
ERROR_FILE_EXISTS=80#文件已存在
ERROR_ALREADY_EXISTS=183#已存在

def _映射errno(win32码):#Win32 码映射 errno 名
    """把常见 Win32 错误码映射成 errno 风格字符串。"""
    if win32码 in (2,3):#未找到
        return 'ENOENT'#ENOENT
    if win32码==5:#访问拒绝
        return 'EACCES'#EACCES
    if win32码==17:#非同设备
        return 'EXDEV'#EXDEV
    if win32码==32:#共享冲突
        return 'EBUSY'#EBUSY
    if win32码 in (ERROR_FILE_EXISTS,ERROR_ALREADY_EXISTS):#已存在
        return 'EEXIST'#EEXIST
    if win32码==123:#无效名
        return 'EINVAL'#EINVAL
    return 'EIO'#其余

def _扩展路径(路径):#\\?\ 扩展路径
    """为长路径准备 Win32 宽字符路径。"""
    绝对=os.path.abspath(路径)#绝对
    if 绝对.startswith('\\\\?\\'):#已扩展
        return 绝对#原样
    if 绝对.startswith('\\\\'):#UNC
        return '\\\\?\\UNC\\'+绝对[2:]#UNC 扩展
    return '\\\\?\\'+绝对#盘符扩展

def 发布新文件win32(已有,替换):#写穿发布新文件
    """以 MOVEFILE_WRITE_THROUGH 把已同步暂存发布到最终名；目标不得已存在。"""
    if sys.platform!='win32':#非 Windows
        raise OSError('publishNewFileWin32 is only available on win32')#拒绝
    内核=ctypes.WinDLL('kernel32',use_last_error=True)#kernel32
    移动=内核.MoveFileExW#MoveFileExW
    移动.argtypes=[wintypes.LPCWSTR,wintypes.LPCWSTR,wintypes.DWORD]#参数
    移动.restype=wintypes.BOOL#返回
    源=_扩展路径(已有)#源
    目标=_扩展路径(替换)#目标
    成功=移动(源,目标,MOVEFILE_WRITE_THROUGH)#写穿移动
    if 成功:#成功
        return#结束
    码=ctypes.get_last_error()#末次错误
    错误=OSError(f'MoveFileExW {_映射errno(码)} (Win32 {码}): {已有} -> {替换}')#构造
    错误.winerror=码#Win32 码
    错误.errno=码#挂 errno 槽
    错误.strerror=_映射errno(码)#映射名
    错误.filename=已有#源
    错误.filename2=替换#目标
    错误.code=_映射errno(码)#errno 风格码（供 isEEXIST）
    raise 错误#抛出

def 是否eexist(错误):#是否 EEXIST
    """文件系统冲突是否表示目标已存在。"""
    码=getattr(错误,'code',None)#自定义码
    if 码=='EEXIST':#已映射
        return True#是
    if getattr(错误,'winerror',None) in (ERROR_FILE_EXISTS,ERROR_ALREADY_EXISTS):#Win32
        return True#是
    if getattr(错误,'errno',None) in (getattr(os,'EEXIST',17),ERROR_FILE_EXISTS,ERROR_ALREADY_EXISTS):#errno
        return True#是
    return False#否

__all__=['发布新文件win32','是否eexist','MOVEFILE_WRITE_THROUGH']#公开面
