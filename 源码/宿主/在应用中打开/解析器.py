'把目录条目解析成本机真实持有的启动器，并在看护窗口内分离启动'
import errno,os,re,signal,subprocess,sys,threading#平台、派生与看护
from ...工具.原生命令 import (
    可打开原生路径,#有没有桌面会话
    打开原生路径,#操作系统的打开动作
    运行原生命令,#无 shell 的宿主命令
)
from ...工具.原生命令.桌面条目 import (
    桌面条目字段,#Exec / TryExec / Icon
    桌面数据目录,#XDG 数据目录
)
from ...子进程.子进程 import 擦洗父环境#去掉凭证形态和 DSH_ 名字
from .异常 import 在应用中打开错误,断言穷尽#缺解析器时大声失败；封闭并集
from .目录 import 路径令牌#工作区目录在 argv 里的占位

__all__=[
    '分离启动应用','补全内部事实','取命令输出','是否目录','是否普通文件',
    '展开候选','展开注册表值','去掉两端引号','解析注册表转储','查找桌面条目',
    'xdg数据目录','平台规格于','可执行图标','自然降序键','是否可执行缺失',
    '执行启动','经注册表解析','启动已解析','注册表视图一次',
]

变量模式=re.compile(r'\$\{([^}]+)\}')#${VAR}
百分变量模式=re.compile(r'%([^%]+)%')#%VAR%
注册表值模式=re.compile(r'^\s+(.*?)\s+(REG_SZ|REG_EXPAND_SZ)\s+(.*)$')#reg.exe 的值行
键路径模式=re.compile(r'^HK')#子键路径行
默认值名模式=re.compile(r'^\(.*\)$')#本地化的默认值名，两侧是括号
执行首段引号模式=re.compile(r'^"([^"]+)"')#Exec 的引号路径
执行首段裸名模式=re.compile(r'^\S+')#Exec 的裸第一段
图标后缀模式=re.compile(r',-?\d+$')#DisplayIcon 末尾的图标索引

应用路径根列表=(#用户巢优先，盖住机器巢
    'HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\App Paths',
    'HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths',
)
卸载根列表=(#用户、64 位机器、32 位机器视图
    'HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall',
    'HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall',
    'HKLM\\SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall',
)

def 去掉两端引号(文本):
    '去掉注册表值开头和结尾各一个引号'
    if 文本.startswith('"'):#开头一个
        文本=文本[1:]
    if 文本.endswith('"'):#结尾一个
        文本=文本[:-1]
    return 文本

def 分离启动应用(命令,参数列表,选项):
    '分离派生一条界面程序。看护窗口内早退或派生失败就抛出；窗口结束仍在跑则算成功，进程继续留着'
    环境=擦洗父环境()#父环境去掉凭证
    if 选项.get('env') is not None:#适配器自己的环境盖上去
        环境.update(选项['env'])
    关键字={
        'stdin':subprocess.DEVNULL,#不接标准输入
        'stdout':subprocess.DEVNULL,#不接标准输出
        'stderr':subprocess.DEVNULL,#不接标准错误
        'env':环境,#擦洗后再盖适配器环境
        'shell':False,#argv，不是命令字符串
    }
    if os.name=='nt':#Windows 分离，并按适配器决定是否藏窗口
        标志=0x00000008#DETACHED_PROCESS
        if 选项.get('windowsHide') is True:#只有明确要求才藏
            标志=标志|0x08000000#CREATE_NO_WINDOW
        关键字['creationflags']=标志
    else:#POSIX 新会话，父进程退出后子进程还在
        关键字['start_new_session']=True
    try:#派生失败在这里抛，相当于 Node 的 error 事件
        子进程=subprocess.Popen([命令,*list(参数列表)],**关键字)
    except FileNotFoundError as 错误:#可执行文件不在
        错误.code='ENOENT'#让调用方认出陈旧解析
        raise
    except OSError as 错误:#其它派生错误；ENOENT 同样标上
        if 错误.errno==errno.ENOENT:
            错误.code='ENOENT'
        raise
    结束=threading.Event()#退出或等待失败
    盒子={}#退出码或等待错误

    def 等退出():
        '在旁路线程里等子进程，主路线程只等看护窗口'
        try:
            盒子['码']=子进程.wait()#退出码；信号在 POSIX 上是负数
        except Exception as 错误:#等待本身失败
            盒子['错误']=错误
        结束.set()#通知主路

    等待线程=threading.Thread(target=等退出,daemon=True)#不挡住进程退出
    等待线程.start()#开始等
    if not 结束.wait(选项['watchMs']/1000.0):#窗口结束仍在跑
        return#算已启动，不杀进程
    if '错误' in 盒子:#等待失败
        raise 盒子['错误']
    码=盒子['码']#退出码
    if 码==0:#正常退出
        return
    if 码 is not None and 码<0:#被信号杀掉
        try:
            信号名=signal.Signals(-码).name#SIGTERM 这类名字
        except ValueError:#不是已知信号
            信号名=str(-码)
        raise 在应用中打开错误('launcher exited with code null, signal '+信号名)
    raise 在应用中打开错误('launcher exited with code '+str(码)+', signal null')

def 补全内部事实(内部):
    '按运行宿主补全可覆盖事实。没给解析可执行就大声失败'
    if 内部 is None:#调用方省略
        内部={}
    家目录=内部.get('home')#测试可换家目录
    if 家目录 is None:
        家目录=os.path.expanduser('~')#本机家目录
    解析可执行=内部.get('resolveExecutable')#必须由插件或测试给
    if 解析可执行 is None:
        raise 在应用中打开错误('open-in-app: internals.resolveExecutable is required (the subprocess capability provides it)')
    平台=内部.get('platform')#Node 平台名
    if 平台 is None:
        系统名=sys.platform#本机
        if 系统名.startswith('linux'):#linux 与带版本的名字都收成 linux
            平台='linux'
        else:
            平台=系统名
    ssh值=内部.get('ssh')#SSH 拉起时不探测
    if ssh值 is None:
        ssh值=False
    应用根=内部.get('applicationRoots')#macOS 应用目录根
    if 应用根 is None:
        应用根=('/Applications',os.path.join(家目录,'Applications'))
    环境=内部.get('env')#变量展开用的环境
    if 环境 is None:
        环境=os.environ
    运行=内部.get('run')#宿主命令
    if 运行 is None:
        运行=运行原生命令
    启动=内部.get('launch')#分离启动器
    if 启动 is None:
        启动=分离启动应用
    return {
        'platform':平台,
        'ssh':ssh值,
        'applicationRoots':应用根,
        'env':环境,
        'home':家目录,
        'run':运行,
        'launch':启动,
        'resolveExecutable':解析可执行,
    }

def 取命令输出(命令,参数列表,超时毫秒,事实):
    '跑一条有期限的宿主命令。成功交回标准输出，派生失败、非零退出和到时都交回 None'
    信号=threading.Event()#到时置位，运行器据此中止
    定时=threading.Timer(超时毫秒/1000.0,信号.set)#期限
    定时.daemon=True#不挡住进程退出
    定时.start()
    try:
        结果=事实['run'](命令,参数列表,信号)#现有运行器不收第四个 hidden
        return 结果['stdout']#退出码 0 的标准输出
    except Exception as 失败:#派生、非零退出、到时，都是不可用
        return None
    finally:
        定时.cancel()#命令已经结束就拆掉定时器

def 是否目录(路径):
    '路径存在并且是目录'
    try:
        return os.path.isdir(路径)#符号链接指向目录也算
    except OSError as 错误:#读不到就不是 bundle
        return False

def 是否普通文件(路径):
    '路径存在并且是普通文件'
    try:
        return os.path.isfile(路径)#目录不算
    except OSError as 错误:#读不到就不是启动器
        return False

def 展开候选(模板,事实):
    '展开 ${VAR}，以及开头的 ~/。有变量没设置就没有结果'
    未设=[]#没设置的变量名

    def 替换(匹配):
        '替换一个 ${变量}。没设置就先记下，整段稍后作废'
        名=匹配.group(1)#变量名
        值=事实['env'].get(名)#缺席是 None
        if 值 is None:
            未设.append(名)#记一笔
            return 匹配.group(0)#先留原文
        return 值#换成变量值

    展开=变量模式.sub(替换,模板)#只做字符串替换
    if len(未设)>0:#有变量没设置
        return None
    if 展开.startswith('~/'):#家目录前缀
        return os.path.join(事实['home'],展开[2:])
    return 展开

def 展开注册表值(值,事实):
    '展开注册表值里的 %VAR%。有变量没设置就没有结果'
    未设=[]#没设置的变量名

    def 替换(匹配):
        '替换一个 %变量%'
        名=匹配.group(1)#变量名
        找到=事实['env'].get(名)#缺席是 None
        if 找到 is None:
            未设.append(名)#记一笔
            return 匹配.group(0)#先留原文
        return 找到

    展开=百分变量模式.sub(替换,值)#字符串替换
    if len(未设)>0:
        return None
    return 展开

def 解析注册表转储(转储):
    '把 reg.exe query /s 的输出收成子键到 REG_SZ / REG_EXPAND_SZ 值'
    键表={}#子键路径 → 值名 → 数据
    当前=None#当前子键
    for 行 in re.split(r'\r?\n',转储):#按行
        if 键路径模式.match(行):#新的子键
            当前={}
            键表[行.strip()]=当前
            continue
        匹配=注册表值模式.match(行)#值行
        if 匹配 is None or 当前 is None:#不是字符串值，或还没有子键
            continue
        名=匹配.group(1)#值名。默认值的字样随语言变
        数据=匹配.group(3)#值数据
        if 默认值名模式.match(名):#各种语言都包在括号里
            名='(Default)'
        当前[名]=数据.strip()#去掉数据两端空白
    return 键表

def 查找桌面条目(桌面标识,事实):
    '在 XDG applications 目录里按标识读 desktop 条目。都没有则 None'
    for 数据目录 in xdg数据目录(事实):#优先级从高到低
        路径=os.path.join(数据目录,'applications',桌面标识+'.desktop')#条目文件
        try:
            with open(路径,'r',encoding='utf-8') as 文件:#读文本
                文本=文件.read()
        except OSError as 错误:#没有或读不到，试下一个数据目录
            continue
        字段=桌面条目字段(文本)#只认主节
        条目={}#Exec / TryExec / Icon
        if 'Exec' in 字段:
            条目['exec']=字段['Exec']
        if 'TryExec' in 字段:
            条目['tryExec']=字段['TryExec']
        if 'Icon' in 字段:
            条目['icon']=字段['Icon']
        return 条目#第一个读到的
    return None

def xdg数据目录(事实):
    '按优先级排列的 XDG 数据目录'
    return 桌面数据目录(事实['home'],事实['env'])#含 freedesktop 默认

def 平台规格于(应用,平台):
    '条目在 darwin、win32、linux 上的规格。其它平台没有'
    if 平台 not in ('darwin','win32','linux'):#目录没声明的平台
        return None
    return 应用['platforms'].get(平台)#这一条可能也不声明该平台

def 可执行图标(路径,事实):
    '已解析可执行文件的图标来源。只有 Windows 从二进制本身取'
    if 事实['platform']=='win32':
        return {'kind':'executable','path':路径}
    return None

def 自然降序键(名称):
    '版本名的比较键。数字段按整数，供从新到旧排序'
    键=[]#段
    for 段 in re.split(r'(\d+)',名称):#数字单独成段
        if 段.isdigit():
            键.append((0,int(段)))#按数值
        else:
            键.append((1,段))#其余按文本
    return tuple(键)

def 是否可执行缺失(错误):
    '这次失败是不是可执行文件已经不在'
    return isinstance(错误,BaseException) and getattr(错误,'code',None)=='ENOENT'

def 执行启动(启动,路径,看护毫秒,事实):
    '跑一条启动器，并归成 launched、missing 或 failed'
    种类=启动['kind']#argv 或 shell-open
    if 种类=='shell-open':#交给操作系统的打开动作
        盒子={'结局':'failed'}#窗口内若失败，默认失败
        结束=threading.Event()#打开动作结束

        def 跑打开():
            '在旁路等打开动作。窗口已经算成功之后，这里的失败不再改结果'
            try:
                打开原生路径(路径,threading.Event(),{#新的未中止信号
                    'platform':事实['platform'],
                    'run':事实['run'],
                    'env':事实['env'],
                })
                盒子['结局']='launched'#打开动作自己结束了
            except Exception as 错误:#窗口内失败
                if 是否可执行缺失(错误):
                    盒子['结局']='missing'
                else:
                    盒子['结局']='failed'
            结束.set()

        打开线程=threading.Thread(target=跑打开,daemon=True)#晚到的结算不挡住请求
        打开线程.start()
        if not 结束.wait(看护毫秒/1000.0):#到时还在跑
            return 'launched'#算已启动，晚到的失败丢掉
        return 盒子['结局']
    if 种类=='argv':#分离派生
        参数=启动['args']#声明的 argv
        if any(路径令牌 in 段 for 段 in 参数):#有占位就替换
            实际参数=[段.replace(路径令牌,路径) for 段 in 参数]
        else:#没有占位就把目录接在后面
            实际参数=list(参数)+[路径]
        选项={'watchMs':看护毫秒}#看护窗口
        if 启动.get('env') is not None:#适配器环境
            选项['env']=启动['env']
        if 启动.get('windowsHide') is not None:#显式隐藏或显式不隐藏
            选项['windowsHide']=启动['windowsHide']
        try:
            事实['launch'](启动['command'],实际参数,选项)#分离启动
            return 'launched'
        except Exception as 错误:#派生失败或窗口内早退
            if 是否可执行缺失(错误):
                return 'missing'#调用方会重解析这一条
            return 'failed'
    断言穷尽(启动)#封闭的启动种类

def 经注册表解析(应用,探测超时毫秒,注册表,事实):
    '按本平台定位器的书写顺序，第一个核验通过的启动器胜出'
    平台规格=平台规格于(应用,事实['platform'])#本机平台
    if 平台规格 is None:#这条在本平台没有声明
        return None
    for 定位器 in 平台规格['locators']:#按序
        种类=定位器['kind']#定位种类
        找到=None#这一条没有核验通过
        if 种类=='fixed':#随系统出货。图标路径不探测，变量没设置才丢掉图标
            图标路径=展开候选(定位器['iconPath'],事实)
            if 图标路径 is None:
                图标=None
            elif 事实['platform']=='win32':
                图标={'kind':'executable','path':图标路径}
            else:
                图标={'kind':'app-bundle','path':图标路径}
            找到={'launch':定位器['launch'],'icon':图标}
        elif 种类=='app':#已知应用目录里的 bundle
            for 根 in 事实['applicationRoots']:
                if 找到 is not None:
                    break
                for 文件名 in 定位器['fsNames']:
                    包=os.path.join(根,文件名)#bundle 目录
                    if 是否目录(包):
                        找到={
                            'launch':{'kind':'argv','command':'open','args':('-a',包)},
                            'icon':{'kind':'app-bundle','path':包},
                        }
                        break
        elif 种类=='xcode':#跟随 xcode-select -p
            开发者目录=取命令输出('xcode-select',['-p'],探测超时毫秒,事实)
            if 开发者目录 is not None:
                包=os.path.dirname(os.path.dirname(开发者目录.strip()))#Developer 的上两级
                if 包.endswith('.app') and 是否目录(包):
                    找到={
                        'launch':{'kind':'argv','command':'xed','args':()},
                        'fallbackLaunch':{'kind':'argv','command':'open','args':('-a',包)},
                        'icon':{'kind':'app-bundle','path':包},
                    }
        elif 种类=='cli':#PATH 名
            需要桌面=定位器.get('requiresDesktop') is True
            桌面可用=True
            if 需要桌面:#没有桌面会话就不提供
                桌面可用=可打开原生路径({'platform':事实['platform'],'env':dict(事实['env'])})
            if 桌面可用:
                命中=事实['resolveExecutable'](定位器['name'])#进程内解析
                if 命中 is not None:
                    找到={
                        'launch':{'kind':'argv','command':命中,'args':定位器['args']},
                        'icon':可执行图标(命中,事实),
                    }
        elif 种类=='file':#第一个存在的候选
            for 候选模板 in 定位器['candidates']:
                路径=展开候选(候选模板,事实)
                if 路径 is not None and 是否普通文件(路径):
                    找到={
                        'launch':{'kind':'argv','command':路径,'args':定位器['args']},
                        'icon':可执行图标(路径,事实),
                    }
                    break
        elif 种类=='scan':#版本目录，新的优先
            根=展开候选(定位器['root'],事实)
            if 根 is not None:
                try:
                    条目列表=os.listdir(根)#安装根下的名字
                except OSError as 错误:#根不存在或读不到
                    条目列表=None
                if 条目列表 is not None:
                    版本列表=sorted(
                        [项 for 项 in 条目列表 if 项.startswith(定位器['namePrefix'])],
                        key=自然降序键,
                        reverse=True,
                    )#数字感知，新的在前
                    for 版本 in 版本列表:
                        启动器=os.path.join(根,版本,定位器['relativeLauncher'])
                        if 是否普通文件(启动器):
                            找到={
                                'launch':{'kind':'argv','command':启动器,'args':定位器['args']},
                                'icon':可执行图标(启动器,事实),
                            }
                            break
        elif 种类=='app-paths':#App Paths 默认值
            目标=注册表.读取()['appPaths'].get(定位器['exe'].lower())
            if 目标 is not None and 是否普通文件(目标):
                找到={
                    'launch':{'kind':'argv','command':目标,'args':定位器['args']},
                    'icon':{'kind':'executable','path':目标},
                }
        elif 种类=='install-record':#Uninstall 记录证明的可执行文件
            相对=定位器.get('relativeLauncher')
            for 记录 in 注册表.读取()['installRecords']:
                if not 记录['displayName'].startswith(定位器['displayNamePrefix']):
                    continue
                启动器路径=None#这条记录还没证明出文件
                安装位置=记录.get('installLocation')
                if 相对 is not None and 安装位置 not in (None,''):
                    展开位置=展开注册表值(去掉两端引号(安装位置),事实)
                    if 展开位置 is not None:
                        候选=os.path.join(展开位置,相对)
                        if 是否普通文件(候选):
                            启动器路径=候选
                if 启动器路径 is None and 记录.get('displayIcon') is not None:
                    裸=图标后缀模式.sub('',记录['displayIcon'])#去掉 ,0 这类索引
                    裸=去掉两端引号(裸).strip()#引号和空白
                    展开图标=展开注册表值(裸,事实)
                    if 展开图标 is not None and 展开图标.lower().endswith('.exe') and 是否普通文件(展开图标):
                        启动器路径=展开图标
                if 启动器路径 is not None:
                    找到={
                        'launch':{'kind':'argv','command':启动器路径,'args':定位器['args']},
                        'icon':{'kind':'executable','path':启动器路径},
                    }
                    break
        elif 种类=='github-desktop':#版本目录里的 exe 和 cli.js 要同时在
            根=展开候选(定位器['root'],事实)
            if 根 is not None:
                try:
                    版本列表=sorted(
                        [项 for 项 in os.listdir(根) if 项.startswith('app-')],
                        key=自然降序键,
                        reverse=True,
                    )#新的版本在前
                except OSError as 错误:#安装根不存在或读不到
                    版本列表=None
                if 版本列表 is not None:
                    for 版本 in 版本列表:
                        目录路径=os.path.join(根,版本)
                        可执行=os.path.join(目录路径,'GitHubDesktop.exe')
                        命令行文件=os.path.join(目录路径,'resources','app','cli.js')
                        if 是否普通文件(可执行) and 是否普通文件(命令行文件):
                            找到={
                                'launch':{
                                    'kind':'argv',
                                    'command':可执行,
                                    'args':(命令行文件,'open'),
                                    'env':{'ELECTRON_RUN_AS_NODE':'1'},
                                    'windowsHide':True,
                                },
                                'icon':{'kind':'executable','path':可执行},
                            }
                            break
        elif 种类=='desktop':#XDG 条目证明的可执行文件。TryExec 优先，否则 Exec 第一段
            条目=查找桌面条目(定位器['desktopId'],事实)
            if 条目 is not None:
                候选=条目.get('tryExec')#有 TryExec 就用它，包括空串
                if 候选 is None:
                    执行=条目.get('exec')
                    if 执行 is None:
                        候选=None
                    else:
                        引号匹配=执行首段引号模式.match(执行)
                        if 引号匹配 is not None:
                            候选=引号匹配.group(1)#引号里的路径
                        else:
                            裸匹配=执行首段裸名模式.match(执行)
                            候选=None if 裸匹配 is None else 裸匹配.group(0)
                if 候选 is not None and 候选!='':
                    if os.path.isabs(候选):
                        启动器=候选 if 是否普通文件(候选) else None
                    else:
                        启动器=事实['resolveExecutable'](候选)#裸名走 PATH
                    if 启动器 is not None:
                        找到={'launch':{'kind':'argv','command':启动器,'args':定位器['args']}}
        else:
            断言穷尽(定位器)#封闭的定位种类
        if 找到 is not None:#这一条已经核验通过
            return 找到
    return None#本平台的定位器都没证明出启动器

def 启动已解析(已解析,路径,看护毫秒,内部=None):
    '先跑主启动器。主启动器没打开且声明了回退，再跑回退。试过的可执行文件不见了就返回 missing'
    if 内部 is None:#调用方省略
        内部={}
    完成=补全内部事实(内部)#补齐启动器
    主结局=执行启动(已解析['launch'],路径,看护毫秒,完成)#主启动器
    回退=已解析.get('fallbackLaunch')#没有回退就是 None
    if 主结局=='launched' or 回退 is None:
        return 主结局
    回退结局=执行启动(回退,路径,看护毫秒,完成)#回退启动器
    if 回退结局=='launched':
        return 'launched'
    if 主结局=='missing' or 回退结局=='missing':#任一文件不见了都要重解析
        return 'missing'
    return 'failed'

class 注册表视图一次:
    '一趟检测最多读一次注册表'
    def __init__(自身,超时毫秒,事实):
        '记下这一趟的期限和已补全事实'
        自身.超时毫秒=超时毫秒#每条 reg.exe 的期限
        自身.事实=事实#平台事实
        自身.视图=None#还没读

    def 读取(自身):
        '第一次调用时读 App Paths 和 Uninstall。根失败或缺失就跳过'
        if 自身.视图 is None:#这一趟还没读
            应用路径表={}#小写 exe 名 → 默认值路径。先写入的用户巢保留
            安装记录列表=[]#DisplayName 以及可选的位置和图标
            for 根 in 应用路径根列表:#两条 App Paths
                转储=取命令输出('reg.exe',['query',根,'/s'],自身.超时毫秒,自身.事实)
                if 转储 is None:#这条根没有或查询失败
                    continue
                for 键,值表 in 解析注册表转储(转储).items():
                    可执行名=键[键.rfind('\\')+1:].lower()#最后一段，测试在 POSIX 上也不用 basename
                    目标=值表.get('(Default)')#默认值
                    if (not 可执行名.endswith('.exe')) or 目标 is None or 可执行名 in 应用路径表:
                        continue#不是 exe，没有默认值，或用户巢已经占了这个名字
                    展开=展开注册表值(去掉两端引号(目标),自身.事实)
                    if 展开 is not None:
                        应用路径表[可执行名]=展开
            for 根 in 卸载根列表:#三条 Uninstall
                转储=取命令输出('reg.exe',['query',根,'/s'],自身.超时毫秒,自身.事实)
                if 转储 is None:
                    continue
                for 值表 in 解析注册表转储(转储).values():
                    显示名=值表.get('DisplayName')
                    if 显示名 is None:#没有显示名就不是一条安装记录
                        continue
                    安装记录列表.append({
                        'displayName':显示名,
                        'installLocation':值表.get('InstallLocation'),
                        'displayIcon':值表.get('DisplayIcon'),
                    })
            自身.视图={'appPaths':应用路径表,'installRecords':tuple(安装记录列表)}#这一趟的事实
        return 自身.视图
