'原生后端的跨平台单目录选择框'
import re,sys#取消文案与平台
from ...工具.原生命令 import 运行原生命令#宿主命令
from .对话框 import 选Win32目录,对话框标题#Windows 对话框

def 输出路径(标准输出):#去掉尾部换行
    '空输出是取消'
    路径=re.sub(r'[\r\n]+$','',标准输出)#去尾
    return None if 路径=='' else 路径#空则取消

def 错误码(错误):#退出码或 ENOENT
    '没有 code 则没有'
    码=getattr(错误,'code',None)#码
    if isinstance(码,(str,int)) and not isinstance(码,bool):#字符串或整数
        return 码#码
    return None#无

def 错误标准错误(错误):#捕获的 stderr
    '没有则空串'
    文本=getattr(错误,'stderr',None)#stderr
    return 文本 if isinstance(文本,str) else ''#文本

def 是缺命令(错误):#可执行不在 PATH
    'ENOENT'
    return 错误码(错误)=='ENOENT'#缺

def 中止则再抛(信号,错误):#中止优先于业务失败
    '信号已置位则把原错误抛回去'
    if 信号 is not None and 信号.is_set():#已中止
        raise 错误#原样

def 选原生目录(信号,内部=None):#按平台打开选择框
    '返回选中路径；取消返回 None'
    if 内部 is None:#无测试钩子
        内部={}#空
    平台=内部['platform'] if 'platform' in 内部 else sys.platform#平台
    运行=内部['run'] if 'run' in 内部 else 运行原生命令#命令运行器
    if 平台=='darwin':#macOS
        try:#osascript
            结果=运行('osascript',[#选择文件夹
                '-e','set selectedFolder to choose folder with prompt "'+对话框标题+'"',#提示
                '-e','POSIX path of selectedFolder',#POSIX 路径
            ],信号)#运行
            return 输出路径(结果['stdout'])#路径
        except Exception as 错误:#失败
            if (not (信号 is not None and 信号.is_set())) and 错误码(错误)==1 and re.search(r'(?:User canceled|-128)',错误标准错误(错误),re.I) is not None:#用户取消
                return None#取消
            raise#其它
    if 平台=='win32':#Windows
        选框=内部['pickWin32Dialog'] if 'pickWin32Dialog' in 内部 else 选Win32目录#对话框
        return 选框(信号)#子进程对话框
    if 平台=='linux':#Linux
        try:#zenity
            结果=运行('zenity',['--file-selection','--directory','--title='+对话框标题],信号)#运行
            return 输出路径(结果['stdout'])#路径
        except Exception as 错误:#失败
            中止则再抛(信号,错误)#中止
            if 错误码(错误)==1:#取消
                return None#取消
            if not 是缺命令(错误):#不是缺命令
                raise#其它
        try:#kdialog
            结果=运行('kdialog',['--getexistingdirectory','.','--title',对话框标题],信号)#运行
            return 输出路径(结果['stdout'])#路径
        except Exception as 错误:#失败
            中止则再抛(信号,错误)#中止
            if 错误码(错误)==1:#取消
                return None#取消
            if 是缺命令(错误):#两个都没有
                raise OSError('no supported native directory picker found (install zenity or kdialog)')#缺
            raise#其它
    raise OSError('native directory picker is unsupported on '+平台)#不支持

