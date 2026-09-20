"""在应用中打开的应用目录：编译期白名单表，按平台声明按序尝试的启动器来源。

解析在 解析器，图标在 图标。平台无声明时解析为空目录。定位器种类与应用标识字面量保持英文（目录数据/线协议）。
"""
from dataclasses import dataclass#不可变目录条目

__all__=[
    '路径令牌','参数启动','外壳打开启动','平台规格','应用条目','在应用中打开目录',
]

路径令牌='{path}'#启动参数中承载工作区目录的令牌

@dataclass(frozen=True)
class 参数启动:#argv 分离派生
    """以 argv 分离派生启动器；可选环境叠在擦洗父环境上。"""
    命令:str#可执行路径或 PATH 名
    参数列表:tuple#argv 其余段
    环境:dict|None=None#显式环境条目
    隐藏窗口:bool|None=None#Windows 上隐藏自身 CLI 进程
    种类:str='argv'#判别种类（英文字面量）

@dataclass(frozen=True)
class 外壳打开启动:#经 OS shell open verb
    """把目录交给操作系统 shell 的 open verb。"""
    种类:str='shell-open'#判别种类（英文字面量）

@dataclass(frozen=True)
class 固定定位:#随 OS 出货
    """随操作系统出货的固定启动。"""
    启动:object#参数启动或外壳打开启动
    图标路径:str#图标来源模板
    种类:str='fixed'#判别种类

@dataclass(frozen=True)
class 应用包定位:#macOS .app 目录
    """在已知应用目录中查找命名 bundle。"""
    文件系统名列表:tuple#bundle 文件名
    种类:str='app'#判别种类

@dataclass(frozen=True)
class Xcode定位:#跟随 xcode-select
    """经 xcode-select -p 解析 Xcode。"""
    种类:str='xcode'#判别种类

@dataclass(frozen=True)
class 命令行定位:#PATH 名
    """进程内解析 PATH 名后启动。"""
    名称:str#PATH 名
    参数列表:tuple#启动参数
    需要桌面:bool|None=None#无桌面会话则不提供
    种类:str='cli'#判别种类

@dataclass(frozen=True)
class 文件定位:#首个存在的候选
    """取第一个存在的展开候选文件。"""
    候选列表:tuple#路径模板
    参数列表:tuple#启动参数
    种类:str='file'#判别种类

@dataclass(frozen=True)
class 扫描定位:#版本化安装目录
    """在根下挑最新匹配前缀的版本目录。"""
    根:str#根路径模板
    名称前缀:str#版本目录名前缀
    相对启动器:str#版本目录内相对启动器
    参数列表:tuple#启动参数
    种类:str='scan'#判别种类

@dataclass(frozen=True)
class 应用路径定位:#Windows App Paths
    """读 Windows App Paths 注册表。"""
    可执行名:str#注册的 exe 名
    参数列表:tuple#启动参数
    种类:str='app-paths'#判别种类

@dataclass(frozen=True)
class 安装记录定位:#Windows Uninstall
    """读 Windows Uninstall 记录并核验可执行文件。"""
    显示名前缀:str#DisplayName 前缀
    参数列表:tuple#启动参数
    相对启动器:str|None=None#InstallLocation 下的相对路径
    种类:str='install-record'#判别种类

@dataclass(frozen=True)
class GitHub桌面定位:#GitHub Desktop 版本化布局
    """同时解析 GitHub Desktop 可执行文件与随包 cli.js。"""
    根:str#安装根模板
    种类:str='github-desktop'#判别种类

@dataclass(frozen=True)
class 桌面条目定位:#Linux XDG desktop
    """读 XDG desktop 条目并核验 TryExec/Exec。"""
    桌面标识:str#不含 .desktop 后缀
    参数列表:tuple#启动参数
    种类:str='desktop'#判别种类

@dataclass(frozen=True)
class 平台规格:#一平台的定位链
    """一平台的定位器链；Linux 可挂拥有图标的 desktop 标识。"""
    定位器列表:tuple#按序尝试
    桌面标识:str|None=None#Linux 图标所属 desktop id

@dataclass(frozen=True)
class 应用条目:#一条可启动应用
    """一条可启动应用及其平台规格。"""
    标识:str#目录 id（英文字面量，进线协议）
    平台表:dict#平台名 → 平台规格

def 苹果应用(*文件系统名):#macOS 已知目录查 bundle
    """在 /Applications 与 ~/Applications 中查找命名 bundle。"""
    return 平台规格(定位器列表=(应用包定位(文件系统名列表=文件系统名),))#仅 app 定位

def 规格(*定位器):#无图标 desktop 的规格
    """由定位器链构成的平台规格。"""
    return 平台规格(定位器列表=定位器)#无 desktopId

def 桌面规格(桌面标识,*定位器):#带 Linux 图标归属
    """定位器链加上拥有图标的 desktop 标识。"""
    return 平台规格(定位器列表=定位器,桌面标识=桌面标识)#带 desktopId

def 命令行(名称,*参数):#PATH 定位
    """进程内 PATH 名定位。"""
    return 命令行定位(名称=名称,参数列表=参数)#普通 CLI

def 桌面命令行(名称,*参数):#需桌面会话的 PATH 定位
    """仅在有桌面会话时有意义的 PATH 定位。"""
    return 命令行定位(名称=名称,参数列表=参数,需要桌面=True)#requiresDesktop

def 文件(候选列表,*参数):#首个存在文件
    """首个存在文件定位。"""
    return 文件定位(候选列表=tuple(候选列表),参数列表=参数)#file

def 应用路径(可执行名,*参数):#App Paths
    """Windows App Paths 定位。"""
    return 应用路径定位(可执行名=可执行名,参数列表=参数)#app-paths

def 安装记录(显示名前缀,相对启动器=None,*参数):#Uninstall 记录
    """Windows Uninstall 记录定位。"""
    return 安装记录定位(显示名前缀=显示名前缀,相对启动器=相对启动器,参数列表=参数)#install-record

def jetbrains产品(标识,产品名,命令行名,窗口可执行,苹果名列表):#JetBrains 产品条目
    """JetBrains 产品：macOS bundle、Windows 扫描/卸载记录、Linux PATH/Toolbox 脚本。"""
    return 应用条目(标识=标识,平台表={#三平台
        'darwin':苹果应用(*苹果名列表),#macOS bundles
        'win32':规格(#Windows
            扫描定位(根='${ProgramFiles}/JetBrains',名称前缀=产品名,相对启动器='bin/'+窗口可执行,参数列表=()),#版本扫描
            安装记录(产品名,'bin/'+窗口可执行),#卸载记录
        ),#win32 结束
        'linux':规格(命令行(命令行名),文件(['~/.local/share/JetBrains/Toolbox/scripts/'+命令行名])),#Linux
    })#平台表结束

在应用中打开目录=(#菜单顺序的启动目录
    应用条目(标识='finder',平台表={#macOS Finder
        'darwin':规格(固定定位(启动=外壳打开启动(),图标路径='/System/Library/CoreServices/Finder.app')),#固定
    }),#finder
    应用条目(标识='explorer',平台表={#Windows 资源管理器
        'win32':规格(固定定位(启动=外壳打开启动(),图标路径='${SystemRoot}/explorer.exe')),#固定
    }),#explorer
    应用条目(标识='filemanager',平台表={'linux':规格(桌面命令行('xdg-open'))}),#Linux 文件管理器
    应用条目(标识='cursor',平台表={#Cursor
        'darwin':苹果应用('Cursor.app'),#macOS
        'win32':规格(#Windows
            应用路径('Cursor.exe'),#App Paths
            安装记录('Cursor'),#卸载记录
            文件(['${LOCALAPPDATA}/Programs/cursor/Cursor.exe']),#已知路径
        ),#win32
        'linux':规格(命令行('cursor')),#Linux
    }),#cursor
    应用条目(标识='vscode',平台表={#VS Code
        'darwin':苹果应用('Visual Studio Code.app'),#macOS
        'win32':规格(#Windows
            应用路径('Code.exe'),#App Paths
            安装记录('Microsoft Visual Studio Code','Code.exe'),#卸载记录
            文件([#已知路径
                '${LOCALAPPDATA}/Programs/Microsoft VS Code/Code.exe',
                '${ProgramFiles}/Microsoft VS Code/Code.exe',
            ]),#file
        ),#win32
        'linux':桌面规格('code',命令行('code')),#Linux
    }),#vscode
    应用条目(标识='vscodeinsiders',平台表={#VS Code Insiders
        'darwin':苹果应用('Visual Studio Code - Insiders.app'),#macOS
        'win32':规格(#Windows
            应用路径('Code - Insiders.exe'),#App Paths
            安装记录('Microsoft Visual Studio Code Insiders','Code - Insiders.exe'),#卸载记录
            文件(['${LOCALAPPDATA}/Programs/Microsoft VS Code Insiders/Code - Insiders.exe']),#已知路径
        ),#win32
        'linux':桌面规格('code-insiders',命令行('code-insiders')),#Linux
    }),#vscodeinsiders
    应用条目(标识='windsurf',平台表={#Windsurf
        'darwin':苹果应用('Windsurf.app'),#macOS
        'win32':规格(#Windows
            应用路径('Windsurf.exe'),#App Paths
            安装记录('Windsurf'),#卸载记录
            文件(['${LOCALAPPDATA}/Programs/Windsurf/Windsurf.exe']),#已知路径
        ),#win32
        'linux':规格(命令行('windsurf')),#Linux
    }),#windsurf
    应用条目(标识='zed',平台表={#Zed
        'darwin':苹果应用('Zed.app','Zed Preview.app'),#macOS
        'linux':桌面规格('dev.zed.Zed',命令行('zed'),桌面条目定位(桌面标识='dev.zed.Zed',参数列表=())),#Linux
    }),#zed
    应用条目(标识='sublimetext',平台表={#Sublime Text
        'darwin':苹果应用('Sublime Text.app'),#macOS
        'win32':规格(#Windows
            应用路径('sublime_text.exe'),#App Paths
            安装记录('Sublime Text'),#卸载记录
            文件(['${ProgramFiles}/Sublime Text/sublime_text.exe']),#已知路径
        ),#win32
        'linux':桌面规格('sublime_text',命令行('subl')),#Linux
    }),#sublimetext
    应用条目(标识='xcode',平台表={'darwin':规格(Xcode定位())}),#Xcode
    应用条目(标识='androidstudio',平台表={#Android Studio
        'darwin':苹果应用('Android Studio.app'),#macOS
        'win32':规格(#Windows
            安装记录('Android Studio','bin/studio64.exe'),#卸载记录
            文件(['${ProgramFiles}/Android/Android Studio/bin/studio64.exe']),#已知路径
        ),#win32
        'linux':规格(命令行('studio'),文件([#Linux
            '~/.local/share/JetBrains/Toolbox/scripts/studio',
            '/opt/android-studio/bin/studio.sh',
        ])),#linux
    }),#androidstudio
    jetbrains产品('intellij','IntelliJ IDEA','idea','idea64.exe',#IntelliJ
        ('IntelliJ IDEA.app','IntelliJ IDEA Ultimate.app','IntelliJ IDEA CE.app')),#mac 名
    jetbrains产品('pycharm','PyCharm','pycharm','pycharm64.exe',#PyCharm
        ('PyCharm.app','PyCharm Professional.app','PyCharm CE.app','PyCharm Community.app')),#mac 名
    jetbrains产品('webstorm','WebStorm','webstorm','webstorm64.exe',('WebStorm.app',)),#WebStorm
    jetbrains产品('phpstorm','PhpStorm','phpstorm','phpstorm64.exe',('PhpStorm.app',)),#PhpStorm
    jetbrains产品('goland','GoLand','goland','goland64.exe',('GoLand.app',)),#GoLand
    jetbrains产品('rider','Rider','rider','rider64.exe',('Rider.app','JetBrains Rider.app')),#Rider
    jetbrains产品('rustrover','RustRover','rustrover','rustrover64.exe',('RustRover.app',)),#RustRover
    应用条目(标识='fork',平台表={#Fork
        'darwin':苹果应用('Fork.app'),#macOS
        'win32':规格(安装记录('Fork'),文件(['${LOCALAPPDATA}/Fork/Fork.exe'])),#Windows
    }),#fork
    应用条目(标识='sourcetree',平台表={'darwin':苹果应用('Sourcetree.app')}),#Sourcetree
    应用条目(标识='github',平台表={#GitHub Desktop
        'darwin':苹果应用('GitHub Desktop.app'),#macOS
        'win32':规格(GitHub桌面定位(根='${LOCALAPPDATA}/GitHubDesktop')),#Windows
    }),#github
    应用条目(标识='tower',平台表={'darwin':苹果应用('Tower.app')}),#Tower
    应用条目(标识='gitkraken',平台表={'darwin':苹果应用('GitKraken.app')}),#GitKraken
    应用条目(标识='smartgit',平台表={'darwin':苹果应用('SmartGit.app')}),#SmartGit
    应用条目(标识='sublimemerge',平台表={#Sublime Merge
        'darwin':苹果应用('Sublime Merge.app'),#macOS
        'win32':规格(#Windows
            应用路径('sublime_merge.exe'),#App Paths
            安装记录('Sublime Merge'),#卸载记录
            文件(['${ProgramFiles}/Sublime Merge/sublime_merge.exe']),#已知路径
        ),#win32
        'linux':桌面规格('sublime_merge',命令行('smerge')),#Linux
    }),#sublimemerge
    应用条目(标识='ghostty',平台表={#Ghostty
        'darwin':苹果应用('Ghostty.app'),#macOS
        'linux':桌面规格(#Linux
            'com.mitchellh.ghostty',#desktop id
            命令行('ghostty','--working-directory='+路径令牌),#CLI
            桌面条目定位(桌面标识='com.mitchellh.ghostty',参数列表=('--working-directory='+路径令牌,)),#desktop
        ),#linux
    }),#ghostty
    应用条目(标识='warp',平台表={'darwin':苹果应用('Warp.app')}),#Warp
    应用条目(标识='iterm',平台表={'darwin':苹果应用('iTerm.app')}),#iTerm
    应用条目(标识='kitty',平台表={#kitty
        'darwin':苹果应用('kitty.app'),#macOS
        'linux':桌面规格(#Linux
            'kitty',#desktop id
            命令行('kitty','--directory'),#CLI
            桌面条目定位(桌面标识='kitty',参数列表=('--directory',)),#desktop
        ),#linux
    }),#kitty
    应用条目(标识='terminal',平台表={#macOS Terminal
        'darwin':规格(固定定位(#固定
            启动=参数启动(命令='open',参数列表=('-a','Terminal')),#open -a Terminal
            图标路径='/System/Applications/Utilities/Terminal.app',#图标
        )),#固定定位
    }),#terminal
    应用条目(标识='windowsterminal',平台表={'win32':规格(命令行('wt','-d'))}),#Windows Terminal
    应用条目(标识='gitbash',平台表={#Git Bash
        'win32':规格(#Windows
            安装记录('Git version','git-bash.exe','--cd='+路径令牌),#避免匹配 GitHub Desktop
            文件(['${ProgramFiles}/Git/git-bash.exe'],'--cd='+路径令牌),#已知路径
        ),#win32
    }),#gitbash
    应用条目(标识='gnometerminal',平台表={#GNOME Terminal
        'linux':桌面规格(#Linux
            'org.gnome.Terminal',#desktop id
            命令行('gnome-terminal','--working-directory='+路径令牌),#CLI
            桌面条目定位(桌面标识='org.gnome.Terminal',参数列表=('--working-directory='+路径令牌,)),#desktop
        ),#linux
    }),#gnometerminal
    应用条目(标识='konsole',平台表={#Konsole
        'linux':桌面规格(#Linux
            'org.kde.konsole',#desktop id
            命令行('konsole','--workdir'),#CLI
            桌面条目定位(桌面标识='org.kde.konsole',参数列表=('--workdir',)),#desktop
        ),#linux
    }),#konsole
)#目录结束
