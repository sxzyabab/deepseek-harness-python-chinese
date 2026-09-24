"""解析宿主账户文档目录，供首次使用工作区创建。"""
import os,sys,re
from pathlib import PurePosixPath,PureWindowsPath
from ...工具.原生命令 import 运行原生命令,已中止

__all__=['校验文档目录','默认工作区目录']

换行尾=re.compile(r'[\r\n]+\Z',re.ASCII)

class 文档目录错误(Exception):
    """文档目录解析失败。"""

def 若已中止则抛出(信号):
    """信号已置位则抛出。"""
    if 已中止(信号):
        raise 文档目录错误('Documents directory lookup was aborted')

def 校验文档目录(目录,平台=None):
    """校验已配置或系统返回的文档路径，不相对 cwd 解析。"""
    if 平台 is None:
        平台=sys.platform
    路径=PureWindowsPath if 平台=='win32' else PurePosixPath
    解析=路径(目录)
    根=str(解析.anchor)
    if not 解析.is_absolute() or (平台=='win32' and (根=='\\' or 根=='/')):
        raise 文档目录错误("Documents directory must be fully qualified: '"+目录+"'")
    return str(解析)

def 默认工作区目录(目录名,文档目录,信号,内部=None):
    """解析首次使用目录，不创建文件。内部可替换平台与命令运行器。"""
    if 内部 is None:
        内部={}
    平台=内部['platform'] if 'platform' in 内部 else sys.platform
    路径=PureWindowsPath if 平台=='win32' else PurePosixPath
    若已中止则抛出(信号)
    目录=文档目录
    if 目录 is None:
        运行=内部['run'] if 'run' in 内部 else 运行原生命令
        if 平台=='darwin':
            结果=运行('osascript',[
                '-e','POSIX path of (path to documents folder from user domain without folder creation)',
            ],信号)
        elif 平台=='win32':
            结果=运行('powershell.exe',[
                '-NoLogo','-NoProfile','-NonInteractive','-Command',
                '[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false); '
                +'[Environment]::GetFolderPath([Environment+SpecialFolder]::MyDocuments, '
                +'[Environment+SpecialFolderOption]::DoNotVerify)',
            ],信号)
        elif 平台=='linux':
            结果=运行('xdg-user-dir',['DOCUMENTS'],信号)
        else:
            raise 文档目录错误('system Documents directory is unavailable on '+平台)
        目录=换行尾.sub('',结果['stdout'])
        主目录=内部['home'] if 'home' in 内部 else os.path.expanduser('~')
        if 目录=='' or (平台=='linux' and 校验文档目录(目录,平台)==校验文档目录(主目录,平台)):
            raise 文档目录错误('system Documents directory is unavailable')
    目录=校验文档目录(目录,平台)
    若已中止则抛出(信号)
    return str(路径(目录)/'deepseek-harness'/目录名)
