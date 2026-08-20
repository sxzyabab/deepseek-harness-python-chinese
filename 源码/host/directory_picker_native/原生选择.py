"""跨平台原生单目录选择器：macOS osascript、Linux zenity/kdialog、Windows IFileOpenDialog。

对齐上游 `native-picker.ts`。公开面仅中文名。Windows 侧用 ctypes 调同一套 COM API（上游在派生子进程里用 koffi；Python 可在调用线程直接 COM）。
"""
import os,re,sys#平台与文本
from native_command import 运行原生命令#无 shell 原生命令
from .win32对话框 import 选Win32目录#Windows COM 对话框

__all__=['选原生目录']#仅中文公开名

def 输出路径(标准输出):#从 stdout 取出路径
    """去掉尾部换行；空则视为取消。"""
    路径=re.sub(r'[\r\n]+$','',标准输出)#去尾换行
    return None if 路径=='' else 路径#空当取消

def 错误码(错误):#从未知失败取 code
    """取出 code 字段；无则 None。"""
    return getattr(错误,'code',None)#退出码或 errno 名

def 错误标准错误(错误):#从未知失败取 stderr
    """取出 stderr 文本。"""
    值=getattr(错误,'stderr',None)#可能缺席
    return 值 if isinstance(值,str) else ''#非字符串当空

def 是否缺命令(错误):#是否因命令不存在而失败
    """ENOENT 表示二进制不在 PATH。"""
    return 错误码(错误)=='ENOENT'#缺命令

def 若已中止则抛(信号,错误):#中止导致的失败原样抛出
    """中止则不要当成用户取消。"""
    if getattr(信号,'aborted',False) or getattr(信号,'已中止',False):#已中止
        raise 错误#原样抛出

def 选原生目录(信号,内部=None):#打开平台目录选择器
    """打开平台目录选择器。返回选定绝对路径；用户取消为 None。内部钩子供测试注入。"""
    if 内部 is None:#缺省空钩子
        内部={}#无覆盖
    平台=内部.get('platform') or sys.platform#有效平台
    运行=内部.get('run') or 运行原生命令#有效运行器
    if 平台=='darwin':#macOS：osascript
        try:#跑 AppleScript
            结果=运行('osascript',[#两行脚本
                '-e','set selectedFolder to choose folder with prompt "Select Workspace Directory"',#选文件夹
                '-e','POSIX path of selectedFolder',#POSIX 路径
            ],信号)#带中止
            return 输出路径(结果['stdout'])#路径或取消
        except BaseException as 错误:#失败
            if (not (getattr(信号,'aborted',False) or getattr(信号,'已中止',False))) and 错误码(错误)==1 and re.search(r'(?:User canceled|-128)',错误标准错误(错误),re.I):#用户取消
                return None#取消
            raise#其它失败
    if 平台=='win32':#Windows：IFileOpenDialog
        选对话框=内部.get('pickWin32Dialog') or 选Win32目录#可替换
        return 选对话框(信号)#打开对话框
    if 平台.startswith('linux'):#Linux：zenity 再 kdialog
        try:#zenity
            结果=运行('zenity',['--file-selection','--directory','--title=Select Workspace Directory'],信号)#仅目录
            return 输出路径(结果['stdout'])#路径或取消
        except BaseException as 错误:#zenity 失败
            若已中止则抛(信号,错误)#中止优先
            if 错误码(错误)==1:#取消
                return None#取消
            if not 是否缺命令(错误):#不是缺命令
                raise#原样抛出
        try:#kdialog 兜底
            结果=运行('kdialog',['--getexistingdirectory','.','--title','Select Workspace Directory'],信号)#已有目录
            return 输出路径(结果['stdout'])#路径或取消
        except BaseException as 错误:#kdialog 失败
            若已中止则抛(信号,错误)#中止优先
            if 错误码(错误)==1:#取消
                return None#取消
            if 是否缺命令(错误):#两个都缺
                raise Exception('no supported native directory picker found (install zenity or kdialog)')#无选择器
            raise#其它失败
    raise Exception('native directory picker is unsupported on '+平台)#其它平台
