import os,platform,re
from pathlib import Path,PureWindowsPath
from . import 运行原生命令,已中止,原生命令错误

__all__=[
    '可打开原生路径','原生文件管理器','揭示原生路径','打开原生路径','打开原生文本文件',
]

浏览器文档={'.html','.htm','.xhtml','.svg'}

def 有值(值):
    """某环境标记是否设为非空值。"""
    return 值 is not None and 值!=''

def 是否WSL(内部=None):
    """用进程与内核标记区分 WSL 与桌面 Linux。"""
    if 内部 is None:
        内部={}
    环境=内部['env'] if 'env' in 内部 else os.environ
    if 有值(环境.get('WSL_DISTRO_NAME')) or 有值(环境.get('WSL_INTEROP')):
        return True
    发行=内部['osRelease'] if 'osRelease' in 内部 else platform.release()
    return 'microsoft' in 发行.lower()

def PowerShell字面量(路径):
    """PowerShell 单引号字面量（内嵌引号加倍）。"""
    return "'"+路径.replace("'","''")+"'"

def 确保未中止(信号):
    """信号已置位则抛 ABORT。"""
    if 已中止(信号):
        raise 原生命令错误('The operation was aborted','ABORT_ERR','','',None)#ABORT_ERR 字面量不翻译

def macHttps包(plist):
    """为 https 注册的 macOS 包。"""
    剥=re.sub(r'LSHandlerPreferredVersions\s*=\s*\{[^}]*\};','',plist)
    块匹配=re.search(r'\{[^{}]*LSHandlerURLScheme\s*=\s*"?https"?;[^{}]*\}',剥)
    if 块匹配 is None:
        return None
    包匹配=re.search(r'LSHandlerRoleAll\s*=\s*"?([\w.-]+)"?;',块匹配.group(0))
    return None if 包匹配 is None else 包匹配.group(1)

def 用浏览器打开(路径,信号,系统,运行,环境):
    """用默认浏览器打开一份浏览器可渲染文档。成功为真。"""
    if 系统=='darwin':
        try:
            结果=运行('defaults',['read','com.apple.LaunchServices/com.apple.launchservices.secure'],信号)
            包=macHttps包(结果['stdout'])
        except 原生命令错误:
            return False
        if 包 is None:
            return False
        运行('open',['-b',包,路径],信号)
        return True
    if 系统=='linux':
        浏览器=环境.get('BROWSER')
        if not 有值(浏览器):
            return False
        运行(浏览器,[路径],信号)
        return True
    return False

def 打开Windows路径(路径,信号,运行):
    """经已注册桌面应用打开一条 Windows 可解析路径。"""
    运行('powershell.exe',['-NoProfile','-Command','Invoke-Item -LiteralPath '+PowerShell字面量(路径)],信号)

def 打开WSL路径(路径,信号,运行):
    """交给 Windows 桌面前先翻译 WSL 路径。"""
    译=运行('wslpath',['-w',路径],信号)
    确保未中止(信号)
    windows路径=re.sub(r'[\r\n]+$','',译['stdout'])
    if windows路径=='':
        raise 原生命令错误('wslpath 没有返回 Windows 路径','EINVAL','','',None)
    打开Windows路径(windows路径,信号,运行)

def 按意图打开原生路径(路径,信号,意图,内部=None):
    """为请求的打开意图派发一次无 shell 平台命令。"""
    if 内部 is None:
        内部={}
    系统=内部['platform'] if 'platform' in 内部 else ('win32' if os.name=='nt' else platform.system().lower())
    if 系统=='windows':
        系统='win32'#Node 平台名
    if 系统=='macos':
        系统='darwin'#Node 平台名
    运行=内部['run'] if 'run' in 内部 else 运行原生命令
    环境=内部['env'] if 'env' in 内部 else os.environ
    为wsl=系统=='linux' and 是否WSL(内部)
    扩展=Path(路径).suffix.lower()
    if not 为wsl and 意图=='default' and 扩展 in 浏览器文档:
        if 用浏览器打开(路径,信号,系统,运行,环境):
            return
    if 系统=='darwin':
        运行('open',['-t',路径] if 意图=='text-editor' else [路径],信号)
        return
    if 系统=='win32':
        打开Windows路径(路径,信号,运行)
        return
    if 系统=='linux':
        if 为wsl:
            打开WSL路径(路径,信号,运行)
            return
        运行('xdg-open',[路径],信号)
        return
    raise 原生命令错误('本系统不支持原生路径打开器','ENOSYS','','',None)

def 可打开原生路径(内部=None):
    """本宿主上路径交给原生打开器是否大致能到达桌面。"""
    if 内部 is None:
        内部={}
    系统=内部['platform'] if 'platform' in 内部 else ('win32' if os.name=='nt' else platform.system().lower())
    if 系统 in ('windows','win32','darwin','macos'):
        return True
    if 系统!='linux':
        return False
    环境=内部['env'] if 'env' in 内部 else os.environ
    return 是否WSL(内部) or 有值(环境.get('DISPLAY')) or 有值(环境.get('WAYLAND_DISPLAY'))

def 原生文件管理器(内部=None):
    """识别原生文件管理器动作；不支持平台为 None。"""
    if 内部 is None:
        内部={}
    系统=内部['platform'] if 'platform' in 内部 else ('win32' if os.name=='nt' else platform.system().lower())
    if 系统 in ('darwin','macos'):
        return 'finder'
    if 系统 in ('win32','windows') or (系统=='linux' and 是否WSL(内部)):
        return 'explorer'
    return 'directory' if 系统=='linux' else None

def 揭示原生路径(路径,信号,内部=None):
    """在 Finder 或 Explorer 中揭示文件，或在 Linux 默认文件管理器中打开其父目录。"""
    if 内部 is None:
        内部={}
    确保未中止(信号)
    系统=内部['platform'] if 'platform' in 内部 else ('win32' if os.name=='nt' else platform.system().lower())
    if 系统=='windows':
        系统='win32'#Node 平台名
    if 系统=='macos':
        系统='darwin'#Node 平台名
    运行=内部['run'] if 'run' in 内部 else 运行原生命令
    管理器=原生文件管理器({**内部,'platform':系统})
    if 管理器=='finder':
        运行('open',['-R',路径],信号)
        return
    if 管理器=='explorer':
        windows路径=路径
        if 系统=='linux':
            译=运行('wslpath',['-w',路径],信号)
            确保未中止(信号)
            windows路径=re.sub(r'[\r\n]+$','',译['stdout'])
            if windows路径=='':
                raise 原生命令错误('wslpath 没有返回 Windows 路径','EINVAL','','',None)
        目标=PureWindowsPath(windows路径).as_uri().replace(',','%2C')#逗号必须写入 file URI
        try:
            运行('explorer.exe',['/select,',目标],信号)
        except 原生命令错误 as 错误:
            确保未中止(信号)#中止优先于退出码 1
            if 错误.code!=1:
                raise 错误
        return
    if 管理器=='directory':
        运行('xdg-open',[str(Path(路径).parent)],信号)
        return
    raise 原生命令错误('本系统不支持原生文件管理器','ENOSYS','','',None)

def 打开原生路径(路径,信号,内部=None):
    """用操作系统默认应用打开文件系统路径。"""
    按意图打开原生路径(路径,信号,'default',内部)

def 打开原生文本文件(路径,信号,内部=None):
    """打开文本文档以供编辑。"""
    按意图打开原生路径(路径,信号,'text-editor',内部)
