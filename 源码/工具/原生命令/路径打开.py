"""宿主 UI 集成用的跨平台原生路径与文本文档打开器。默认意图优先用平台能点名的默认浏览器打开可渲染文档，再回退到默认应用。WSL 把路径翻译给 Windows 桌面。"""
import os,platform,re#平台判定
from pathlib import Path,PureWindowsPath#路径与Windows URI
from . import 运行原生命令,已中止,原生命令错误#运行器与中止

__all__=[#公开面
    '可打开原生路径','原生文件管理器','揭示原生路径','打开原生路径','打开原生文本文件',
]#公开面结束

浏览器文档={'.html','.htm','.xhtml','.svg'}#浏览器文档扩展名

def 有值(值):#非空存在
    """某环境标记是否设为非空值。"""
    return 值 is not None and 值!=''#有且非空

def 是否WSL(内部=None):#是否WSL
    """用进程与内核标记区分 WSL 与桌面 Linux。"""
    if 内部 is None:#缺省
        内部={}#空
    环境=内部['env'] if 'env' in 内部 else os.environ#环境
    if 有值(环境.get('WSL_DISTRO_NAME')) or 有值(环境.get('WSL_INTEROP')):#环境标记
        return True#是WSL
    发行=内部['osRelease'] if 'osRelease' in 内部 else platform.release()#发行版
    return 'microsoft' in 发行.lower()#内核含microsoft

def PowerShell字面量(路径):#PowerShell字面量
    """PowerShell 单引号字面量（内嵌引号加倍）。"""
    return "'"+路径.replace("'","''")+"'"#加倍单引号

def 确保未中止(信号):#中止则抛
    """信号已置位则抛 ABORT。"""
    if 已中止(信号):#已中止
        raise 原生命令错误('The operation was aborted','ABORT_ERR','','',None)#中止

def macHttps包(plist):#从plist取https处理包
    """为 https 注册的 macOS 包。"""
    剥=re.sub(r'LSHandlerPreferredVersions\s*=\s*\{[^}]*\};','',plist)#剥版本字典
    块匹配=re.search(r'\{[^{}]*LSHandlerURLScheme\s*=\s*"?https"?;[^{}]*\}',剥)#https块
    if 块匹配 is None:#无块
        return None#无
    包匹配=re.search(r'LSHandlerRoleAll\s*=\s*"?([\w.-]+)"?;',块匹配.group(0))#包id
    return None if 包匹配 is None else 包匹配.group(1)#包或无

def 用浏览器打开(路径,信号,系统,运行,环境):#用浏览器打开
    """用默认浏览器打开一份浏览器可渲染文档。成功为真。"""
    if 系统=='darwin':#macOS
        try:#读LaunchServices
            结果=运行('defaults',['read','com.apple.LaunchServices/com.apple.launchservices.secure'],信号)#读defaults
            包=macHttps包(结果['stdout'])#解析包
        except Exception:#无记录
            return False#回退
        if 包 is None:#无包
            return False#回退
        运行('open',['-b',包,路径],信号)#按包打开
        return True#成功
    if 系统=='linux':#Linux
        浏览器=环境.get('BROWSER')#浏览器命令
        if not 有值(浏览器):#未设
            return False#回退
        运行(浏览器,[路径],信号)#运行浏览器
        return True#成功
    return False#Windows回退关联

def 打开Windows路径(路径,信号,运行):#Windows打开
    """经已注册桌面应用打开一条 Windows 可解析路径。"""
    运行('powershell.exe',['-NoProfile','-Command','Invoke-Item -LiteralPath '+PowerShell字面量(路径)],信号)#字面路径打开

def 打开WSL路径(路径,信号,运行):#WSL打开
    """交给 Windows 桌面前先翻译 WSL 路径。"""
    译=运行('wslpath',['-w',路径],信号)#译为Windows路径
    确保未中止(信号)#检查取消
    windows路径=re.sub(r'[\r\n]+$','',译['stdout'])#去尾换行
    if windows路径=='':#空结果
        raise 原生命令错误('wslpath returned no Windows path','EINVAL','','',None)#空结果
    打开Windows路径(windows路径,信号,运行)#经Windows打开

def 按意图打开原生路径(路径,信号,意图,内部=None):#按意图打开
    """为请求的打开意图派发一次无 shell 平台命令。"""
    if 内部 is None:#缺省
        内部={}#空
    系统=内部['platform'] if 'platform' in 内部 else ('win32' if os.name=='nt' else platform.system().lower())#平台
    if 系统=='windows':#归一
        系统='win32'#Node名
    if 系统=='macos':#归一
        系统='darwin'#Node名
    运行=内部['run'] if 'run' in 内部 else 运行原生命令#运行器
    环境=内部['env'] if 'env' in 内部 else os.environ#环境
    为wsl=系统=='linux' and 是否WSL(内部)#是否WSL
    扩展=Path(路径).suffix.lower()#扩展名
    if not 为wsl and 意图=='default' and 扩展 in 浏览器文档:#默认且浏览器文档
        if 用浏览器打开(路径,信号,系统,运行,环境):#浏览器成功
            return#结束
    if 系统=='darwin':#macOS
        运行('open',['-t',路径] if 意图=='text-editor' else [路径],信号)#文本或默认
        return#结束
    if 系统=='win32':#Windows
        打开Windows路径(路径,信号,运行)#桌面打开
        return#结束
    if 系统=='linux':#Linux
        if 为wsl:#WSL
            打开WSL路径(路径,信号,运行)#经Windows
            return#结束
        运行('xdg-open',[路径],信号)#xdg打开
        return#结束
    raise 原生命令错误('native path opener is unsupported on '+系统,'ENOSYS','','',None)#不支持

def 可打开原生路径(内部=None):#是否可打开
    """本宿主上路径交给原生打开器是否大致能到达桌面。"""
    if 内部 is None:#缺省
        内部={}#空
    系统=内部['platform'] if 'platform' in 内部 else ('win32' if os.name=='nt' else platform.system().lower())#平台
    if 系统 in ('windows','win32','darwin','macos'):#桌面OS
        return True#可
    if 系统!='linux':#非Linux
        return False#否
    环境=内部['env'] if 'env' in 内部 else os.environ#环境
    return 是否WSL(内部) or 有值(环境.get('DISPLAY')) or 有值(环境.get('WAYLAND_DISPLAY'))#WSL或有显示

def 原生文件管理器(内部=None):#原生文件管理器
    """识别原生文件管理器动作；不支持平台为 None。"""
    if 内部 is None:#缺省
        内部={}#空
    系统=内部['platform'] if 'platform' in 内部 else ('win32' if os.name=='nt' else platform.system().lower())#平台
    if 系统 in ('darwin','macos'):#macOS
        return 'finder'#Finder
    if 系统 in ('win32','windows') or (系统=='linux' and 是否WSL(内部)):#Windows/WSL
        return 'explorer'#资源管理器
    return 'directory' if 系统=='linux' else None#Linux打开父目录或无

def 揭示原生路径(路径,信号,内部=None):#在文件管理器中揭示
    """在 Finder 或 Explorer 中揭示文件，或在 Linux 默认文件管理器中打开其父目录。"""
    if 内部 is None:#缺省
        内部={}#空
    确保未中止(信号)#已中止则抛
    系统=内部['platform'] if 'platform' in 内部 else ('win32' if os.name=='nt' else platform.system().lower())#平台
    if 系统=='windows':#归一
        系统='win32'#Node名
    if 系统=='macos':#归一
        系统='darwin'#Node名
    运行=内部['run'] if 'run' in 内部 else 运行原生命令#运行器
    管理器=原生文件管理器({**内部,'platform':系统})#管理器种类
    if 管理器=='finder':#macOS Finder
        运行('open',['-R',路径],信号)#Reveal
        return#结束
    if 管理器=='explorer':#Windows Explorer
        windows路径=路径#默认
        if 系统=='linux':#WSL需翻译
            译=运行('wslpath',['-w',路径],信号)#译路径
            确保未中止(信号)#中止检查
            windows路径=re.sub(r'[\r\n]+$','',译['stdout'])#去尾换行
            if windows路径=='':#空
                raise 原生命令错误('wslpath returned no Windows path','EINVAL','','',None)#空结果
        目标=PureWindowsPath(windows路径).as_uri().replace(',','%2C')#file URI并编码逗号
        try:#调用Explorer
            运行('explorer.exe',['/select,',目标],信号)#选中打开
        except 原生命令错误 as 错误:#可能退出1
            确保未中止(信号)#中止优先
            if 错误.code!=1:#非1则抛
                raise 错误#抛出
        return#结束
    if 管理器=='directory':#Linux打开父目录
        运行('xdg-open',[str(Path(路径).parent)],信号)#打开父目录
        return#结束
    raise 原生命令错误('native file manager is unsupported on '+系统,'ENOSYS','','',None)#不支持

def 打开原生路径(路径,信号,内部=None):#默认打开路径
    """用操作系统默认应用打开文件系统路径。"""
    按意图打开原生路径(路径,信号,'default',内部)#默认意图

def 打开原生文本文件(路径,信号,内部=None):#文本编辑打开
    """打开文本文档以供编辑。"""
    按意图打开原生路径(路径,信号,'text-editor',内部)#文本编辑意图
