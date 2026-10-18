'在应用中打开的应用目录：按平台声明、按顺序尝试的启动器来源'

__all__=[
    '路径令牌','苹果应用','规格','桌面规格','命令行','文件','应用路径','安装记录',
    'jetbrains产品','在应用中打开目录',
]

路径令牌='{path}'#启动参数里承载工作区目录的令牌

def 苹果应用(*文件系统名):
    '在 /Applications 和 ~/Applications 里查找这些 bundle'
    return {'locators':({'kind':'app','fsNames':文件系统名},)}#只有应用包定位

def 规格(*定位器):
    '由定位器链构成、不带桌面图标标识的平台规格'
    return {'locators':定位器}#按书写顺序尝试

def 桌面规格(桌面标识,*定位器):
    '定位器链，加上拥有图标的 Linux desktop 标识'
    return {'locators':定位器,'desktopId':桌面标识}#图标走 Icon=

def 命令行(名称,*参数):
    '进程内解析 PATH 名，再启动解析到的可执行文件'
    return {'kind':'cli','name':名称,'args':参数}#裸名，不是 shell 字符串

def 文件(候选列表,*参数):
    '取第一个存在的展开候选文件'
    return {'kind':'file','candidates':tuple(候选列表),'args':参数}#模板按书写顺序

def 应用路径(可执行名,*参数):
    '读 Windows App Paths 里这个已注册可执行名'
    return {'kind':'app-paths','exe':可执行名,'args':参数}#注册表键名

def 安装记录(显示名前缀,相对启动器=None,*参数):
    '读 Windows Uninstall 记录，并核验它指向的可执行文件'
    定位={'kind':'install-record','displayNamePrefix':显示名前缀,'args':参数}#前缀匹配 DisplayName
    if 相对启动器 is not None:#没写就改看 DisplayIcon
        定位['relativeLauncher']=相对启动器#InstallLocation 下的相对路径
    return 定位#定位器

def jetbrains产品(标识,产品名,命令行名,窗口可执行,苹果名列表):
    'JetBrains：macOS 用 bundle 名，Windows 用版本目录或卸载记录，Linux 用 PATH 或 Toolbox 脚本'
    return {
        'id':标识,#目录标识
        'platforms':{
            'darwin':苹果应用(*苹果名列表),#直接下载和 Toolbox 的拼写
            'win32':规格(
                {
                    'kind':'scan',
                    'root':'${ProgramFiles}/JetBrains',
                    'namePrefix':产品名,
                    'relativeLauncher':'bin/'+窗口可执行,
                    'args':(),
                },
                安装记录(产品名,'bin/'+窗口可执行),
            ),#先扫安装目录，再看卸载记录
            'linux':规格(
                命令行(命令行名),
                文件(('~/.local/share/JetBrains/Toolbox/scripts/'+命令行名,)),
            ),#PATH，然后 Toolbox 脚本
        },
    }

在应用中打开目录=(
    {#访达，随系统出货
        'id':'finder',
        'platforms':{
            'darwin':规格({
                'kind':'fixed',
                'launch':{'kind':'shell-open'},
                'iconPath':'/System/Library/CoreServices/Finder.app',
            }),
        },
    },
    {#资源管理器，随系统出货
        'id':'explorer',
        'platforms':{
            'win32':规格({
                'kind':'fixed',
                'launch':{'kind':'shell-open'},
                'iconPath':'${SystemRoot}/explorer.exe',
            }),
        },
    },
    {#Linux 默认打开器。只在有桌面会话时提供
        'id':'filemanager',
        'platforms':{
            'linux':规格({'kind':'cli','name':'xdg-open','args':(),'requiresDesktop':True}),
        },
    },
    {
        'id':'cursor',
        'platforms':{
            'darwin':苹果应用('Cursor.app'),
            'win32':规格(
                应用路径('Cursor.exe'),
                安装记录('Cursor'),
                文件(('${LOCALAPPDATA}/Programs/cursor/Cursor.exe',)),
            ),
            'linux':规格(命令行('cursor')),
        },
    },
    {
        'id':'vscode',
        'platforms':{
            'darwin':苹果应用('Visual Studio Code.app'),
            'win32':规格(
                应用路径('Code.exe'),
                安装记录('Microsoft Visual Studio Code','Code.exe'),
                文件((
                    '${LOCALAPPDATA}/Programs/Microsoft VS Code/Code.exe',
                    '${ProgramFiles}/Microsoft VS Code/Code.exe',
                )),
            ),
            'linux':桌面规格('code',命令行('code')),
        },
    },
    {
        'id':'vscodeinsiders',
        'platforms':{
            'darwin':苹果应用('Visual Studio Code - Insiders.app'),
            'win32':规格(
                应用路径('Code - Insiders.exe'),
                安装记录('Microsoft Visual Studio Code Insiders','Code - Insiders.exe'),
                文件(('${LOCALAPPDATA}/Programs/Microsoft VS Code Insiders/Code - Insiders.exe',)),
            ),
            'linux':桌面规格('code-insiders',命令行('code-insiders')),
        },
    },
    {
        'id':'windsurf',
        'platforms':{
            'darwin':苹果应用('Windsurf.app'),
            'win32':规格(
                应用路径('Windsurf.exe'),
                安装记录('Windsurf'),
                文件(('${LOCALAPPDATA}/Programs/Windsurf/Windsurf.exe',)),
            ),
            'linux':规格(命令行('windsurf')),
        },
    },
    {
        'id':'zed',
        'platforms':{
            'darwin':苹果应用('Zed.app','Zed Preview.app'),
            'linux':桌面规格(
                'dev.zed.Zed',
                命令行('zed'),
                {'kind':'desktop','desktopId':'dev.zed.Zed','args':()},
            ),
        },
    },
    {
        'id':'sublimetext',
        'platforms':{
            'darwin':苹果应用('Sublime Text.app'),
            'win32':规格(
                应用路径('sublime_text.exe'),
                安装记录('Sublime Text'),
                文件(('${ProgramFiles}/Sublime Text/sublime_text.exe',)),
            ),
            'linux':桌面规格('sublime_text',命令行('subl')),
        },
    },
    {'id':'xcode','platforms':{'darwin':规格({'kind':'xcode'})}},
    {
        'id':'androidstudio',
        'platforms':{
            'darwin':苹果应用('Android Studio.app'),
            'win32':规格(
                安装记录('Android Studio','bin/studio64.exe'),
                文件(('${ProgramFiles}/Android/Android Studio/bin/studio64.exe',)),
            ),
            'linux':规格(
                命令行('studio'),
                文件((
                    '~/.local/share/JetBrains/Toolbox/scripts/studio',
                    '/opt/android-studio/bin/studio.sh',
                )),
            ),
        },
    },
    jetbrains产品(
        'intellij','IntelliJ IDEA','idea','idea64.exe',
        ('IntelliJ IDEA.app','IntelliJ IDEA Ultimate.app','IntelliJ IDEA CE.app'),
    ),
    jetbrains产品(
        'pycharm','PyCharm','pycharm','pycharm64.exe',
        ('PyCharm.app','PyCharm Professional.app','PyCharm CE.app','PyCharm Community.app'),
    ),
    jetbrains产品('webstorm','WebStorm','webstorm','webstorm64.exe',('WebStorm.app',)),
    jetbrains产品('phpstorm','PhpStorm','phpstorm','phpstorm64.exe',('PhpStorm.app',)),
    jetbrains产品('goland','GoLand','goland','goland64.exe',('GoLand.app',)),
    jetbrains产品('rider','Rider','rider','rider64.exe',('Rider.app','JetBrains Rider.app')),
    jetbrains产品('rustrover','RustRover','rustrover','rustrover64.exe',('RustRover.app',)),
    {
        'id':'fork',
        'platforms':{
            'darwin':苹果应用('Fork.app'),
            'win32':规格(安装记录('Fork'),文件(('${LOCALAPPDATA}/Fork/Fork.exe',))),
        },
    },
    {'id':'sourcetree','platforms':{'darwin':苹果应用('Sourcetree.app')}},
    {
        'id':'github',
        'platforms':{
            'darwin':苹果应用('GitHub Desktop.app'),
            'win32':规格({'kind':'github-desktop','root':'${LOCALAPPDATA}/GitHubDesktop'}),
        },
    },
    {'id':'tower','platforms':{'darwin':苹果应用('Tower.app')}},
    {'id':'gitkraken','platforms':{'darwin':苹果应用('GitKraken.app')}},
    {'id':'smartgit','platforms':{'darwin':苹果应用('SmartGit.app')}},
    {
        'id':'sublimemerge',
        'platforms':{
            'darwin':苹果应用('Sublime Merge.app'),
            'win32':规格(
                应用路径('sublime_merge.exe'),
                安装记录('Sublime Merge'),
                文件(('${ProgramFiles}/Sublime Merge/sublime_merge.exe',)),
            ),
            'linux':桌面规格('sublime_merge',命令行('smerge')),
        },
    },
    {
        'id':'ghostty',
        'platforms':{
            'darwin':苹果应用('Ghostty.app'),
            'linux':桌面规格(
                'com.mitchellh.ghostty',
                命令行('ghostty','--working-directory='+路径令牌),
                {
                    'kind':'desktop',
                    'desktopId':'com.mitchellh.ghostty',
                    'args':('--working-directory='+路径令牌,),
                },
            ),
        },
    },
    {'id':'warp','platforms':{'darwin':苹果应用('Warp.app')}},
    {'id':'iterm','platforms':{'darwin':苹果应用('iTerm.app')}},
    {
        'id':'kitty',
        'platforms':{
            'darwin':苹果应用('kitty.app'),
            'linux':桌面规格(
                'kitty',
                命令行('kitty','--directory'),
                {'kind':'desktop','desktopId':'kitty','args':('--directory',)},
            ),
        },
    },
    {#终端，随 macOS 出货
        'id':'terminal',
        'platforms':{
            'darwin':规格({
                'kind':'fixed',
                'launch':{'kind':'argv','command':'open','args':('-a','Terminal')},
                'iconPath':'/System/Applications/Utilities/Terminal.app',
            }),
        },
    },
    {'id':'windowsterminal','platforms':{'win32':规格(命令行('wt','-d'))}},
    {
        'id':'gitbash',
        'platforms':{
            'win32':规格(
                #Git for Windows 登记成 Git version x.y.z。只用 Git 会误中 GitHub Desktop
                安装记录('Git version','git-bash.exe','--cd='+路径令牌),
                文件(('${ProgramFiles}/Git/git-bash.exe',),'--cd='+路径令牌),
            ),
        },
    },
    {
        'id':'gnometerminal',
        'platforms':{
            'linux':桌面规格(
                'org.gnome.Terminal',
                命令行('gnome-terminal','--working-directory='+路径令牌),
                {
                    'kind':'desktop',
                    'desktopId':'org.gnome.Terminal',
                    'args':('--working-directory='+路径令牌,),
                },
            ),
        },
    },
    {
        'id':'konsole',
        'platforms':{
            'linux':桌面规格(
                'org.kde.konsole',
                命令行('konsole','--workdir'),
                {'kind':'desktop','desktopId':'org.kde.konsole','args':('--workdir',)},
            ),
        },
    },
)
