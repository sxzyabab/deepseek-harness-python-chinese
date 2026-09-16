import json,math,os,re,shutil,signal,socket,stat,subprocess,sys,tempfile,threading,time#子进程与帧泵
from ...依赖.schemastery import 数字字段,字符串字段,复合类型字段#配置
from ...ptc运行时.ptc运行时 import ptc运行时,保留绑定全局,保留错误成员,双下划线成员,可移植保留字#缝
from ...内核.会话 import 快照json值#无损快照
from ...内核.作用域 import 操作任务#结算
from ...工具.超时 import 定时器延迟上限毫秒,已中止,等待中止#中止与定时上限
from .协议 import (
    检查完成值,
    含不安全整数词,
    含非无损数字,
    编码json纯值,
    日志截断标记,
    校验子帧,
    协议文件描述符,
)

__all__=['python子进程ptc运行时','宿主帧解析上限','读进程启动','解析python可执行','分离残余',
    '检查完成值','编码json纯值','含非无损数字','含不安全整数词','日志截断标记','校验子帧']#仅中文公开名

标识=re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')#标识符
python脚本=('bootstrap.py','protocol.py')#须物化
帧解析上限字节=64*1024*1024#64 MiB
最大待块=1024#块数
最大待应答=1024#应答积压
帧信封字节=64#信封
最小日志字节=64#标记下限
关闭回收裕量毫秒=2000#close 兜底
输出预算最坏倍数=12#Unicode 峰值
解释器基线字节=64*1024*1024#解释器
宿主解析最坏倍数=16#JSON.parse 峰值
宿主解析基线字节=64*1024*1024#应用
组回收轮询毫秒=50#空组探测
最低cpython=(3,10)#最低版本
python探测超时毫秒=5000#探测
截断标记='… [truncated]'#诊断截断
截断标记字节=len(截断标记.encode('utf-8'))#15
默认堆上限=4*1024*1024*1024#无 V8 时约 4GiB

def 宿主帧解析上限(堆上限=None):#有效帧帽
    """协议帽与堆推导帽取小。"""
    if 堆上限 is None:#缺省
        堆上限=默认堆上限#4GiB
    return min(帧解析上限字节,math.floor((堆上限-宿主解析基线字节)/宿主解析最坏倍数))#帽

def 消息于(错误):#安全渲染
    """未知抛值的英文消息。"""
    try:#渲染
        if isinstance(错误,BaseException):#异常
            return str(错误)#消息
        return str(错误)#字面
    except Exception:#不可渲染
        return '<unrenderable rejection value>'#占位

def 读进程启动(pid):#身份半边
    """Linux /proc 启动时刻；其余平台空。"""
    if sys.platform!='linux':#非 Linux
        return None#空
    try:#读
        with open('/proc/'+str(pid)+'/stat','r',encoding='utf-8') as 文件:#stat
            文=文件.read()#原文
        字段=文[文.rfind(')')+2:].split(' ')#去 comm
        return 字段[19]#starttime
    except Exception:#失败
        return None#空

def 解析python可执行(命令):#解析绝对路径
    """basename 搜 PATH；相对对加载 cwd。"""
    def 可执行文件(候选):#X_OK 普通文件
        """可执行普通文件则返回路径。"""
        try:#查
            if os.access(候选,os.X_OK) and stat.S_ISREG(os.stat(候选).st_mode):#可执行文件
                return 候选#路径
        except Exception:#错过
            return None#空
        return None#空
    if os.path.isabs(命令):#绝对
        return 可执行文件(命令)#就地
    if '/' in 命令 or (os.sep!='/' and os.sep in 命令):#相对
        return 可执行文件(os.path.abspath(命令))#相对
    路径=os.environ.get('PATH')#PATH
    if 路径 is None:#无
        return None#空
    for 目录 in 路径.split(os.pathsep):#逐段
        if 目录=='' or not os.path.isabs(目录):#跳相对
            continue#下
        命中=可执行文件(os.path.join(目录,命令))#候选
        if 命中 is not None:#命中
            return 命中#路径
    return None#空

def python环境():#子环境
    """只暴露 TMPDIR。"""
    return {'TMPDIR':tempfile.gettempdir()}#环境

def 校验python可执行(路径):#探测版本
    """须为响应的 CPython 3.10+。"""
    try:#探测
        输出=subprocess.check_output([路径,'-I','-c','import sys; print(sys.implementation.name, sys.version_info.major, sys.version_info.minor, sys.version_info.micro)'],env=python环境(),timeout=python探测超时毫秒/1000,stderr=subprocess.STDOUT).decode('utf-8').strip()#探测
    except Exception as 错误:#失败
        raise Exception('dsh-ptc-runtime-python: config.pythonBin '+json.dumps(路径)+' failed the CPython version probe: '+消息于(错误))#失败
    匹配=re.fullmatch(r'(\S+) (\d+) (\d+) (\d+)',输出)#版本行
    if 匹配 is None:#畸形
        raise Exception('dsh-ptc-runtime-python: config.pythonBin '+json.dumps(路径)+' did not report a CPython version')#失败
    实现,主文,次文,补文=匹配.group(1),匹配.group(2),匹配.group(3),匹配.group(4)#拆
    主,次=int(主文),int(次文)#数
    if 实现!='cpython':#非 CPython
        raise Exception('dsh-ptc-runtime-python: config.pythonBin '+json.dumps(路径)+' must be CPython, got '+实现)#失败
    if 主<最低cpython[0] or (主==最低cpython[0] and 次<最低cpython[1]):#过低
        raise Exception('dsh-ptc-runtime-python: config.pythonBin '+json.dumps(路径)+' must be CPython '+str(最低cpython[0])+'.'+str(最低cpython[1])+' or newer, got '+实现+' '+主文+'.'+次文+'.'+补文)#失败

def 物化python脚本():#每跑一份
    """把 子/ 脚本拷到真实临时目录，返回入口路径。"""
    目录=tempfile.mkdtemp(prefix='dsh-ptc-runtime-python-')#目录
    源=os.path.join(os.path.dirname(os.path.abspath(__file__)),'子')#源
    try:#拷
        for 名 in python脚本:#逐文件
            shutil.copyfile(os.path.join(源,名),os.path.join(目录,名))#拷
    except Exception as 错误:#失败
        try:#清
            shutil.rmtree(目录,ignore_errors=True)#删
        except Exception:#忽略
            pass#忽略
        raise 错误#原样
    os.chmod(目录,0o700)#私有
    return os.path.join(目录,'bootstrap.py')#入口

def 分离残余(残余):#拷走视图
    """把残余拷成独立 bytes，避免钉住大缓冲。"""
    if len(残余)>0:#有
        return [bytes(残余)]#拷
    return []#空

def 序列化字符代价(码,字符):#一字代价
    """一字的 JSON 转义 UTF-8 宽。"""
    if 码<0x20:#C0
        return 2 if 码 in (0x08,0x09,0x0a,0x0c,0x0d) else 6#短或长
    if 码 in (0x22,0x5c):#引号反斜
        return 2#转义
    if 0xd800<=码<=0xdfff:#孤代理
        return 6#转义
    return len(字符.encode('utf-8'))#原文

def json串代价上限(文本,最大字节):#不物化转义
    """JSON 串代价，一超即停。"""
    if 最大字节<2:#不够引号
        return None#超
    字节=2#引号
    for 字符 in 文本:#逐字
        字节+=序列化字符代价(ord(字符),字符)#代价
        if 字节>最大字节:#超
            return None#超
    return 字节#代价

def 累加杂散代价(缓冲,状态):#UTF-8 计费
    """按 WHATWG 替换计杂散字节的 JSON 代价。状态就地改。"""
    代价=0#累计
    下标=0#扫描
    长=len(缓冲)#长
    while 下标<长:#逐字节
        字节=缓冲[下标]#字节
        if 状态['expected']>0:#续
            已=状态['width']-状态['expected']#已耗
            下界=状态['lowerFirst'] if 已==1 else 0x80#下
            上界=状态['upperFirst'] if 已==1 else 0xbf#上
            if 下界<=字节<=上界:#合法续
                状态['expected']-=1#减
                if 状态['expected']==0:#成
                    代价+=状态['width']#宽
                    状态['width']=0#清
                下标+=1#前
                continue#下
            代价+=3#折成一枚 U+FFFD
            状态['expected']=0#清
            状态['width']=0#清
            continue#重看本字节
        if 字节<0x20:#控制
            代价+=2 if 字节 in (0x08,0x09,0x0a,0x0c,0x0d) else 6#短或长
        elif 字节 in (0x22,0x5c):#引号反斜
            代价+=2#转义
        elif 字节<0x80:#ASCII
            代价+=1#一
        elif 0xc2<=字节<=0xdf:#两字节
            状态['expected']=1#续
            状态['width']=2#宽
            状态['lowerFirst']=0x80#下
            状态['upperFirst']=0xbf#上
        elif 0xe0<=字节<=0xef:#三字节
            状态['expected']=2#续
            状态['width']=3#宽
            状态['lowerFirst']=0xa0 if 字节==0xe0 else 0x80#下
            状态['upperFirst']=0x9f if 字节==0xed else 0xbf#上
        elif 0xf0<=字节<=0xf4:#四字节
            状态['expected']=3#续
            状态['width']=4#宽
            状态['lowerFirst']=0x90 if 字节==0xf0 else 0x80#下
            状态['upperFirst']=0x8f if 字节==0xf4 else 0xbf#上
        else:#非法首
            代价+=3#U+FFFD
        下标+=1#前
    return 代价#代价

def 截消息(消息,最大字节):#原始字节帽
    """按 UTF-8 字节截断 done.error.message。"""
    if len(消息.encode('utf-8'))<=最大字节 and len(消息)*3<=最大字节:#必入
        return 消息#原样
    留=min(len(消息),最大字节)#码点上限
    整=留==len(消息)#是否全文
    字节=消息[:留].encode('utf-8')#编码
    if 整 and len(字节)<=最大字节:#全文且入
        return 消息#原样
    预算=max(0,最大字节-截断标记字节)#留给正文
    尾=min(预算,len(字节))#切
    while 尾>0 and (字节[尾-1] if 尾==len(字节) else 字节[尾])&0b11000000==0b10000000:#续字节
        尾-=1#回
        if 尾<len(字节) and (字节[尾]&0b11000000)==0b10000000:#仍续
            continue#再
        break#停
    while 尾>0 and (字节[尾-1]&0b11000000)==0b10000000:#回落到首
        尾-=1#回
    return 字节[:尾].decode('utf-8','strict')+截断标记#截

配置=复合类型字段({#加载期校验另做
    'cpuSeconds':数字字段(默认值=60),#CPU
    'maxWallMs':数字字段(默认值=600000),#墙钟
    'addressSpaceMb':数字字段(默认值=512),#地址空间
    'maxLogBytes':数字字段(默认值=65536),#日志
    'maxValueBytes':数字字段(默认值=32768),#完成值
    'graceMs':数字字段(默认值=3000),#宽限
    'pythonBin':字符串字段(默认值='python3'),#解释器
})#配置结束

class python子进程ptc运行时(ptc运行时):#CPython 子进程后端
    """每次请求一个全新 CPython 子进程；fd 3 JSON-lines。"""
    Config=配置#框架槽
    def __init__(自身,上下文,配置值=None):#加载校验
        """Unix 平台；拒绝非法预算。"""
        super().__init__(上下文)#登记 ptcRuntime
        if sys.platform=='win32':#Windows
            raise Exception('dsh-ptc-runtime-python: this backend requires a Unix platform (POSIX rlimits, fd-3 stdio, process-group signals); it cannot run on Windows')#失败
        值=dict(配置值 or {})#副本
        for 键,缺 in (('cpuSeconds',60),('maxWallMs',600000),('addressSpaceMb',512),('maxLogBytes',65536),('maxValueBytes',32768),('graceMs',3000),('pythonBin','python3')):#缺省
            if 值.get(键) is None:#缺
                值[键]=缺#填
        自身.配置=值#记下
        for 键,项 in 值.items():#正数
            if isinstance(项,(int,float)) and not isinstance(项,bool) and not (math.isfinite(项) and 项>0):#非正
                raise Exception('dsh-ptc-runtime-python: config.'+键+' must be a positive number, got '+str(项))#失败
        if not isinstance(值['cpuSeconds'],int) or isinstance(值['cpuSeconds'],bool):#非整数
            raise Exception('dsh-ptc-runtime-python: config.cpuSeconds must be a positive integer, got '+str(值['cpuSeconds']))#失败
        if abs(值['cpuSeconds']+1)>9007199254740991:#超安全
            raise Exception('dsh-ptc-runtime-python: config.cpuSeconds must be at most '+str(9007199254740991-1)+' (it and its +1 hard limit cross to setrlimit as exact integers), got '+str(值['cpuSeconds']))#失败
        if abs(值['addressSpaceMb']*1024*1024)>9007199254740991:#超安全
            raise Exception('dsh-ptc-runtime-python: config.addressSpaceMb must be at most '+str(9007199254740991//(1024*1024))+' (its byte count crosses the wire as an exact integer), got '+str(值['addressSpaceMb']))#失败
        if 值['pythonBin']=='' or '\0' in 值['pythonBin']:#空或 NUL
            raise Exception('dsh-ptc-runtime-python: config.pythonBin must be a non-empty path without NUL bytes, got '+json.dumps(值['pythonBin']))#失败
        if 值['maxWallMs']>定时器延迟上限毫秒:#定时器会钳
            raise Exception('dsh-ptc-runtime-python: config.maxWallMs must not exceed '+str(定时器延迟上限毫秒)+' (setTimeout clamps a larger delay to 1ms), got '+str(值['maxWallMs']))#失败
        if 值['graceMs']+关闭回收裕量毫秒>定时器延迟上限毫秒:#截止
            raise Exception('dsh-ptc-runtime-python: config.graceMs must not exceed '+str(定时器延迟上限毫秒-关闭回收裕量毫秒)+' (its close deadline adds '+str(关闭回收裕量毫秒)+'ms, and setTimeout clamps a larger delay to 1ms), got '+str(值['graceMs']))#失败
        自身.帧解析帽=宿主帧解析上限()#本实例
        for 键 in ('maxLogBytes','maxValueBytes'):#整数预算
            if not isinstance(值[键],int) or isinstance(值[键],bool):#非整数
                raise Exception('dsh-ptc-runtime-python: config.'+键+' must be a positive integer (the child reads it as an int, so a float diverges from the host), got '+str(值[键]))#失败
            限=自身.帧解析帽-帧信封字节#可载
            if 值[键]>限:#超帧
                堆注=''#注
                if 自身.帧解析帽<帧解析上限字节:#堆约束
                    堆注=" — this host's heap limits the parse to "+str(自身.帧解析帽)+' bytes, so the protocol cap of '+str(帧解析上限字节)+' would be unsafe'#注
                raise Exception('dsh-ptc-runtime-python: config.'+键+' must not exceed '+str(限)+' (a payload that large cannot cross the fd-3 frame PARSER, which rejects raw frames past '+str(自身.帧解析帽)+' bytes before decoding to bound host memory'+堆注+' — a larger budget would admit a config whose honest child frames the host then rejects as a worker-exit), got '+str(值[键]))#失败
            if 键=='maxLogBytes' and 值[键]<最小日志字节:#过小
                raise Exception('dsh-ptc-runtime-python: config.maxLogBytes must be at least '+str(最小日志字节)+' (a smaller budget cannot serialize the truncation marker itself, so a marker-only truncated run would return more than the configured cap), got '+str(值[键]))#失败
        地址字节=值['addressSpaceMb']*1024*1024#AS
        可预算=地址字节-解释器基线字节#剩余
        if 可预算<=0:#基线不够
            raise Exception('dsh-ptc-runtime-python: config.addressSpaceMb must exceed the '+str(解释器基线字节)+'-byte interpreter baseline with room for the output budgets, so the child has address space left to build and encode them; got '+str(值['addressSpaceMb'])+' MiB ('+str(地址字节)+' bytes)')#失败
        可纳=math.ceil(可预算/输出预算最坏倍数)-1#上限
        for 键 in ('maxLogBytes','maxValueBytes'):#对 AS
            if 值[键]*输出预算最坏倍数>=可预算:#会破 AS
                raise Exception('dsh-ptc-runtime-python: config.'+键+' times the '+str(输出预算最坏倍数)+'x worst-case Unicode expansion must fit within the '+str(可预算)+' bytes left after the '+str(解释器基线字节)+'-byte interpreter baseline within the '+str(地址字节)+'-byte addressSpaceMb, so a near-budget output truncates rather than breaching RLIMIT_AS as worker-exit; got '+str(值[键])+' against a limit of '+str(可纳))#失败
        解释器=解析python可执行(值['pythonBin'])#解析
        if 解释器 is None:#找不到
            显式=os.path.isabs(值['pythonBin']) or '/' in 值['pythonBin']#显式路径
            raise Exception('dsh-ptc-runtime-python: config.pythonBin '+json.dumps(值['pythonBin'])+' '+('is not an executable regular file' if 显式 else 'does not resolve on PATH'))#失败
        校验python可执行(解释器)#探测
        自身.python可执行=解释器#固定
        自身.在途=set()#活运行
        自身.已拆=False#拆除
        def 拆除寿命():#fiber 拆
            """等全部子退出。"""
            def 卸():#拆
                """中止在途。"""
                自身.拆除()#拆
            return 卸#拆除器
        上下文.副作用(拆除寿命,'python ptc-runtime teardown')#挂

    def 语言(自身):#源语言
        """python。"""
        return 'python'#语言

    def 隔离(自身):#基底
        """process。"""
        return 'process'#隔离

    def 拆除(自身):#静默
        """在途标 abort 并等退出。"""
        自身.已拆=True#记下
        表=list(自身.在途)#快照
        for 项 in 表:#逐项
            项['settle']({'kind':'abort','message':'runtime disposed'})#中止
        for 项 in 表:#等
            项['finished'].等待()#等

    def 解析(自身,请求):#填 cwd 与墙钟
        """不支持沙箱与逐次超时。"""
        if 请求.get('sandboxPolicy') is not None:#沙箱
            raise Exception('dsh-ptc-runtime-python: sandbox policy is unsupported')#失败
        if 请求.get('timeoutMs') is not None:#覆盖
            raise Exception('dsh-ptc-runtime-python: per-call timeout is unsupported')#失败
        目录=请求.get('cwd')#cwd
        if 目录 is None:#缺
            目录=os.getcwd()#cwd
        if not os.path.isabs(目录):#相对
            raise Exception('dsh-ptc-runtime-python: cwd must be absolute')#失败
        规格=dict(请求)#副本
        规格['cwd']=目录#绝对
        规格['timeoutMs']=自身.配置['maxWallMs']#墙钟
        return 规格#规格

    def 运行(自身,请求):#一次程序
        """无文件围栏。"""
        if 请求.get('sandboxPolicy') is not None or 请求.get('timeoutMs')!=自身.配置['maxWallMs']:#政策
            raise Exception('dsh-ptc-runtime-python: unsupported execution policy or timeout')#失败
        if 自身.已拆:#已拆
            raise Exception('dsh-ptc-runtime-python: run() after disposal')#失败
        绑定=自身.校验绑定(请求)#绑定
        if 已中止(请求.get('signal')):#已中止
            return {'logs':[],'error':{'kind':'abort','message':消息于(getattr(请求.get('signal'),'reason',None))}}#中止
        try:#物化
            入口=物化python脚本()#入口
        except Exception as 错误:#失败
            return {'logs':[],'error':{'kind':'worker-exit','message':'failed to stage the python bootstrap: '+消息于(错误)}}#基底
        return 自身.执行(请求,绑定,入口)#跑

    def 校验绑定(自身,请求):#缝误用
        """拒绝非法命名空间。"""
        绑定={}#名 → 记录
        注入=set()#已占全局
        def 占全局(名,角色):#占
            """运行时槽与重复。"""
            if 名 in 保留绑定全局:#槽
                raise Exception('dsh-ptc-runtime-python: '+角色+' '+json.dumps(名)+' collides with a runtime-owned global')#失败
            if 名 in 注入:#重
                raise Exception('dsh-ptc-runtime-python: '+角色+' '+json.dumps(名)+' collides with another injected global')#失败
            注入.add(名)#占
        for 空间 in 请求.get('bindings') or ():#逐空间
            全局=空间['global']#名
            if not 标识.fullmatch(全局) or 全局 in 可移植保留字:#非法
                raise Exception('dsh-ptc-runtime-python: binding global '+json.dumps(全局)+' is not a usable Python identifier')#失败
            if 全局 in 绑定:#重复
                raise Exception('dsh-ptc-runtime-python: duplicate binding global '+json.dumps(全局))#失败
            占全局(全局,'binding global')#占
            错类=空间.get('errorClass')#错误类
            已校错=None#可选
            if 错类:#有
                名=错类['name']#名
                成员=错类['memberNameProperty']#成员
                if not 标识.fullmatch(名) or 名 in 可移植保留字:#非法
                    raise Exception('dsh-ptc-runtime-python: errorClass.name '+json.dumps(名)+' is not a usable Python identifier')#失败
                if len(成员)==0:#空
                    raise Exception('dsh-ptc-runtime-python: errorClass.memberNameProperty must be a non-empty attribute name')#失败
                if 成员 in 保留错误成员 or 双下划线成员.match(成员):#保留
                    raise Exception('dsh-ptc-runtime-python: errorClass.memberNameProperty '+json.dumps(成员)+' is a reserved error member and cannot be assigned')#失败
                占全局(名,'errorClass.name')#占
                已校错={'name':名,'memberNameProperty':成员}#记下
            函数={}#可调用快照
            源函数=空间.get('functions') or {}#源
            for 名 in 源函数:#逐名
                函=源函数[名]#值
                if callable(函):#可调用
                    函数[名]=函#记下
            记录={'functions':函数}#记录
            if 已校错 is not None:#错误类
                记录['errorClass']=已校错#记下
            绑定[全局]=记录#挂
        return 绑定#表

    def 执行(自身,请求,绑定,入口):#驱动到结算
        """spawn 并泵帧。"""
        引导目录=os.path.dirname(入口)#staging
        宿主套,子套=socket.socketpair()#双向 fd 3
        try:#spawn
            def 子预():#子进程预
                """把子套接到 fd 3。"""
                os.dup2(子套.fileno(),协议文件描述符)#fd 3
                子套.close()#关原
                宿主套.close()#子不要宿主端
            子=subprocess.Popen([自身.python可执行,'-u','-I',入口],cwd=请求['cwd'],env=python环境(),stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,preexec_fn=子预,start_new_session=True)#组
            子套.close()#宿主只留宿主套
        except Exception as 错误:#spawn 同步失败
            try:#清
                shutil.rmtree(引导目录,ignore_errors=True)#删
            except Exception:#忽略
                pass#忽略
            try:#关套
                宿主套.close()#关
                子套.close()#关
            except Exception:#忽略
                pass#忽略
            return {'logs':[],'error':{'kind':'worker-exit','message':'python spawn error: '+消息于(错误)}}#基底
        结局=操作任务()#run 结果
        def 体():#泵
            """驱动到结算。"""
            自身._泵(请求,绑定,子,宿主套,引导目录,结局)#泵
        threading.Thread(target=体,daemon=True).start()#泵
        return 结局.等待()#阻塞

    def _泵(自身,请求,绑定,子,宿主套,引导目录,结局):#一跑泵
        """fd-3 与杂散捕获。"""
        已结算=[False]#settled
        已兑现=[False]#resolved
        日志=[]#logs
        开片段=[]#openParts
        开封=[]#openSealed
        日志预算=[自身.配置['maxLogBytes']-1]#账本
        日志已截=[False]#truncated
        空utf8={'expected':0,'width':0,'lowerFirst':0,'upperFirst':0}#UTF-8
        杂出={'chunks':[],'blocks':[],'cost':0,'utf8':dict(空utf8)}#stdout
        杂错={'chunks':[],'blocks':[],'cost':0,'utf8':dict(空utf8)}#stderr
        待块=[]#pendingChunks
        封块=[]#sealedBlocks
        待字节=[0]#pendingBytes
        下一调用号=[0]#nextCallId
        启动门={'run':None}#boot-ack
        应答队列=[]#replyQueue
        待应答=[0]#pendingReplies
        待调用=[0]#pendingCalls
        抽检挂=[False]#postBatch
        排空中=[False]#draining
        正在杀=[False]#killing
        宽限定时=[None]#graceTimer
        关闭截止=[None]#closeDeadline
        决定=[None]#decided
        活项=[None]#live
        完成任务=操作任务()#finished
        墙定时=[None]#墙钟
        协议锁=threading.Lock()#写锁
        def 清杂散(杂):#丢缓冲
            """截断后丢掉管道缓冲。"""
            杂['chunks']=[]#清
            杂['blocks']=[]#清
            杂['cost']=0#清
            杂['utf8']=dict(空utf8)#清
        def 截日志():#账本截断
            """提交开行再追加标记。"""
            日志已截[0]=True#记下
            if len(开封)>0 or len(开片段)>0:#有开
                日志.append(''.join(开封)+''.join(开片段))#提交
                开封.clear()#清
                开片段.clear()#清
            日志.append(日志截断标记(自身.配置['maxLogBytes']))#标记
            清杂散(杂出)#清
            清杂散(杂错)#清
        def 准入(文本):#一条
            """按序列化代价记账。"""
            if 日志已截[0]:#已截
                return#停
            if len(文本)+3>日志预算[0]:#下界
                截日志()#截
                return#停
            测=json串代价上限(文本,日志预算[0]-1)#精确
            if 测 is None:#超
                截日志()#截
                return#停
            日志预算[0]-=测+1#扣
            日志.append(文本)#记
        def 冲杂散(杂,留尾=False):#冲残余
            """把管道残余写入 logs。"""
            if len(杂['chunks'])==0 and len(杂['blocks'])==0:#空
                return#停
            全=b''.join(杂['blocks']+杂['chunks'])#拼接
            if 留尾 and 杂['utf8']['expected']>0:#留未完成序列
                丢=min(杂['utf8']['width']-杂['utf8']['expected'],len(全))#尾
                留=全[len(全)-丢:]#尾
                全=全[:len(全)-丢]#前
                杂['chunks']=分离残余(留)#带走
                杂['utf8']=dict(空utf8)#新
                杂['cost']=累加杂散代价(留,杂['utf8'])#再计
                杂['blocks']=[]#清
                if len(全)>0:#有完整
                    准入(全.decode('utf-8','replace'))#准入
                return#停
            杂['chunks']=[]#清
            杂['cost']=0#清
            杂['utf8']=dict(空utf8)#清
            杂['blocks']=[]#清
            准入(全.decode('utf-8','replace'))#准入
        def 捕杂散(杂,块):#stdout/stderr
            """按行准入杂散。"""
            if 日志已截[0]:#已截
                return#停
            杂['chunks'].append(块)#块
            杂['cost']+=累加杂散代价(块,杂['utf8'])#计
            if len(杂['chunks'])>=最大待块:#封
                杂['blocks'].append(b''.join(杂['chunks']))#封
                杂['chunks']=[]#清
            if 10 in 块:#有换行
                缓冲=b''.join(杂['blocks']+杂['chunks'])#拼
                杂['blocks']=[]#清
                while True:#切行
                    位=缓冲.find(b'\n')#换行
                    if 位<0:#无
                        break#停
                    准入(缓冲[:位].decode('utf-8','replace'))#行
                    缓冲=缓冲[位+1:]#余
                if 日志已截[0]:#已截
                    return#停
                杂['chunks']=分离残余(缓冲)#余
                杂['utf8']=dict(空utf8)#新
                杂['cost']=累加杂散代价(缓冲,杂['utf8'])#再计
            if 杂出['cost']+杂错['cost']+3>日志预算[0]:#合计超
                冲杂散(杂出,True)#冲
                冲杂散(杂错,True)#冲
        def 组空():#组是否空
            """killpg 探测。"""
            if 子.pid is None:#无
                return True#空
            try:#探
                os.killpg(子.pid,0)#探
                return False#有
            except OSError as 错误:#失败
                return getattr(错误,'errno',None)==getattr(os,'ESRCH',3)#ESRCH
        领袖启动=读进程启动(子.pid) if 子.pid is not None else None#身份
        def 杀组(信号值):#杀组
            """负 pid 组信号。"""
            try:#杀
                if 子.pid is None:#无
                    return#停
                现在=读进程启动(子.pid)#现在
                if 领袖启动 is not None and 现在 is not None and 现在!=领袖启动:#复用
                    return#拒
                os.killpg(子.pid,信号值)#杀
            except OSError:#ESRCH
                pass#已死
        def 杀():#升级
            """SIGTERM 再 SIGKILL。"""
            if 正在杀[0]:#已
                return#停
            正在杀[0]=True#记下
            杀组(signal.SIGTERM)#TERM
            def 到期杀():#宽限后
                """SIGKILL。"""
                杀组(signal.SIGKILL)#KILL
            定时=threading.Timer(自身.配置['graceMs']/1000,到期杀)#宽限
            定时.daemon=True#守护
            定时.start()#开
            宽限定时[0]=定时#记下
        def 结算(结果):#唯一结算点
            """兑现 run 并等组空。"""
            if 已兑现[0]:#已
                return#停
            已兑现[0]=True#记下
            if 关闭截止[0] is not None:#有截止
                关闭截止[0].cancel()#取消
            try:#删 staging
                shutil.rmtree(引导目录,ignore_errors=True)#删
            except Exception:#忽略
                pass#忽略
            结局.兑现({**结果,'logs':list(日志)})#兑现
            def 收尾():#出 live
                """从在途摘除。"""
                if 活项[0] is not None:#有
                    自身.在途.discard(活项[0])#摘
                try:#完成
                    完成任务.兑现(None)#完成
                except Exception:#已
                    pass#忽略
            if (not 正在杀[0]) or 组空():#无需等
                if 宽限定时[0] is not None:#有
                    宽限定时[0].cancel()#取消
                收尾()#收
                return#停
            截止=time.time()*1000+自身.配置['graceMs']+关闭回收裕量毫秒#截止
            硬=[0]#硬限
            def 轮询():#等组空
                """轮询组。"""
                if 组空():#空
                    if 宽限定时[0] is not None:#有
                        宽限定时[0].cancel()#取消
                    收尾()#收
                    return#停
                现在=time.time()*1000#现在
                if 硬[0]==0 and 现在>=截止:#到
                    杀组(signal.SIGKILL)#KILL
                    if 宽限定时[0] is not None:#有
                        宽限定时[0].cancel()#取消
                    硬[0]=现在+关闭回收裕量毫秒#再等
                if 硬[0]!=0 and 现在>=硬[0]:#硬
                    收尾()#收
                    return#停
                threading.Timer(组回收轮询毫秒/1000,轮询).start()#再
            轮询()#开
        def 完成(结果):#决定结局
            """杀组，等 close。"""
            if 已结算[0]:#已
                return#停
            已结算[0]=True#记下
            决定[0]=结果#记下
            if 墙定时[0] is not None:#墙钟
                墙定时[0].cancel()#取消
            if len(开封)>0 or len(开片段)>0:#开行
                日志.append(''.join(开封)+''.join(开片段))#提交
            开封.clear()#清
            开片段.clear()#清
            if 子.pid is None:#无 pid
                结算(结果)#即结
                return#停
            杀()#升级
            def 到截止():#孤儿兜底
                """拆流强制结算。"""
                冲杂散(杂出)#冲
                冲杂散(杂错)#冲
                try:#关协议
                    宿主套.close()#关
                except Exception:#忽略
                    pass#忽略
                for 流 in (子.stdout,子.stderr):#流
                    if 流 is not None:#有
                        try:#关
                            流.close()#关
                        except Exception:#忽略
                            pass#忽略
                结算(结果)#结
            定时=threading.Timer((自身.配置['graceMs']+关闭回收裕量毫秒)/1000,到截止)#截止
            定时.daemon=True#守护
            定时.start()#开
            关闭截止[0]=定时#记下
        def 排空应答():#写应答
            """一次一帧。"""
            if 排空中[0]:#已
                return#停
            排空中[0]=True#进
            头=0#头
            try:#写
                while 头<len(应答队列):#还有
                    if 已结算[0]:#已结
                        break#停
                    载荷=应答队列[头]#帧
                    应答队列[头]=None#放
                    头+=1#进
                    待应答[0]-=1#减
                    if 头>=最大待应答:#压缩
                        del 应答队列[:头]#切
                        头=0#重置
                    行=(编码json纯值(载荷)+'\n').encode('utf-8')#行
                    with 协议锁:#锁
                        宿主套.sendall(行)#写
            except Exception:#管道关
                pass#close 结算
            finally:#出
                排空中[0]=False#出
                待应答[0]=0#清
                应答队列.clear()#清
        def 发应答(载荷):#排队
            """积压上限。"""
            if 已结算[0]:#已
                return#停
            if 待应答[0]>=最大待应答:#满
                完成({'error':{'kind':'worker-exit','message':'reply queue exceeded '+str(最大待应答)+' pending frames on fd 3 (the child stopped consuming its replies)'}})#满
                return#停
            待应答[0]+=1#加
            应答队列.append(载荷)#排
            排空应答()#排
        def 处理帧(消息):#一帧
            """boot-ack/log/done/call。"""
            if 已结算[0]:#已
                return#停
            种=消息['type']#种
            if 种=='boot-ack':#应答
                跑=启动门.get('run')#跑
                if 跑 is not None:#有
                    跑()#发 run
                return#停
            if 种=='log':#日志
                if 消息.get('truncated') is True:#子截断
                    if not 日志已截[0]:#尚未
                        截日志()#截
                    return#停
                if 消息.get('open') is True:#未结束
                    if not 日志已截[0]:#未截
                        帽=日志预算[0]-1 if len(开片段)==0 else 日志预算[0]+2#帽
                        代价=json串代价上限(消息['text'],帽)#代价
                        if 代价 is None:#超
                            截日志()#截
                        else:#记
                            账=代价+1 if len(开片段)==0 else max(代价-2,0)#账
                            日志预算[0]-=账#扣
                            if 消息['text']!='':#非空
                                if len(开片段)>=最大待块:#封
                                    开封.append(''.join(开片段))#封
                                    开片段.clear()#清
                                开片段.append(消息['text'])#持
                    return#停
                if len(开片段)>0 or len(开封)>0:#闭开行
                    if not 日志已截[0]:#未截
                        代价=json串代价上限(消息['text'],日志预算[0]+2)#代价
                        if 代价 is None:#超
                            截日志()#截
                        else:#合
                            日志预算[0]-=max(代价-2,0)#扣
                            日志.append(''.join(开封)+''.join(开片段)+消息['text'])#合
                    开封.clear()#清
                    开片段.clear()#清
                    return#停
                准入(消息['text'])#普通
                return#停
            if 种=='done':#完成
                if 待调用[0]>最大待应答:#积压
                    完成({'error':{'kind':'worker-exit','message':'call backlog exceeded '+str(最大待应答)+' in-flight binding calls (a binding never settled)'}})#满
                    return#停
                if 消息.get('error') is not None:#有错
                    错=消息['error']#错
                    完成({'error':{'kind':错['kind'],'message':截消息(错['message'],自身.配置['maxValueBytes'])}})#错
                    return#停
                if 'value' not in 消息:#无值
                    完成({})#空
                    return#停
                查=检查完成值(消息['value'],自身.配置['maxValueBytes'])#查
                if not 查['ok']:#失败
                    if 查['reason']=='over-budget':#超
                        完成({'error':{'kind':'output-limit','message':'completion value exceeded '+str(自身.配置['maxValueBytes'])+' bytes'}})#超
                    else:#非无损
                        完成({'error':{'kind':'invalid-output','message':'completion value contained a non-lossless number'}})#非无损
                    return#停
                完成({'value':消息['value']})#值
                return#停
            if 种=='call':#调用
                if 消息['id']!=下一调用号[0]:#非后继
                    return#丢
                下一调用号[0]+=1#进
                记录=绑定.get(消息['global'],{}).get('functions')#函数表
                函=记录.get(消息['name']) if isinstance(记录,dict) and 消息['name'] in 记录 else None#函数
                if not callable(函):#未知
                    帽=自身.配置['maxValueBytes']#帽
                    目标=消息['global'][:帽]+'.'+消息['name'][:帽]#目标
                    预览=json.dumps(目标[:1024],ensure_ascii=False)#预览
                    发应答({'type':'reply','id':消息['id'],'ok':False,'message':截消息('unknown binding '+预览,帽)})#未知
                    return#停
                待调用[0]+=1#在途
                def 调体(函数=函,帧=消息):#线程
                    """跑绑定。"""
                    try:#调
                        解析=函数(帧['args'])#调
                        if 已结算[0]:#已结
                            return#停
                        值=快照json值(解析)#快照
                        if 值 is None:#非无损
                            发应答({'type':'reply','id':帧['id'],'ok':False,'message':'binding resolution must be lossless JSON'})#失败
                            return#停
                        发应答({'type':'reply','id':帧['id'],'ok':True,'value':值})#成功
                    except Exception as 错误:#失败
                        if 已结算[0]:#已结
                            return#停
                        发应答({'type':'reply','id':帧['id'],'ok':False,'message':消息于(错误)})#失败
                    finally:#放槽
                        待调用[0]-=1#减
                threading.Thread(target=调体,daemon=True).start()#调
                return#停
        def 处理协议块(块):#fd 3
            """按行解析。"""
            if 已结算[0]:#已
                return#停
            if not 抽检挂[0]:#安排抽检
                抽检挂[0]=True#挂
                def 抽检():#后检
                    """在途调用上限。"""
                    抽检挂[0]=False#清
                    if 已结算[0]:#已
                        return#停
                    if 待调用[0]>最大待应答:#超
                        完成({'error':{'kind':'worker-exit','message':'call backlog exceeded '+str(最大待应答)+' in-flight binding calls (a binding never settled)'}})#满
                threading.Timer(0,抽检).start()#尽快
            待块.append(块)#块
            待字节[0]+=len(块)#字节
            if 待字节[0]>自身.帧解析帽 and 10 not in 块:#无换行超帽
                待块.clear()#清
                封块.clear()#清
                待字节[0]=0#清
                完成({'error':{'kind':'worker-exit','message':'protocol frame exceeded '+str(自身.帧解析帽)+' bytes on fd 3'}})#超
                return#停
            if 10 in 块:#有换行
                首长=0#首帧
                见换=False#见
                for 乙 in 封块:#封
                    首长+=len(乙)#加
                for 丙 in 待块:#待
                    位=丙.find(b'\n')#换行
                    if 位>=0:#见
                        首长+=位#加
                        见换=True#见
                        break#停
                    首长+=len(丙)#加
                if 见换 and 首长>自身.帧解析帽:#首超
                    待块.clear()#清
                    封块.clear()#清
                    待字节[0]=0#清
                    完成({'error':{'kind':'worker-exit','message':'protocol frame exceeded '+str(自身.帧解析帽)+' bytes on fd 3'}})#超
                    return#停
                缓冲=b''.join(封块+待块)#拼
                封块.clear()#清
                while True:#切行
                    位=缓冲.find(b'\n')#换行
                    if 位<0:#无
                        break#停
                    行=缓冲[:位]#行
                    缓冲=缓冲[位+1:]#余
                    if len(行)==0:#空
                        continue#下
                    try:#致命 UTF-8
                        文本=行.decode('utf-8')#解码
                    except UnicodeDecodeError:#非法
                        continue#丢
                    if 含不安全整数词(文本):#不安全
                        continue#丢
                    try:#JSON
                        解析=json.loads(文本)#解析
                    except Exception:#垃圾
                        continue#丢
                    帧=校验子帧(解析)#重建
                    if 帧 is not None:#有效
                        处理帧(帧)#处理
                待块[:]=分离残余(缓冲)#余
                待字节[0]=len(缓冲)#字节
            elif len(待块)>=最大待块:#封
                封块.append(b''.join(待块))#封
                待块.clear()#清
        def 读流(流,收):#读管道
            """读到 EOF。"""
            try:#读
                while True:#循环
                    块=流.read(65536)#块
                    if not 块:#EOF
                        break#停
                    收(块)#收
            except Exception:#关
                pass#忽略
        def 收出(块):#stdout 块
            """捕 stdout。"""
            捕杂散(杂出,块)#捕
        def 收误(块):#stderr 块
            """捕 stderr。"""
            捕杂散(杂错,块)#捕
        def 读出():#stdout
            """捕 stdout。"""
            读流(子.stdout,收出)#捕
            冲杂散(杂出)#冲
        def 读误():#stderr
            """捕 stderr。"""
            读流(子.stderr,收误)#捕
            冲杂散(杂错)#冲
        def 读协议():#fd 3 入站
            """读子→宿主帧。"""
            try:#读
                while True:#循环
                    块=宿主套.recv(65536)#块
                    if not 块:#EOF
                        break#停
                    处理协议块(块)#处理
            except Exception:#关
                pass#忽略
        threading.Thread(target=读出,daemon=True).start()#stdout
        threading.Thread(target=读误,daemon=True).start()#stderr
        threading.Thread(target=读协议,daemon=True).start()#fd 3
        def 墙到():#墙钟
            """墙钟超时。"""
            完成({'error':{'kind':'timeout','message':'wall-clock ceiling reached ('+str(自身.配置['maxWallMs'])+'ms)'}})#超时
        墙=threading.Timer(自身.配置['maxWallMs']/1000,墙到)#墙
        墙.daemon=True#守护
        墙.start()#开
        墙定时[0]=墙#记下
        def 中止时():#abort
            """请求中止。"""
            完成({'error':{'kind':'abort','message':消息于(getattr(请求.get('signal'),'reason',None))}})#中止
        信号=请求.get('signal')#信号
        if 信号 is not None:#有
            def 监视():#等
                """置位后中止。"""
                等待中止(信号)#等
                中止时()#中止
            threading.Thread(target=监视,daemon=True).start()#监视
        def 结算失败(失败):#活运行 settle
            """把失败送进完成。"""
            完成({'error':失败})#完成
        活={'kill':杀,'finished':完成任务,'settle':结算失败}#活运行
        活项[0]=活#记下
        自身.在途.add(活)#挂
        空间表=[]#namespaces
        for 全局,记录 in 绑定.items():#逐空间
            项={'global':全局,'names':list(记录['functions'].keys())}#项
            if 'errorClass' in 记录:#错误类
                项['errorClass']=记录['errorClass']#带
            空间表.append(项)#记下
        启动={'type':'boot','cpuSeconds':自身.配置['cpuSeconds'],'addressSpaceBytes':自身.配置['addressSpaceMb']*1024*1024,'maxLogBytes':自身.配置['maxLogBytes'],'maxValueBytes':自身.配置['maxValueBytes'],'namespaces':空间表}#boot
        已发跑=[False]#runSent
        try:#写 boot
            宿主套.sendall((json.dumps(启动,ensure_ascii=False)+'\n').encode('utf-8'))#boot
        except Exception as 错误:#失败
            完成({'error':{'kind':'worker-exit','message':'failed to boot python subprocess: '+消息于(错误)}})#失败
            return#停
        def 发跑():#run 帧
            """boot-ack 后发程序。"""
            if 已发跑[0]:#已
                return#停
            已发跑[0]=True#记下
            try:#写
                宿主套.sendall((json.dumps({'type':'run','program':请求['program']},ensure_ascii=False)+'\n').encode('utf-8'))#run
            except Exception as 错误:#失败
                完成({'error':{'kind':'worker-exit','message':'failed to boot python subprocess: '+消息于(错误)}})#失败
        启动门['run']=发跑#登记
        码=子.wait()#等 close
        信号名=None#信号
        if 码 is not None and 码<0:#信号退出
            号=-码#信号号
            if 号==getattr(signal,'SIGXCPU',24):#CPU
                信号名='SIGXCPU'#名
            else:#其它
                信号名=str(号)#号
        if 信号名=='SIGXCPU':#CPU
            完成({'error':{'kind':'timeout','message':'CPU time exhausted (limit at most the configured '+str(自身.配置['cpuSeconds'])+'s; a stricter inherited RLIMIT_CPU can fire sooner)'}})#超时
        else:#其它
            完成({'error':{'kind':'worker-exit','message':'python exited (code='+str(码)+', signal='+str(信号名)+') before completing'}})#退出
        if 决定[0] is not None:#已决定
            结算(决定[0])#结
        elif not 已兑现[0]:#尚未
            结算({'error':{'kind':'worker-exit','message':'python exited (code='+str(码)+', signal='+str(信号名)+') before completing'}})#结

default=python子进程ptc运行时#框架槽
Config=配置#框架槽
name='experimental-ptc-runtime-python'#框架槽
inject=[]#类即 ptcRuntime 服务
apply=python子进程ptc运行时#框架槽
