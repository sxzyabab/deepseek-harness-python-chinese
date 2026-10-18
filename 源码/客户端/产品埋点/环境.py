'与账号、凭据无关的桌面静态环境字段'
import base64,ctypes,json,os,platform,re,sys#编码、内存、路径与平台
from ...基础设施.通用工具 import 启动守护线程#两条查询同时跑
from ...基础设施.通用工具.数值判定 import 是否正安全整数#正的安全整数
from .环境查询 import 查询环境#固定命令

__all__=['收集环境']#仅中文公开名

数字模式=re.compile(r'^\d+$')#纯数字
产品版本模式=re.compile(r'^(\d+(?:\.\d+){1,2})(?: (\([a-z]\)))?$')#主版本，可选内联后缀
额外版本模式=re.compile(r'^\([a-z]\)$')#独立的安全响应后缀
构建版本模式=re.compile(r'^\d+[A-Za-z]\d+[a-z]?$')#macOS 构建号
版本查询=(#Windows 版本注册表。脚本原文保持英文
    "\n$ErrorActionPreference = 'Stop'\n"
    "$r = Get-Item -LiteralPath 'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion'\n"
    "@{ major = $r.GetValue('CurrentMajorVersionNumber'); minor = $r.GetValue('CurrentMinorVersionNumber'); "
    "build = $r.GetValue('CurrentBuildNumber'); revision = $r.GetValue('UBR') } | ConvertTo-Json -Compress\n"
)#版本查询结束
处理器查询=(#Windows 物理核与架构。脚本原文保持英文
    "\n$ErrorActionPreference = 'Stop'\n"
    'ConvertTo-Json -Compress -InputObject @(Get-CimInstance -ClassName Win32_Processor '
    '-Property NumberOfCores,Architecture | ForEach-Object { @{ cores = $_.NumberOfCores; architecture = $_.Architecture } })\n'
)#处理器查询结束
架构名={0:'ia32',5:'arm',9:'x64',12:'arm64'}#Win32_Processor.Architecture

def 拆行(标准输出):
    '冒号左右拆成键值。没有冒号时键去掉末字符，值是整行'
    结果={}//后写的同名键覆盖先写的
    for 行 in re.split(r'\r?\n',标准输出.strip()):#按行
        冒号=行.find(':')#第一处冒号
        if 冒号<0:#没有冒号
            键=行[:-1].strip()#去掉末字符
            值=行.strip()#整行
        else:#有冒号
            键=行[:冒号].strip()#左侧
            值=行[冒号+1:].strip()#右侧
        结果[键]=值#记下
    return 结果#键值

def 解码(标准输出):
    '命令输出不是合法 JSON 时没有元数据'
    try:#只解析，不校验字段
        return json.loads(标准输出)#对象或数组
    except Exception as 解析错误:#畸形 JSON，不把原文交出去
        return None#调用方记 invalid-value

def 收集环境(选项):
    '只收批准过的元数据。一个来源失败，只让依赖它的字段缺失'
    平台=sys.platform#win32、darwin 或其他
    if 平台=='darwin':#对外写成 macos
        系统名='macos'#产品名
    elif 平台=='win32':#对外写成 windows
        系统名='windows'#产品名
    else:#其余平台原样
        系统名=平台#不改名
    机器=platform.machine().lower()#本进程机器名
    if 机器 in ('amd64','x86_64'):#64 位 x86
        应用架构='x64'#与 process.arch 相同的词
    elif 机器 in ('arm64','aarch64'):#64 位 ARM
        应用架构='arm64'#与 process.arch 相同的词
    elif 机器 in ('x86','i386','i686'):#32 位 x86
        应用架构='ia32'#与 process.arch 相同的词
    elif 机器.startswith('arm'):#32 位 ARM
        应用架构='arm'#与 process.arch 相同的词
    else:#其余原样
        应用架构=机器#不发明名字
    字段={'os_name':系统名,'app_arch':应用架构,'missing_fields':{}}#总能给出的两项
    def 标记缺失(键列表,原因):
        '把这些字段记成同一个固定原因'
        for 键 in 键列表:#逐个
            字段['missing_fields'][键]=原因#后来的覆盖先前的
    def 读取(键,来源):
        '来源抛错、空串或不是正的安全整数时，只记这一个字段缺失'
        try:#一个来源失败不影响已经收下的字段
            值=来源()#取值
        except Exception:#来源拒绝
            标记缺失([键],'unavailable')#不可用
            return#换下一个字段
        if 值 is None or 值=='':#空
            标记缺失([键],'unavailable')#不可用
            return#不写入
        if isinstance(值,(int,float)) and not isinstance(值,bool) and not 是否正安全整数(值):#0、小数、过大
            标记缺失([键],'unavailable')#不可用
            return#不写入
        字段[键]=值#收下
    def 取系统版本():
        '平台名加内核版本'
        if 平台=='win32':#Windows 的内核版本是 major.minor.build
            版本=platform.version()#例如 10.0.26100
        else:#其余用 uname 的 release
            版本=platform.release()#内核版本
        return 平台+' '+版本#例如 win32 10.0.26100
    def 总内存():
        '物理内存字节数'
        if 平台=='win32':#Windows 没有 sysconf 页数
            class 内存状态(ctypes.Structure):
                'GlobalMemoryStatusEx 的结果'
                _fields_=[#只使用总物理内存
                    ('dwLength',ctypes.c_ulong),#结构长度
                    ('dwMemoryLoad',ctypes.c_ulong),#占用
                    ('ullTotalPhys',ctypes.c_ulonglong),#总物理内存
                    ('ullAvailPhys',ctypes.c_ulonglong),#可用物理内存
                    ('ullTotalPageFile',ctypes.c_ulonglong),#总页面文件
                    ('ullAvailPageFile',ctypes.c_ulonglong),#可用页面文件
                    ('ullTotalVirtual',ctypes.c_ulonglong),#总虚拟内存
                    ('ullAvailVirtual',ctypes.c_ulonglong),#可用虚拟内存
                    ('ullAvailExtendedVirtual',ctypes.c_ulonglong),#扩展虚拟内存
                ]#字段结束
            状态=内存状态()#空结果
            状态.dwLength=ctypes.sizeof(内存状态)#必须先写长度
            函数=ctypes.windll.kernel32.GlobalMemoryStatusEx#系统调用
            函数.argtypes=[ctypes.POINTER(内存状态)]#64 位上传指针
            函数.restype=ctypes.c_int#非零为成功
            成功=函数(ctypes.byref(状态))#读取
            if not 成功:#系统拒绝
                raise OSError('GlobalMemoryStatusEx failed')#交给读取记缺失
            return int(状态.ullTotalPhys)#字节
        页大小=os.sysconf('SC_PAGE_SIZE')#一页字节
        页数=os.sysconf('SC_PHYS_PAGES')#物理页数
        return int(页大小*页数)#字节
    读取('os_version',取系统版本)#平台与内核版本
    读取('memory_total_bytes',总内存)#物理内存
    型号文本=None#第一颗逻辑处理器
    逻辑数=None#逻辑处理器个数
    try:#两样都来自同一次处理器枚举
        逻辑数=os.cpu_count()#系统报告的逻辑处理器
        if 逻辑数 is None:#数不出来
            raise OSError('logical cpu count unavailable')#型号和个数一起缺失
        型号文本=platform.processor()#型号字符串
    except Exception:#枚举失败
        型号文本=None#没有型号
        逻辑数=None#没有个数
    def 取型号():
        '第一颗逻辑处理器的型号，去掉两端空白'
        if 型号文本 is None:#枚举失败
            return None#记缺失
        return 型号文本.strip()#空白型号会在读取里记缺失
    def 取逻辑数():
        '系统报告的逻辑处理器个数，不是可用并行度'
        if 逻辑数 is None:#枚举失败
            return 0#0 会在读取里记缺失
        return 逻辑数#个数
    读取('cpu_model',取型号)#型号
    读取('cpu_logical_count',取逻辑数)#逻辑核
    if 平台=='win32':#Windows 再问注册表和 CIM
        根=os.environ.get('SystemRoot')#系统目录
        if 根 is None or 根=='':#没有系统目录就不能问
            标记缺失(['os_version_full','os_build','os_arch','cpu_physical_core_count'],'unavailable')#四项都缺
            return 字段#本地字段保留
        命令=os.path.join(根,'System32','WindowsPowerShell','v1.0','powershell.exe')#固定可执行文件
        def 询问(脚本):
            '把脚本编成 UTF-16LE 的 Base64 再问'
            编码=base64.b64encode(脚本.encode('utf-16le')).decode('ascii')#EncodedCommand
            return 查询环境(命令,['-NoProfile','-NonInteractive','-EncodedCommand',编码],选项)#不经 shell
        版本盒={}//版本查询结果
        处理器盒={}//处理器查询结果
        def 跑版本():
            '问 CurrentVersion'
            版本盒['值']=询问(版本查询)#结果
        def 跑处理器():
            '问 Win32_Processor'
            处理器盒['值']=询问(处理器查询)#结果
        版本线程=启动守护线程(跑版本)#与处理器查询同时
        处理器线程=启动守护线程(跑处理器)#与版本查询同时
        版本线程.join()#等到版本
        处理器线程.join()#等到处理器
        版本结果=版本盒['值']#版本
        处理器结果=处理器盒['值']#处理器
        if 版本结果['kind']=='missing':#命令失败
            标记缺失(['os_version_full','os_build'],版本结果['reason'])#沿用命令原因
        else:#有输出
            解析=解码(版本结果['stdout'])#JSON
            版本对象=None#校验通过才有
            if isinstance(解析,dict) and 'major' in 解析 and 'minor' in 解析 and 'build' in 解析 and 'revision' in 解析:#四个键都在
                主=解析['major']#主版本
                次=解析['minor']#次版本
                构建号=解析['build']#构建
                修订=解析['revision']#修订
                主合法=主 is None or (isinstance(主,int) and not isinstance(主,bool) and 主>=0)#非负或空
                次合法=次 is None or (isinstance(次,int) and not isinstance(次,bool) and 次>=0)#非负或空
                构建合法=构建号 is None or (isinstance(构建号,str) and 数字模式.fullmatch(构建号) is not None)#数字或空
                修订合法=修订 is None or (isinstance(修订,int) and not isinstance(修订,bool) and 修订>=0)#非负或空
                if 主合法 and 次合法 and 构建合法 and 修订合法:#通过
                    版本对象={'major':主,'minor':次,'build':构建号,'revision':修订}#只留这四项
            if 版本对象 is None:#JSON 或字段不合法
                标记缺失(['os_version_full','os_build'],'invalid-value')#两项都无效
            else:#字段合法，空值仍然缺失
                if 版本对象['build'] is None:#没有构建号
                    标记缺失(['os_build'],'unavailable')#构建缺失
                else:#有构建号
                    字段['os_build']=版本对象['build']#收下
                if 版本对象['major'] is None or 版本对象['minor'] is None or 版本对象['build'] is None or 版本对象['revision'] is None:#凑不齐四段
                    标记缺失(['os_version_full'],'unavailable')#完整版本缺失
                else:#四段都在
                    字段['os_version_full']=str(版本对象['major'])+'.'+str(版本对象['minor'])+'.'+版本对象['build']+'.'+str(版本对象['revision'])#四段
        if 处理器结果['kind']=='missing':#命令失败
            标记缺失(['os_arch','cpu_physical_core_count'],处理器结果['reason'])#沿用命令原因
        else:#有输出
            解析=解码(处理器结果['stdout'])#JSON
            处理器列表=None#校验通过才有
            if isinstance(解析,list) and len(解析)>=1:#至少一个插座
                收成=[]#通过的项
                合法=True#任一项失败则整表无效
                for 项 in 解析:#逐个插座
                    if not isinstance(项,dict) or 'cores' not in 项 or 'architecture' not in 项:#缺键
                        合法=False#无效
                        break#停止
                    核数=项['cores']#物理核
                    架构=项['architecture']#架构编号
                    核合法=核数 is None or (isinstance(核数,int) and not isinstance(核数,bool) and 核数>0)#正整数或空
                    架构合法=架构 is None or (isinstance(架构,int) and not isinstance(架构,bool))#整数或空
                    if not 核合法 or not 架构合法:#类型不对
                        合法=False#无效
                        break#停止
                    收成.append({'cores':核数,'architecture':架构})#只留这两项
                if 合法:#整表通过
                    处理器列表=收成#可用
            if 处理器列表 is None:#无效
                标记缺失(['os_arch','cpu_physical_core_count'],'invalid-value')#两项都无效
            else:#字段类型通过
                核心列表=[项['cores'] for 项 in 处理器列表]#各插座核数
                if all(个数 is not None for 个数 in 核心列表):#没有空核数
                    def 合计核心():
                        '各插座物理核相加，不从逻辑核推断'
                        合计=0#从零加
                        for 个数 in 核心列表:#逐个插座
                            合计=合计+个数#累加
                        return 合计#总和
                    读取('cpu_physical_core_count',合计核心)#总和还要是正的安全整数
                else:#有插座没报告核数
                    标记缺失(['cpu_physical_core_count'],'unavailable')#不猜测
                架构=处理器列表[0]['architecture']#第一颗
                架构一致=all(项['architecture']==架构 for 项 in 处理器列表)#插座必须一致
                if 架构 is None or not 架构一致 or 架构 not in 架构名:#空、冲突或未知
                    标记缺失(['os_arch'],'unavailable')#不合并冲突架构
                else:#已知且一致
                    字段['os_arch']=架构名[架构]#原生架构
    elif 平台=='darwin':#macOS
        版本盒={}//sw_vers
        处理器盒={}//sysctl
        def 跑版本():
            '问产品版本和构建号'
            版本盒['值']=查询环境('/usr/bin/sw_vers',[],选项)#无参数
        def 跑处理器():
            '问物理核和是否 arm64'
            处理器盒['值']=查询环境('/usr/sbin/sysctl',['-i','hw.physicalcpu','hw.optional.arm64'],选项)#固定参数
        版本线程=启动守护线程(跑版本)#同时
        处理器线程=启动守护线程(跑处理器)#同时
        版本线程.join()#等到版本
        处理器线程.join()#等到处理器
        版本结果=版本盒['值']#版本
        处理器结果=处理器盒['值']#处理器
        if 版本结果['kind']=='missing':#命令失败
            标记缺失(['os_version_full','os_build'],版本结果['reason'])#沿用命令原因
        else:#有输出
            行表=拆行(版本结果['stdout'])#键值
            产品=行表.get('ProductVersion')#产品版本
            额外=行表.get('ProductVersionExtra') or None#空串当成没有
            匹配=None if 产品 is None else 产品版本模式.fullmatch(产品)#整行匹配
            额外合法=额外 is None or 额外版本模式.fullmatch(额外) is not None#后缀形态
            后缀一致=匹配 is None or 匹配.group(2) is None or 额外 is None or 匹配.group(2)==额外#两边不冲突
            if 产品 is not None and 匹配 is not None and 额外合法 and 后缀一致:#可以收下
                后缀=匹配.group(2) if 匹配.group(2) is not None else 额外#内联优先，否则用额外行
                if 后缀 is None:#没有后缀
                    字段['os_version_full']=产品#原产品版本
                else:#有后缀
                    字段['os_version_full']=匹配.group(1)+' '+后缀#数字部分加一个后缀
            else:#形态不对
                标记缺失(['os_version_full'],'invalid-value')#不收下
            构建=行表.get('BuildVersion')#构建号
            if 构建 is not None and 构建版本模式.fullmatch(构建) is not None:#形态对
                字段['os_build']=构建#收下
            else:#缺失或形态不对
                标记缺失(['os_build'],'invalid-value')#不收下
        if 处理器结果['kind']=='missing':#命令失败
            标记缺失(['os_arch','cpu_physical_core_count'],处理器结果['reason'])#沿用命令原因
        else:#有输出
            行表=拆行(处理器结果['stdout'])#键值
            核心文本=行表.get('hw.physicalcpu')#物理核
            if 核心文本 is not None and 数字模式.fullmatch(核心文本) is not None and 是否正安全整数(int(核心文本)):#正的安全整数
                字段['cpu_physical_core_count']=int(核心文本)#收下
            else:#缺失或不是正整数
                标记缺失(['cpu_physical_core_count'],'invalid-value')#不收下
            臂=行表.get('hw.optional.arm64')#是否 arm64
            if 臂=='1':#是
                字段['os_arch']='arm64'#原生 ARM
            elif 臂 is None or 臂=='0':#没有这项或明确不是
                字段['os_arch']='x64'#Intel
            else:#其他值
                标记缺失(['os_arch'],'invalid-value')#不猜测
    else:#其余平台不发命令
        标记缺失(['os_version_full','os_build','os_arch','cpu_physical_core_count'],'unsupported')#不支持
    return 字段#含失败字段的快照
