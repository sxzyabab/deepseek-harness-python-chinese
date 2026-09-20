"""平台解析：把目录条目解析为本机已验证的启动器，并按看护窗口分离启动。

中止用 threading.Event；异步一律同步。PATH 名经依赖的 subprocess 能力解析；其余宿主命令经原生命令（argv，不经 shell）。
"""
import errno,os,re,subprocess,sys,threading#错误码、路径、正则、派生、平台与看护
from dataclasses import dataclass#已解析启动与注册表视图
from pathlib import Path#家目录
from ...工具.原生命令 import 运行原生命令,原生命令错误#无 shell 宿主命令
from ...子进程.子进程 import 擦洗父环境#凭证擦洗环境
from .目录 import 在应用中打开目录,路径令牌,参数启动#目录数据与 argv 启动

__all__=[
    '在应用中打开错误','图标来源','已解析启动','已完成内部事实',
    '分离启动应用','补全内部事实','取命令输出','是否目录','是否普通文件',
    '展开候选','解析注册表转储','读Windows注册表视图','桌面条目',
    'xdg数据目录列表','查找桌面条目','执行命令首段','平台规格于',
    '解析启动','解析在应用中打开应用','启动已解析',
]#公开面结束

变量模式=re.compile(r'\$\{([^}]+)\}')#${VAR} 展开
百分变量模式=re.compile(r'%([^%]+)%')#%VAR% 展开
注册表值模式=re.compile(r'^\s+(.*?)\s+(REG_SZ|REG_EXPAND_SZ)\s+(.*)\Z',re.ASCII)#reg.exe 值行
键路径模式=re.compile(r'^HK',re.ASCII)#注册表键路径行
默认值名模式=re.compile(r'^\(.*\)\Z',re.ASCII)#本地化默认值名
执行首段引号模式=re.compile(r'^"([^"]+)"',re.ASCII)#Exec 引号段
执行首段裸名模式=re.compile(r'^\S+',re.ASCII)#Exec 裸段
自然分段模式=re.compile(r'([0-9]+)',re.ASCII)#版本自然序分段
图标后缀模式=re.compile(r',-?[0-9]+\Z',re.ASCII)#DisplayIcon 索引后缀

应用路径根列表=(#App Paths：用户巢优先
    r'HKCU\Software\Microsoft\Windows\CurrentVersion\App Paths',
    r'HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths',
)#App Paths 根
卸载根列表=(#Uninstall：用户、64 位机、32 位机视图
    r'HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall',
    r'HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall',
    r'HKLM\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall',
)#卸载根

class 在应用中打开错误(Exception):#本包异常基类
    """在应用中打开主机半边失败。"""

@dataclass(frozen=True)
class 图标来源:#已解析图标像素来源
    """本机持有的图标像素来源。"""
    种类:str#app-bundle 或 executable
    路径:str#bundle 目录或可执行路径

@dataclass
class 已解析启动:#一条已验证启动
    """一条条目在本机的已验证启动器与图标来源。"""
    启动:object#参数启动或外壳打开启动
    回退启动:object|None=None#可选回退
    图标:图标来源|None=None#可选图标来源

@dataclass(frozen=True)
class 已完成内部事实:#补全后的可覆盖事实
    """公开入口处一次性补全后的平台事实。"""
    平台:str#darwin/win32/linux/…
    ssh:bool#SSH 拉起
    应用根列表:tuple#macOS 应用目录根
    环境:dict#环境表
    家目录:str#家目录
    运行:object#原生命令运行器
    启动:object#分离启动器
    解析可执行:object#PATH 解析回调

@dataclass(frozen=True)
class Windows安装记录:#Uninstall 相关字段
    """一条 Windows Uninstall 记录中与启动器推导相关的字段。"""
    显示名:str#DisplayName
    安装位置:str|None=None#InstallLocation
    显示图标:str|None=None#DisplayIcon

@dataclass(frozen=True)
class Windows注册表视图:#一批解析共享的注册表事实
    """一次解析趟共享的 App Paths 与 Uninstall 视图。"""
    应用路径表:dict#小写 exe → 目标路径
    安装记录列表:tuple#Uninstall 记录

@dataclass(frozen=True)
class 桌面条目:#XDG desktop 字段
    """解析出的 Desktop Entry 字段。"""
    执行:str|None=None#Exec
    尝试执行:str|None=None#TryExec
    图标:str|None=None#Icon

def 节点平台():
    """把 sys.platform 粗映射到 Node 平台名。"""
    名=sys.platform#本机
    if 名=='win32':#Windows
        return 'win32'#Node 名
    if 名=='darwin':#macOS
        return 'darwin'#Node 名
    if 名.startswith('linux'):#Linux
        return 'linux'#Node 名
    return 名#原样

def 限时信号(毫秒):
    """在期限到时置位的中止事件。"""
    信号=threading.Event()#中止事件
    if isinstance(毫秒,(int,float)) and 毫秒>0:#有期限
        定时=threading.Timer(毫秒/1000.0,信号.set)#到期置位
        定时.daemon=True#不挡退出
        定时.start()#开始计时
    return 信号#返回信号

def 环境有值(值):#非空环境标记
    """环境标记是否为非空字符串。"""
    return 值 is not None and 值!=''#非空

def 是否WSL(平台,环境,内核发行=None):#区分 WSL 与桌面 Linux
    """用进程与内核标记区分 WSL。"""
    if 平台!='linux':#非 Linux
        return False#不是
    if 环境有值(环境.get('WSL_DISTRO_NAME') if isinstance(环境,dict) else None):#发行版名
        return True
    if 环境有值(环境.get('WSL_INTEROP') if isinstance(环境,dict) else None):#互通
        return True
    发行=内核发行 if 内核发行 is not None else (os.uname().release if hasattr(os,'uname') else '')#内核
    return 'microsoft' in str(发行).lower()#微软内核

def 能否打开原生路径(内部=None):#桌面 open verb 是否可达
    """本机是否可能把路径交给原生打开器。"""
    内部={} if 内部 is None else 内部#默认空
    平台=内部['平台'] if '平台' in 内部 else 节点平台()#平台
    if 平台=='darwin' or 平台=='win32':#桌面 OS
        return True#可达
    if 平台!='linux':#其它
        return False#不可达
    环境=内部['环境'] if '环境' in 内部 else dict(os.environ)#环境
    return 是否WSL(平台,环境) or 环境有值(环境.get('DISPLAY')) or 环境有值(环境.get('WAYLAND_DISPLAY'))#显示或 WSL

def powershell单引字面量(路径):#PowerShell 单引号字面量
    """把路径编成 PowerShell 单引号字面量。"""
    return "'"+路径.replace("'","''")+"'"#加倍内嵌引号

def 打开Windows路径(路径,信号,运行):#Invoke-Item
    """经注册的桌面应用打开 Windows 可解析路径。"""
    运行('powershell.exe',[#无配置文件
        '-NoProfile','-Command',
        'Invoke-Item -LiteralPath '+powershell单引字面量(路径),
    ],信号)#运行

def 打开原生路径(路径,信号,内部=None):#OS shell open verb
    """用操作系统默认应用打开文件系统路径（目录走 shell open）。"""
    内部={} if 内部 is None else 内部#默认空
    平台=内部['平台'] if '平台' in 内部 else 节点平台()#平台
    运行=内部['运行'] if '运行' in 内部 else 运行原生命令#运行器
    环境=内部['环境'] if '环境' in 内部 else dict(os.environ)#环境
    if 平台=='darwin':#macOS
        运行('open',[路径],信号)#open
        return#完成
    if 平台=='win32':#Windows
        打开Windows路径(路径,信号,运行)#Invoke-Item
        return#完成
    if 平台=='linux':#Linux
        if 是否WSL(平台,环境):#WSL → Windows 桌面
            结果=运行('wslpath',['-w',路径],信号)#翻译
            if 信号.is_set():#已中止
                raise 在应用中打开错误('The operation was aborted')#中止
            窗口路径=结果['stdout'].replace('\r','').replace('\n','')#去换行
            if 窗口路径=='':#空
                raise 在应用中打开错误('wslpath returned no Windows path')#失败
            打开Windows路径(窗口路径,信号,运行)#打开
            return#完成
        运行('xdg-open',[路径],信号)#桌面 Linux
        return#完成
    raise 在应用中打开错误('native path opener is unsupported on '+平台)#不支持

def 分离启动应用(命令,参数列表,选项):#detached GUI 启动
    """分离派生一条 GUI 启动：擦洗环境、无 stdio 管道，看护窗口内早失败则拒绝。"""
    完成=threading.Event()#是否已结算
    结果={'错误':None}#结算槽
    环境=dict(擦洗父环境())#擦洗基线
    if '环境' in 选项 and 选项['环境'] is not None:#显式环境
        环境.update(选项['环境'])#叠加
    关键字={#Popen 选项
        'stdin':subprocess.DEVNULL,#无管道
        'stdout':subprocess.DEVNULL,#无管道
        'stderr':subprocess.DEVNULL,#无管道
        'env':环境,#环境
        'close_fds':True,#关闭多余 fd
    }#结束选项
    if os.name=='nt':#Windows
        标志=subprocess.DETACHED_PROCESS|subprocess.CREATE_NEW_PROCESS_GROUP#分离
        if '隐藏窗口' in 选项 and 选项['隐藏窗口'] is True:#隐藏 CLI
            标志|=subprocess.CREATE_NO_WINDOW#无控制台
        关键字['creationflags']=标志#创建标志
    else:#POSIX
        关键字['start_new_session']=True#新会话
    try:#拉起
        进程=subprocess.Popen([命令]+list(参数列表),**关键字)#派生
    except OSError as 错误:#启动失败
        if 错误.errno==errno.ENOENT:#缺失
            错误.code='ENOENT'
        raise#原样抛出

    def 结算(错误=None):#只结算一次
        """看护结束：unref 式放行，不杀子进程。"""
        if 完成.is_set():#已结算
            return#忽略
        完成.set()#标记
        结果['错误']=错误#记下
        try:#放开等待
            进程.poll()#刷新
        except OSError:#忽略
            pass#放行

    def 看护退出():#等早退出或看护到期
        """子进程早退或看护窗口关闭。"""
        看护毫秒=选项['看护毫秒'] if '看护毫秒' in 选项 else 0#窗口
        截止=看护毫秒/1000.0 if 看护毫秒 else 0#秒
        try:#等待
            码=进程.wait(timeout=截止 if 截止>0 else None)#等退出或超时
            if 码==0:#干净退出
                结算()#成功
            else:#非零
                结算(在应用中打开错误('launcher exited with code '+str(码)+', signal None'))#失败
        except subprocess.TimeoutExpired:#仍在跑 → 计为已启动
            结算()#成功放行
        except OSError as 错误:#等待失败
            结算(错误)#失败

    线程=threading.Thread(target=看护退出,daemon=True)#看护线程
    线程.start()#开始
    完成.wait()#阻塞到结算
    if 结果['错误'] is not None:#失败
        raise 结果['错误']#抛出

def 补全内部事实(内部):#resolveInternals
    """相对运行宿主补全可覆盖事实；缺解析可执行则大声失败。"""
    内部={} if 内部 is None else 内部#默认空
    家目录=内部['家目录'] if '家目录' in 内部 else str(Path.home())#家目录
    if '解析可执行' not in 内部 or 内部['解析可执行'] is None:#必需
        raise 在应用中打开错误('open-in-app: internals.resolveExecutable is required (the subprocess capability provides it)')#大声失败
    return 已完成内部事实(#补全
        平台=内部['平台'] if '平台' in 内部 else 节点平台(),#平台
        ssh=bool(内部['ssh']) if 'ssh' in 内部 else False,#SSH 拉起
        应用根列表=tuple(内部['应用根列表']) if '应用根列表' in 内部 else ('/Applications',os.path.join(家目录,'Applications')),#根
        环境=dict(内部['环境']) if '环境' in 内部 else dict(os.environ),#环境
        家目录=家目录,#家
        运行=内部['运行'] if '运行' in 内部 else 运行原生命令,#运行器
        启动=内部['启动'] if '启动' in 内部 else 分离启动应用,#启动器
        解析可执行=内部['解析可执行'],#PATH
    )#结束

def 断言穷尽(值):#closed union
    """定位器/启动种类穷尽围栏。"""
    raise 在应用中打开错误('unhandled open-in-app catalog kind: '+repr(值))#未处理

def 取命令输出(命令,参数列表,超时毫秒,事实):#bounded host command
    """跑一条有界宿主命令；成功回 stdout，任何失败回 None。"""
    try:#执行
        结果=事实.运行(命令,list(参数列表),限时信号(超时毫秒))#同步跑
        return 结果['stdout']#标准输出
    except (原生命令错误,OSError,在应用中打开错误):#失败同义：不可用
        return None#不可用

def 是否目录(路径):#目录探针
    """路径存在且为目录。"""
    try:#探测
        return os.path.isdir(路径)#目录
    except OSError:#不可读
        return False#不是

def 是否普通文件(路径):#文件探针
    """路径存在且为普通文件。"""
    try:#探测
        return os.path.isfile(路径)#文件
    except OSError:#不可读
        return False#不是

def 展开候选(模板,事实):#${VAR} 与 ~/
    """展开候选模板；变量未设置则 None。"""
    未设=[]#未设置名
    def 换(匹配):#替换一处
        """替换 ${VAR}。"""
        名=匹配.group(1)#变量名
        if 名 not in 事实.环境 or 事实.环境[名] is None:#缺席
            未设.append(名)#记下
            return 匹配.group(0)#保留原样
        return 事实.环境[名]#展开
    已展=变量模式.sub(换,模板)#全替
    if len(未设)>0:#有未设
        return None#失败
    if 已展.startswith('~/'):#家目录前缀
        return os.path.join(事实.家目录,已展[2:])#拼接
    return 已展#原样

def 展开注册表值(值,事实):#%VAR%
    """展开注册表值中的 %VAR%；未设则 None。"""
    未设=[]#未设置
    def 换(匹配):#替换
        """替换 %VAR%。"""
        名=匹配.group(1)#名
        if 名 not in 事实.环境 or 事实.环境[名] is None:#缺席
            未设.append(名)#记下
            return 匹配.group(0)#保留
        return 事实.环境[名]#展开
    已展=百分变量模式.sub(换,值)#全替
    return None if len(未设)>0 else 已展#结果

def 解析注册表转储(转储):#reg.exe /s
    """把 reg.exe query /s 输出解析成子键 → 值名 → 数据。"""
    键表={}#路径 → 值表
    当前=None#当前值表
    for 行 in 转储.splitlines():#逐行
        if 键路径模式.match(行):#键路径
            当前={}#新表
            键表[行.strip()]=当前#登记
            continue#下一行
        匹配=注册表值模式.match(行)#值行
        if 匹配 is None or 当前 is None:#无关
            continue#跳过
        名,数据=匹配.group(1),匹配.group(3)#名与数据
        当前['(Default)' if 默认值名模式.match(名) else 名]=数据.strip()#默认名归一
    return 键表#视图

def 读Windows注册表视图(超时毫秒,事实):#一批注册表
    """一次解析趟：App Paths 与 Uninstall，每根至多一条 reg.exe。"""
    应用路径表={}#exe → 路径
    安装记录列表=[]#记录
    for 根 in 应用路径根列表:#App Paths
        转储=取命令输出('reg.exe',['query',根,'/s'],超时毫秒,事实)#查询
        if 转储 is None:#失败
            continue#下一根
        for 键,值表 in 解析注册表转储(转储).items():#子键
            可执行=键[键.rfind('\\')+1:].lower()#末段小写
            目标=值表['(Default)'] if '(Default)' in 值表 else None#默认值
            if (not 可执行.endswith('.exe')) or 目标 is None or 可执行 in 应用路径表:#跳过
                continue#下一条
            已展=展开注册表值(目标.strip('"'),事实)#去引号展开
            if 已展 is not None:#有效
                应用路径表[可执行]=已展#记下
    for 根 in 卸载根列表:#Uninstall
        转储=取命令输出('reg.exe',['query',根,'/s'],超时毫秒,事实)#查询
        if 转储 is None:#失败
            continue#下一根
        for 值表 in 解析注册表转储(转储).values():#每条记录
            if 'DisplayName' not in 值表:#无显示名
                continue#跳过
            安装记录列表.append(Windows安装记录(#收下
                显示名=值表['DisplayName'],#名
                安装位置=值表['InstallLocation'] if 'InstallLocation' in 值表 else None,#位置
                显示图标=值表['DisplayIcon'] if 'DisplayIcon' in 值表 else None,#图标
            ))#记录结束
    return Windows注册表视图(应用路径表=应用路径表,安装记录列表=tuple(安装记录列表))#视图

class 注册表视图一次:#惰性共享
    """一趟检测至多读一次注册表。"""
    def __init__(自身,超时毫秒,事实):#绑定
        """记下期限与事实。"""
        自身.超时毫秒=超时毫秒#期限
        自身.事实=事实#事实
        自身.视图=None#惰性

    def 读取(自身):#首次读取
        """返回本趟注册表视图。"""
        if 自身.视图 is None:#未读
            自身.视图=读Windows注册表视图(自身.超时毫秒,自身.事实)#读取
        return 自身.视图#视图

def 记录启动器(记录,相对启动器,事实):#Uninstall → exe
    """一条 Uninstall 记录能证明的可执行路径，或 None。"""
    if 相对启动器 is not None and 记录.安装位置 is not None and 记录.安装位置!='':#有位置
        已展=展开注册表值(记录.安装位置.strip('"'),事实)#展开
        if 已展 is not None:#有效
            候选=os.path.join(已展,相对启动器)#拼接
            if 是否普通文件(候选):#存在
                return 候选#命中
    if 记录.显示图标 is not None:#DisplayIcon
        裸=图标后缀模式.sub('',记录.显示图标).strip().strip('"').strip()#去索引与引号
        已展=展开注册表值(裸,事实)#展开
        if 已展 is not None and 已展.lower().endswith('.exe') and 是否普通文件(已展):#exe
            return 已展#命中
    return None#无

def 解析桌面条目文本(文本):#parseDesktopEntry
    """解析 [Desktop Entry] 的 Exec/TryExec/Icon。"""
    在条目内=False#是否在段内
    执行=尝试执行=图标=None#字段
    for 行 in 文本.splitlines():#逐行
        修剪=行.strip()#修剪
        if 修剪.startswith('['):#段头
            在条目内=修剪=='[Desktop Entry]'#目标段
            continue#下一段
        if not 在条目内:#段外
            continue#跳过
        分隔=修剪.find('=')#键值
        if 分隔<0:#无等号
            continue#跳过
        键=修剪[:分隔].strip()#键
        值=修剪[分隔+1:].strip()#值
        if 键=='Exec':#Exec
            执行=值#记下
        elif 键=='TryExec':#TryExec
            尝试执行=值#记下
        elif 键=='Icon':#Icon
            图标=值#记下
    return 桌面条目(执行=执行,尝试执行=尝试执行,图标=图标)#条目

def xdg数据目录列表(事实):#XDG data dirs
    """按优先级的 XDG 数据目录。"""
    数据家=事实.环境['XDG_DATA_HOME'] if 'XDG_DATA_HOME' in 事实.环境 and 事实.环境['XDG_DATA_HOME'] is not None else os.path.join(事实.家目录,'.local','share')#家
    数据目录串=事实.环境['XDG_DATA_DIRS'] if 'XDG_DATA_DIRS' in 事实.环境 and 事实.环境['XDG_DATA_DIRS'] is not None else '/usr/local/share:/usr/share'#目录串
    return [数据家]+[段 for 段 in 数据目录串.split(':') if 段!='']#列表

def 查找桌面条目(桌面标识,事实):#按 id 找 .desktop
    """在 XDG applications 下按 id 读 desktop 条目。"""
    for 数据目录 in xdg数据目录列表(事实):#逐目录
        路径=os.path.join(数据目录,'applications',桌面标识+'.desktop')#路径
        try:#读取
            with open(路径,'r',encoding='utf-8') as 文件:#打开
                return 解析桌面条目文本(文件.read())#解析
        except OSError:#ENOENT/EACCES
            pass#试下一个
    return None#未找到

def 执行命令首段(执行):#Exec 首 token
    """Exec= 值的第一个 token；缺席或空白则 None。"""
    if 执行 is None:#缺席
        return None#无
    引号=执行首段引号模式.match(执行)#引号
    if 引号 is not None:#有
        return 引号.group(1)#路径
    裸=执行首段裸名模式.match(执行)#裸
    return None if 裸 is None else 裸.group(0)#结果

def 桌面启动器(条目,事实):#desktop → exe
    """desktop 条目证明的可执行：TryExec 或 Exec 首段。"""
    候选=条目.尝试执行 if 条目.尝试执行 is not None else 执行命令首段(条目.执行)#候选
    if 候选 is None or 候选=='':#空
        return None#无
    if os.path.isabs(候选):#绝对
        return 候选 if 是否普通文件(候选) else None#核验
    return 事实.解析可执行(候选)#PATH

def 平台规格于(应用,平台):#specFor
    """条目在声明三平台上的规格；其它平台 None。"""
    if 平台=='darwin' or 平台=='win32' or 平台=='linux':#声明平台
        return 应用.平台表[平台] if 平台 in 应用.平台表 else None#规格
    return None#空

def 可执行图标(路径,事实):#Windows 可执行图标
    """已解析可执行的图标来源；仅 Windows。"""
    return 图标来源(种类='executable',路径=路径) if 事实.平台=='win32' else None#来源

def 自然降序(名称列表):#numeric localeCompare
    """版本感知降序（新→旧）。"""
    def 键(文本):#自然键
        """分段：数字段转 int。"""
        return [int(段) if 段.isdigit() else 段.lower() for 段 in 自然分段模式.split(文本)]#键
    return sorted(名称列表,key=键,reverse=True)#降序

def 定位(定位器,探测超时毫秒,注册表,事实):#locate one
    """把一条定位器解析为已验证启动，或 None。"""
    种类=定位器.种类#判别
    if 种类=='fixed':#固定
        图标路径=展开候选(定位器.图标路径,事实)#展开
        if 图标路径 is None:#变量未设
            图标=None#无图标声称
        elif 事实.平台=='win32':#Windows
            图标=图标来源(种类='executable',路径=图标路径)#可执行
        else:#macOS 等
            图标=图标来源(种类='app-bundle',路径=图标路径)#bundle
        return 已解析启动(启动=定位器.启动,图标=图标)#固定总成功
    if 种类=='app':#macOS bundle
        for 根 in 事实.应用根列表:#根
            for 名 in 定位器.文件系统名列表:#拼写
                包=os.path.join(根,名)#路径
                if 是否目录(包):#存在
                    return 已解析启动(#命中
                        启动=参数启动(命令='open',参数列表=('-a',包)),#open -a
                        图标=图标来源(种类='app-bundle',路径=包),#图标
                    )#结束
        return None#未找到
    if 种类=='xcode':#xcode-select
        开发者=取命令输出('xcode-select',['-p'],探测超时毫秒,事实)#路径
        if 开发者 is None:#失败
            return None#无
        包=os.path.dirname(os.path.dirname(开发者.strip()))#上两级
        if (not 包.endswith('.app')) or (not 是否目录(包)):#非 bundle
            return None#无
        return 已解析启动(#命中
            启动=参数启动(命令='xed',参数列表=()),#xed
            回退启动=参数启动(命令='open',参数列表=('-a',包)),#open -a
            图标=图标来源(种类='app-bundle',路径=包),#图标
        )#结束
    if 种类=='cli':#PATH
        if 定位器.需要桌面 is True and (not 能否打开原生路径({'平台':事实.平台,'环境':事实.环境})):#无桌面
            return None#不提供
        找到=事实.解析可执行(定位器.名称)#解析
        if 找到 is None:#未找到
            return None#无
        return 已解析启动(#命中
            启动=参数启动(命令=找到,参数列表=定位器.参数列表),#argv
            图标=可执行图标(找到,事实),#图标
        )#结束
    if 种类=='file':#候选文件
        for 候选 in 定位器.候选列表:#逐个
            路径=展开候选(候选,事实)#展开
            if 路径 is not None and 是否普通文件(路径):#存在
                return 已解析启动(#命中
                    启动=参数启动(命令=路径,参数列表=定位器.参数列表),#argv
                    图标=可执行图标(路径,事实),#图标
                )#结束
        return None#无
    if 种类=='scan':#版本扫描
        根=展开候选(定位器.根,事实)#根
        if 根 is None:#失败
            return None#无
        try:#列目录
            条目列表=os.listdir(根)#条目
        except OSError:#缺失
            return None#无
        版本列表=自然降序([名 for 名 in 条目列表 if 名.startswith(定位器.名称前缀)])#新→旧
        for 版本 in 版本列表:#逐版本
            启动器=os.path.join(根,版本,定位器.相对启动器)#路径
            if 是否普通文件(启动器):#存在
                return 已解析启动(#命中
                    启动=参数启动(命令=启动器,参数列表=定位器.参数列表),#argv
                    图标=可执行图标(启动器,事实),#图标
                )#结束
        return None#无
    if 种类=='app-paths':#App Paths
        目标=注册表.读取().应用路径表.get(定位器.可执行名.lower())#查表
        if 目标 is None or (not 是否普通文件(目标)):#无效
            return None#无
        return 已解析启动(#命中
            启动=参数启动(命令=目标,参数列表=定位器.参数列表),#argv
            图标=图标来源(种类='executable',路径=目标),#图标
        )#结束
    if 种类=='install-record':#Uninstall
        for 记录 in 注册表.读取().安装记录列表:#逐条
            if not 记录.显示名.startswith(定位器.显示名前缀):#前缀不配
                continue#下一条
            启动器=记录启动器(记录,定位器.相对启动器,事实)#推导
            if 启动器 is not None:#命中
                return 已解析启动(#命中
                    启动=参数启动(命令=启动器,参数列表=定位器.参数列表),#argv
                    图标=图标来源(种类='executable',路径=启动器),#图标
                )#结束
        return None#无
    if 种类=='github-desktop':#GitHub Desktop
        根=展开候选(定位器.根,事实)#根
        if 根 is None:#失败
            return None#无
        try:#列版本
            版本列表=自然降序([名 for 名 in os.listdir(根) if 名.startswith('app-')])#app-*
        except OSError:#缺失
            return None#无
        for 版本 in 版本列表:#逐版本
            目录=os.path.join(根,版本)#目录
            可执行=os.path.join(目录,'GitHubDesktop.exe')#exe
            命令行脚本=os.path.join(目录,'resources','app','cli.js')#cli
            if 是否普通文件(可执行) and 是否普通文件(命令行脚本):#齐备
                return 已解析启动(#命中
                    启动=参数启动(#argv
                        命令=可执行,#exe
                        参数列表=(命令行脚本,'open'),#cli open
                        环境={'ELECTRON_RUN_AS_NODE':'1'},#Electron 作 Node
                        隐藏窗口=True,#隐藏 CLI
                    ),#启动
                    图标=图标来源(种类='executable',路径=可执行),#图标
                )#结束
        return None#无
    if 种类=='desktop':#XDG
        条目=查找桌面条目(定位器.桌面标识,事实)#读
        if 条目 is None:#无
            return None#无
        启动器=桌面启动器(条目,事实)#可执行
        if 启动器 is None:#无
            return None#无
        return 已解析启动(启动=参数启动(命令=启动器,参数列表=定位器.参数列表))#无独立图标来源
    return 断言穷尽(定位器)#穷尽

def 经注册表解析(应用,探测超时毫秒,注册表,事实):#resolveWithRegistry
    """相对共享注册表视图解析一条条目。"""
    平台规格=平台规格于(应用,事实.平台)#规格
    if 平台规格 is None:#无
        return None#空
    for 定位器 in 平台规格.定位器列表:#按序
        找到=定位(定位器,探测超时毫秒,注册表,事实)#尝试
        if 找到 is not None:#命中
            return 找到#首个
    return None#全失败

def 解析启动(应用,探测超时毫秒,内部=None):#resolveLaunch
    """解析一条目录条目；SSH 拉起或未安装则 None。"""
    事实=补全内部事实(内部)#补全
    if 事实.ssh:#SSH 下不探测
        return None#空
    return 经注册表解析(应用,探测超时毫秒,注册表视图一次(探测超时毫秒,事实),事实)#解析

def 解析在应用中打开应用(探测超时毫秒,内部=None):#resolveOpenInAppApps
    """解析整份目录一次：标识 → 已验证启动（目录顺序）。SSH 拉起时不探测，返回空映射。"""
    事实=补全内部事实(内部)#补全
    if 事实.ssh:#SSH 拉起
        return {}#空表
    注册表=注册表视图一次(探测超时毫秒,事实)#共享
    映射={}#可变权威
    for 应用 in 在应用中打开目录:#菜单序
        启动=经注册表解析(应用,探测超时毫秒,注册表,事实)#解析
        if 启动 is not None:#可用
            映射[应用.标识]=启动#写入
    return 映射#映射

def 启动参数列表(参数列表,路径):#PATH_TOKEN 替换
    """把目录令牌代入 argv；无令牌则追加目录。"""
    列表=list(参数列表)#复制
    if any(路径令牌 in 段 for 段 in 列表):#有令牌
        return [段.replace(路径令牌,路径) for 段 in 列表]#全替
    return 列表+[路径]#追加

def 是否可执行缺失(错误):#ENOENT
    """启动拒绝是否表示可执行文件缺失。"""
    if isinstance(错误,OSError) and 错误.errno==errno.ENOENT:#系统 ENOENT
        return True
    码=getattr(错误,'code',None)#挂靠码
    return 码=='ENOENT'

def 执行外壳打开(路径,看护毫秒,事实):#shell-open
    """在看护窗口下经 OS open verb 打开目录。"""
    信号=threading.Event()#不主动中止
    完成=threading.Event()#结算
    结局={'值':'failed'}#默认失败

    def 工作():#打开线程
        """调用原生打开器。"""
        try:#打开
            打开原生路径(路径,信号,{'平台':事实.平台,'运行':事实.运行,'环境':事实.环境})#打开
            结局['值']='launched'#成功
        except (OSError,原生命令错误,在应用中打开错误) as 错误:
            结局['值']='missing' if 是否可执行缺失(错误) else 'failed'
        finally:#结算
            完成.set()#完成

    线程=threading.Thread(target=工作,daemon=True)#后台
    线程.start()#开始
    if 完成.wait(timeout=看护毫秒/1000.0 if 看护毫秒 else None):#窗口内结束
        return 结局['值']#结局
    return 'launched'#仍在跑 → 已启动

def 执行启动器(启动,路径,看护毫秒,事实):#runLaunch
    """执行一条启动器并归类结局。"""
    if 启动.种类=='shell-open':#外壳
        return 执行外壳打开(路径,看护毫秒,事实)#打开
    if 启动.种类=='argv':#argv
        try:#派生
            选项={'看护毫秒':看护毫秒}#看护
            if 启动.环境 is not None:#环境
                选项['环境']=启动.环境#叠入
            if 启动.隐藏窗口 is not None:#隐藏
                选项['隐藏窗口']=启动.隐藏窗口#叠入
            事实.启动(启动.命令,启动参数列表(启动.参数列表,路径),选项)#启动
            return 'launched'#成功
        except (OSError,原生命令错误,在应用中打开错误) as 错误:
            return 'missing' if 是否可执行缺失(错误) else 'failed'
    return 断言穷尽(启动)#穷尽

def 启动已解析(已解析,路径,看护毫秒,内部=None):#launchResolved
    """启动已解析应用：主启动器，失败则回退。"""
    事实=补全内部事实(内部)#补全
    主=执行启动器(已解析.启动,路径,看护毫秒,事实)#主
    if 主=='launched' or 已解析.回退启动 is None:#成功或无回退
        return 主#结局
    回退=执行启动器(已解析.回退启动,路径,看护毫秒,事实)#回退
    if 回退=='launched':#回退成功
        return 'launched'#成功
    return 'missing' if 主=='missing' or 回退=='missing' else 'failed'#缺失优先
