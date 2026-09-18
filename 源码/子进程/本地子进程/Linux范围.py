import ctypes,errno,json,os,re,signal,socket,sys,tempfile,time#libc、缺席码、JSON、路径、正则、信号、套接字、解释器、临时目录与可中止睡眠
from threading import Event as 同步事件,Lock as 互斥锁,Thread as 线程#观察广播、互斥与后台线程
from secrets import token_hex#单元词干随机后缀
from subprocess import Popen,DEVNULL,PIPE,run as 同步跑#派生、忽略流与同步 systemd
from ...工具.超时 import 已中止,若已中止则抛出#中止入口
from ..子进程.控制 import 子进程控制描述符#控制通道 fd
from .启动 import 子环境#擦洗后的子环境
from .终端 import 本地子进程错误#本包错误
from .控制派生 import 控制管道#父侧控制管

__all__=(#仅中文公开名
    '探测Linux引导','探测Linux范围','探测Linux管理器','探测Linux原生',
    '准备Linux终端范围','启动Linux范围','向Linux直接进程发信号',
)#公开面结束

systemctl超时毫秒=5_000#systemctl超时
范围初始轮询间隔毫秒=50#初始轮询间隔
缺失单元=re.compile(r'\bunit\b[^\r\n]*(?:could not be found|not found|not loaded)',re.I)#缺失单元
数字任务=re.compile(r'^[0-9]+\Z')#TasksCurrent数字
runner环境键='DSH_SUBPROCESS_RUNNER'#私有 runner 选择器
runner控制前缀=('NODE_','TSX_')#引导前清掉的控制前缀
标准描述符=(0,1,2)#stdin/stdout/stderr
F_GETFD=1#取 fd 标志
F_SETFD=2#设 fd 标志
FD_CLOEXEC=1#close-on-exec
缓存Execve=None#懒加载 libc execve

def 锁json(值):#线协议 JSON
    """按对拍锁写出 JSON 文本。"""
    return json.dumps(值,ensure_ascii=False,separators=(',',':'),allow_nan=False)#锁格式

def 管理器环境():#管理器环境
    """C 语言环境，去掉 SYSTEMD_LOG_TARGET。"""
    环境=子环境({'LC_ALL':'C'})#C 语言环境
    环境.pop('SYSTEMD_LOG_TARGET',None)#去掉日志目标
    return 环境#返回

def 静默systemd环境():#静默 systemd 环境
    """C 语言环境且 systemd 日志丢弃。"""
    return 子环境({'LC_ALL':'C','SYSTEMD_LOG_TARGET':'null'})#静默

def 查询systemctl(命令,参数):#查询 systemctl
    """同步跑 systemctl 并收成状态/输出。"""
    try:#执行
        完成=同步跑([命令]+list(参数),capture_output=True,text=True,encoding='utf-8',env=管理器环境(),timeout=systemctl超时毫秒/1000)#执行
        return {'status':完成.returncode,'stdout':完成.stdout,'stderr':完成.stderr}#结果
    except OSError as 错误:#派生失败
        return {'status':None,'stdout':'','stderr':'','error':错误}#可选错误

def 单元词干(前缀):#单元词干
    """前缀-pid-随机。"""
    return f'{前缀}-{str(os.getpid())}-{token_hex(6)}'#前缀-pid-随机

def 可中止睡眠(延迟毫秒,信号=None):#可中止睡眠
    """睡指定毫秒；信号中止则抛出。"""
    if 信号 is None:#无取消
        time.sleep(延迟毫秒/1000)#直接睡
        return#结束
    截止=time.monotonic()+延迟毫秒/1000#截止时刻
    while time.monotonic()<截止:#未到
        若已中止则抛出(信号)#已中止则抛
        剩余=截止-time.monotonic()#剩余秒
        if 剩余<=0:#到点
            break#结束
        time.sleep(min(0.02,剩余))#短睡
    若已中止则抛出(信号)#醒来后再查

def 系统错误(errno值,系统调用,路径=None):#系统错误
    """组装带 code/errno/syscall 的错误。"""
    码='errno'+str(errno值)#错误码名
    详情=os.strerror(errno值) if errno值 else str(errno值)#详情
    主语=系统调用 if 路径 is None else f"{系统调用} '{路径}'"#主语
    错误=本地子进程错误(f'{码}: {详情}, {主语}')#组装错误
    错误.code=码#码
    错误.errno=errno值#errno
    错误.syscall=系统调用#系统调用
    if 路径 is not None:#有路径
        错误.path=路径#路径
    return 错误#返回

def 加载LinuxExecve():#加载 Linux execve
    """首次使用时绑定 libc execve 与 fcntl。"""
    global 缓存Execve#缓存
    if 缓存Execve is not None:#命中
        return 缓存Execve#返回
    libc=ctypes.CDLL(None,use_errno=True)#加载 libc
    libc.execve.argtypes=[ctypes.c_char_p,ctypes.POINTER(ctypes.c_char_p),ctypes.POINTER(ctypes.c_char_p)]#execve签名
    libc.execve.restype=ctypes.c_int#返回码
    libc.fcntl.argtypes=[ctypes.c_int,ctypes.c_int,ctypes.c_int]#fcntl签名
    libc.fcntl.restype=ctypes.c_int#返回码
    def 执行映像替换(文件,参数表,环境):#替换当前进程映像
        """清标准 fd 的 CLOEXEC 后 execve；失败抛错。"""
        for 描述符 in 标准描述符:#清标准 fd 的 CLOEXEC
            标志=libc.fcntl(描述符,F_GETFD,0)#取标志
            if 标志==-1:#失败
                raise 系统错误(ctypes.get_errno(),'fcntl')#失败
            if (标志&FD_CLOEXEC)==0:#无 CLOEXEC
                continue#下一描述符
            if libc.fcntl(描述符,F_SETFD,标志&~FD_CLOEXEC)==-1:#清位
                raise 系统错误(ctypes.get_errno(),'fcntl')#失败
        参数数组=(ctypes.c_char_p*(len(参数表)+1))(*[项.encode('utf-8') for 项 in 参数表],None)#argv
        环境数组=(ctypes.c_char_p*(len(环境)+1))(*[f'{键}={值}'.encode('utf-8') for 键,值 in 环境.items()],None)#envp
        libc.execve(文件.encode('utf-8'),参数数组,环境数组)#替换映像
        raise 系统错误(ctypes.get_errno(),'execve',文件)#失败则抛
    缓存Execve=执行映像替换#缓存
    return 缓存Execve#返回

def 是否记录(值):#是否对象记录
    """对象且非 list。"""
    return isinstance(值,dict)#dict

def 键集精确(值,必需,可选=None):#键集精确
    """必需齐全且无多余键。"""
    if 可选 is None:#缺省
        可选=()#空
    允许=set(list(必需)+list(可选))#允许集
    for 键 in 必需:#必需齐全
        if 键 not in 值:#缺键
            return False#非法
    for 键 in 值:#无多余
        if 键 not in 允许:#多余
            return False#非法
    return True#合法

def 是否序列化Runner错误(值):#是否序列化错误
    """有界 name/message 与可选 code/syscall/path。"""
    if not 是否记录(值) or not 键集精确(值,['name','message'],['code','syscall','path']):#形态
        return False#非法
    if not isinstance(值['name'],str) or not isinstance(值['message'],str):#名消息
        return False#非法
    if 'code' in 值 and not isinstance(值['code'],str):#码
        return False#非法
    if 'syscall' in 值 and not isinstance(值['syscall'],str):#系统调用
        return False#非法
    if 'path' in 值 and not isinstance(值['path'],str):#路径
        return False#非法
    return True#合法

def 解析错误结果(值):#解析错误结果
    """解析 type=error 的启动错误。"""
    if not 键集精确(值,['type','error']) or not 是否序列化Runner错误(值['error']):#非法
        raise 本地子进程错误('subprocess runner emitted an invalid error result')#抛错
    if 值['type']!='error':#未知类型
        raise 本地子进程错误('subprocess runner emitted an unknown error result')#抛错
    return {'type':'error','error':值['error']}#返回

def 创建Linux启动文件(请求):#创建 Linux 启动文件
    """创建私有 0700 目录与一份完整 0600 启动请求。"""
    目录=tempfile.mkdtemp(prefix='dsh-subprocess-launch-')#临时目录
    文件={'directory':目录,'requestPath':os.path.join(目录,'launch-request.json'),'startupErrorPath':os.path.join(目录,'startup-error.json')}#路径集
    try:#写入
        os.chmod(目录,0o700)#目录权限
        描述符=os.open(文件['requestPath'],os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)#O_EXCL
        try:#写请求
            os.write(描述符,锁json(请求).encode('utf-8'))#写请求
        finally:#关
            os.close(描述符)#关
        return 文件#返回
    except BaseException:#失败
        清理Linux启动文件(文件)#清理
        raise#重抛

def 读Linux启动错误(路径):#读启动错误
    """若引导发布了预 exec 错误则读取。"""
    if not os.path.exists(路径):#不存在
        return None#未发布
    with open(路径,'r',encoding='utf-8') as 句柄:#读
        值=json.loads(句柄.read())#解析
    if not 是否记录(值):#非法
        raise 本地子进程错误('subprocess runner emitted an invalid startup error')#非法
    return 解析错误结果(值)#解析错误结果

def 反序列化Runner错误(序列化):#反序列化
    """从严格 runner 记录重建错误。"""
    错误=本地子进程错误(序列化['message'])#建错误
    错误.name=序列化['name']#名
    if 'code' in 序列化:#码
        错误.code=序列化['code']#码
    if 'syscall' in 序列化:#系统调用
        错误.syscall=序列化['syscall']#系统调用
    if 'path' in 序列化:#路径
        错误.path=序列化['path']#路径
    return 错误#返回

def 清理Linux启动文件(文件):#清理 Linux 启动文件
    """仅尽力移除为本 spawn 创建的私有路径。"""
    try:#尽力清理
        if os.path.islink(文件['directory']):#符号链接
            os.unlink(文件['directory'])#删链接
            return#结束
        for 路径 in (文件['requestPath'],文件['startupErrorPath']):#私有文件
            try:#删文件
                os.unlink(路径)#删
            except OSError as 错误:#删失败
                if 错误.errno!=os.ENOENT:#非 ENOENT
                    raise 错误#重抛
        os.rmdir(文件['directory'])#删目录
    except OSError:#忽略
        return#崩溃残渣保持私有

def 解析Runner调用():#解析 runner 调用
    """当前解释器加上本包引导入口。"""
    入口=os.path.join(os.path.dirname(os.path.abspath(__file__)),'引导入口.py')#引导入口
    return [sys.executable,入口]#解释器与入口

def runner调用可用(调用=None):# runner 是否可用
    """不执行探针模式地检查可执行文件与入口路径。"""
    if 调用 is None:#缺省
        调用=解析Runner调用()#解析
    try:#探针
        可执行=调用[0]#可执行
        if os.path.isabs(可执行) and (not os.path.isfile(可执行) or not os.access(可执行,os.X_OK)):#不可执行
            return False#不可用
        入口=调用[-1]#入口
        if 入口!=可执行 and os.path.isabs(入口) and not os.access(入口,os.R_OK):#入口不可读
            return False#不可用
        return True#可用
    except OSError:#失败
        return False#不可用

def runner环境(选择器,调用=None):# runner 环境
    """构建引导安全环境；目标覆盖经请求到达。"""
    环境=子环境()#子环境基线
    清掉=[]#待删键
    for 名 in 环境:#清控制前缀
        规范=名.upper()#大写
        for 前缀 in runner控制前缀:#匹配前缀
            if 规范.startswith(前缀):#匹配
                清掉.append(名)#记下
                break#下一键
    for 名 in 清掉:#删除
        环境.pop(名,None)#删除
    环境[runner环境键]=选择器#选择器
    环境['SYSTEMD_LOG_TARGET']='null'#静默 systemd
    return 环境#返回

def runner标准流(规格):# runner stdio
    """直接 Linux 目标 stdio；可选控制管占 fd 7。"""
    标准流=规格['stdio']#三路处置
    入=DEVNULL if 标准流['stdin']=='ignore' else PIPE#stdin
    出=None if 标准流['stdout']=='inherit' else PIPE#stdout
    错=None if 标准流['stderr']=='inherit' else PIPE#stderr
    return 入,出,错#三路

def 取内部(内部,键,缺省):#取测试缝
    """内部覆盖或生产缺省。"""
    if 内部 is None or 键 not in 内部 or 内部[键] is None:#无覆盖
        return 缺省#缺省
    return 内部[键]#覆盖

def 探测Linux引导(内部=None):#探测 Linux 引导
    """不经探针模式确认本精确 runner 入口与 libc execve 绑定。"""
    if 内部 is None:#缺省
        内部={}#空
    try:#探针
        取内部(内部,'loadLinuxExecve',加载LinuxExecve)()#加载 execve
        if 'runnerInvocation' in 内部 and 内部['runnerInvocation'] is not None:#固定调用
            调用=内部['runnerInvocation']#固定
        else:#解析
            调用=取内部(内部,'resolveRunnerInvocation',解析Runner调用)()#解析
        return 取内部(内部,'runnerAvailable',runner调用可用)(调用)#可用性
    except (本地子进程错误,OSError):#失败
        return False#不可用

def 探测Linux范围(内部=None):#探测 Linux scope
    """在选择原生启动前确认当前字面 argv 瞬态 scope 支持。"""
    if 内部 is None:#缺省
        内部={}#空
    单元基=单元词干('dsh-subprocess-probe')#探针单元
    跑=取内部(内部,'spawnSync',同步跑)#同步跑
    参数=[#探针参数
        '--user','--scope','--quiet','--collect','--expand-environment=no',#scope 开关
        f'--unit={单元基}','--',#单元与分隔
        取内部(内部,'systemctl','systemctl'),#systemctl
        '--user','show',f'{单元基}.scope','--property=ActiveState','--value',#属性
    ]#参数结束
    try:#跑探针
        完成=跑([取内部(内部,'systemdRun','systemd-run')]+参数,env=静默systemd环境(),stdout=DEVNULL,stderr=DEVNULL,timeout=systemctl超时毫秒/1000)#选项
        return 完成.returncode==0#成功
    except OSError:#派生失败
        return False#失败

def 探测Linux管理器(内部=None):#探测 Linux 管理器
    """在正向深探针后确认当前用户管理器仍可达。"""
    if 内部 is None:#缺省
        内部={}#空
    跑=取内部(内部,'spawnSync',同步跑)#同步跑
    try:#查询版本
        完成=跑([取内部(内部,'systemctl','systemctl'),'--user','show','--property=Version','--value'],env=管理器环境(),stdout=DEVNULL,stderr=DEVNULL,timeout=systemctl超时毫秒/1000)#选项
        return 完成.returncode==0#成功
    except OSError:#失败
        return False#失败

def 探测Linux原生(内部=None):#探测 Linux 原生
    """为一次合格 spawn 复核每个 Linux 原生先决。"""
    return 探测Linux引导(内部) and 探测Linux范围(内部)#引导且 scope

class 操作任务:
    """单次操作结果；兑现或拒绝一次。"""
    def __init__(自身):#未决
        """构造未决任务。"""
        自身._事件=同步事件()#落定事件
        自身._值=None#兑现值
        自身._错误=None#拒绝错误

    def 兑现(自身,值=None):#成功结算
        """成功结算。"""
        if 自身._事件.is_set():#已结算
            return 值#忽略
        自身._值=值#记下
        自身._事件.set()#落定
        return 值#返回

    def 拒绝(自身,错误):#失败结算
        """失败结算。"""
        if 自身._事件.is_set():#已结算
            return#忽略
        if isinstance(错误,BaseException):#已是异常
            自身._错误=错误#原样
        else:#包装
            自身._错误=本地子进程错误(str(错误))#包装
        自身._事件.set()#落定

    def 等待(自身):#阻塞等到结算
        """阻塞等到结算。"""
        自身._事件.wait()#等
        if 自身._错误 is not None:#失败
            raise 自身._错误#抛出
        return 自身._值#兑现值

class Linux范围启动:#scope 启动结算
    """引导消费与已请求终止信号。"""
    def __init__(自身,文件,种类):#记下文件与种类
        """记下启动文件与种类。"""
        自身.文件=文件#启动文件
        自身.种类=种类#subprocess 或 terminal
        自身.终止信号集=set()#已请求的终止信号

    def 结算结局(自身,结局):#结算结局
        """读启动错误；请求未消费且非已请求终止则抛。"""
        启动=读Linux启动错误(自身.文件['startupErrorPath'])#启动错误
        if 启动 is not None:#引导失败
            raise 反序列化Runner错误(启动['error'])#引导失败
        信号=结局['signal'] if 'signal' in 结局 else None#信号
        if os.path.exists(自身.文件['requestPath']) and not (信号 is not None and 信号 in 自身.终止信号集):#请求未消费
            raise 本地子进程错误(f'{自身.种类} scope exited before its bootstrap consumed the launch request')#引导未消费
        return 结局#返回结局

class 直接范围:#直接范围
    """是否在运行、向直接进程发信号与直接结算。"""
    def __init__(自身,是否在运行,发信号回调,已结算):#记下回调
        """记下在跑探针、发信号与直接结算任务。"""
        自身._是否在运行=是否在运行#探针
        自身._发信号=发信号回调#发信号
        自身.已结算=已结算#直接退出/错误结算

    def 是否在运行(自身):#是否在运行
        """直接进程是否仍在跑。"""
        return 自身._是否在运行()#探针

    def 发信号(自身,信号):#发信号
        """向直接进程发 SIGTERM/SIGKILL；已提交或 PID 缺席则为真。"""
        return 自身._发信号(信号)#回调

class Systemd范围所有者:#systemd scope 所有者
    """终止与整范围结算使用的平台所有者。"""
    def __init__(自身,单元,启动,直接,systemctl路径,同步跑回调,查询,睡眠):#构造
        """记下单元、启动结算、直接范围与 systemd 缝。"""
        自身.单元=单元#单元名
        自身.启动=启动#启动结算
        自身.直接=直接#直接范围
        自身.systemctl=systemctl路径#systemctl
        自身.同步跑=同步跑回调#同步跑
        自身.查询=查询#查询
        自身.睡眠=睡眠#睡眠
        自身.建立='pending'#建立状态
        自身.已停=False#是否已停
        自身.已请求终止=False#是否已请求终止
        自身._观察=None#观察任务
        自身._观察锁=互斥锁()#观察锁
        自身.杀失败=None#杀失败
        自身.直接杀结算=None#直接杀结算
        自身.唤醒代际=0#唤醒代际
        自身._唤醒事件=同步事件()#唤醒事件
        自身._唤醒代际快照=0#等待者代际

    def 检查任务数(自身):#TasksCurrent
        """统计原生范围内的任务数；不可观察则为 None。"""
        完成=自身.同步跑([自身.systemctl,'--user','show','--property=LoadState','--property=ActiveState','--property=TasksCurrent',自身.单元],capture_output=True,text=True,encoding='utf-8',env=管理器环境(),timeout=systemctl超时毫秒/1000)#show
        if 完成.returncode!=0 or not isinstance(完成.stdout,str):#不可观察
            return None#无
        状态=自身.解析单元状态(完成.stdout)#解析
        if 状态['loadState']=='loaded' and 状态['activeState']=='active':#活动
            return 状态['tasksCurrent']#任务
        return None#无

    def 发信号(自身,信号):#发信号
        """向受管范围发 SIGTERM/SIGKILL。"""
        if 自身.已停:#已停
            return#结束
        自身.已请求终止=True#记下终止请求
        if 自身.直接.是否在运行():#在跑则记终止信号
            自身.启动.终止信号集.add(信号)#记终止信号
        自身.观察请求消费()#观察请求消费
        需直接回退=自身.建立=='pending'#建立前需直接回退
        直接已投递=False#是否已直接投递
        if 需直接回退 and 自身.直接.是否在运行():#直接发
            直接已投递=自身.直接.发信号(信号)#直接发
        try:#systemctl kill
            完成=自身.同步跑([自身.systemctl,'--user','kill','--kill-whom=all',f'--signal={信号}',自身.单元],capture_output=True,text=True,encoding='utf-8',env=管理器环境(),timeout=systemctl超时毫秒/1000)#选项
            码=完成.returncode#状态
            错误=None#派生未失败
            出=完成.stdout#stdout
            错=完成.stderr#stderr
        except OSError as 派生错误:#派生失败
            码=None#状态
            错误=派生错误#错误
            出=''#stdout
            错=''#stderr
        自身.唤醒观察()#唤醒观察
        if 错误 is None and 码==0:#成功
            if 信号=='SIGKILL':#清杀失败
                自身.杀失败=None#清
                自身.直接杀结算=None#清直接杀结算
            return#结束
        if (not 需直接回退) and 自身.直接.是否在运行():#建立后回退
            直接已投递=自身.直接.发信号(信号)#回退
        if 信号=='SIGKILL':#KILL 失败
            输出=f'{出}\n{错}'#输出
            if not 缺失单元.search(输出):#非缺失单元
                自身.杀失败=错误 if 错误 is not None else 本地子进程错误(f"systemctl could not signal {自身.单元}: {输出.strip() or ('exit '+str(码))}")#记失败
                自身.直接杀结算=自身.直接.已结算 if 直接已投递 else None#已投递则汇合物理结算

    def 为宿主退出终止(自身):#宿主退出终止
        """宿主退出期间同步强制最终终止。"""
        if 自身.已停:#已停
            return#结束
        try:#直接杀
            if 自身.直接.是否在运行():#在跑
                自身.直接.发信号('SIGKILL')#SIGKILL
        except (本地子进程错误,OSError):#吞
            pass#继续原生所有者
        try:#systemctl 杀
            自身.同步跑([自身.systemctl,'--user','kill','--kill-whom=all','--signal=SIGKILL',自身.单元],env=管理器环境(),stdout=DEVNULL,stderr=DEVNULL,timeout=systemctl超时毫秒/1000)#kill
        except OSError:#失败
            pass#宿主退出不能报告单个范围

    def 观察请求消费(自身):#观察请求消费
        """请求已消费则标记已建立。"""
        if 自身.建立=='pending' and not os.path.exists(自身.启动.文件['requestPath']):#请求已消费
            自身.建立='established'#已建立

    def 单元缺席(自身):#单元是否缺席
        """缺席路径；已建立则否。"""
        自身.观察请求消费()#观察
        if 自身.建立=='established':#已建立则非缺席路径
            return False#非缺席
        if (not 自身.直接.是否在运行()) and os.path.exists(自身.启动.文件['requestPath']):#引导未消费
            return False#仍待
        if 自身.杀失败 is not None:#抛杀失败
            raise 自身.杀失败#抛杀失败
        return True#缺席

    def 空受管范围(自身,当前任务数):#空受管范围
        """已请求终止且无任务且直接进程已走。"""
        return 自身.已请求终止 and 当前任务数==0 and (not 自身.直接.是否在运行() or not os.path.exists(自身.启动.文件['requestPath']))#已请求终止且无任务，且直接进程已走或请求已消费

    def 释放空范围(自身):#释放空范围
        """释放残留空 scope。"""
        try:#停单元
            自身.同步跑([自身.systemctl,'--user','stop',自身.单元],env=管理器环境(),stdout=DEVNULL,stderr=DEVNULL,timeout=systemctl超时毫秒/1000)#stop
        except OSError:#失败
            pass#清理失败只留下瞬态单元

    def 解析单元状态(自身,标准输出):#解析单元状态
        """解析 LoadState/ActiveState/TasksCurrent。"""
        属性表={}#属性表
        for 行 in 标准输出.splitlines():#逐行
            if 行=='':#空行
                continue#下一行
            分隔=行.find('=')#=位置
            if 分隔<=0:#畸形
                raise 本地子进程错误(f'systemctl returned malformed state for {自身.单元}: {锁json(标准输出.strip())}')#抛错
            名=行[:分隔]#名
            if 名 in 属性表:#重复
                raise 本地子进程错误(f'systemctl returned duplicate {名} for {自身.单元}')#抛错
            属性表[名]=行[分隔+1:]#写入
        加载态=属性表['LoadState'] if 'LoadState' in 属性表 else None#加载态
        活动态=属性表['ActiveState'] if 'ActiveState' in 属性表 else None#活动态
        已报任务=属性表['TasksCurrent'] if 'TasksCurrent' in 属性表 else None#当前任务
        当前任务=None if 已报任务=='[not set]' else 已报任务#未设置则缺席
        期望键数=2 if 已报任务 is None else 3#键数
        if len(属性表)!=期望键数 or 加载态 is None or 活动态 is None:#不完整
            raise 本地子进程错误(f'systemctl returned incomplete state for {自身.单元}: {锁json(标准输出.strip())}')#抛错
        if 当前任务 is not None and 数字任务.fullmatch(当前任务) is None:#非数字
            raise 本地子进程错误(f'systemctl returned a non-numeric TasksCurrent for {自身.单元}: {锁json(当前任务)}')#抛错
        return {'loadState':加载态,'activeState':活动态,'tasksCurrent':None if 当前任务 is None else int(当前任务)}#状态

    def 范围活动(自身):#范围是否活动
        """查询单元；活动则 True。"""
        自身.观察请求消费()#观察
        代际=自身.唤醒代际#查询前代际
        直接在跑=自身.直接.是否在运行()#查询前直接是否在跑
        结果=自身.查询(自身.systemctl,['--user','show',自身.单元,'--property=LoadState','--property=ActiveState','--property=TasksCurrent'])#查询
        if 代际!=自身.唤醒代际:#查询过期，当作仍活动
            return True#信号会使投递前的状态失效
        输出=f"{结果['stdout']}\n{结果['stderr']}"#输出
        if 结果['status']==0:#成功
            状态=自身.解析单元状态(结果['stdout'])#解析
            if 状态['loadState']=='not-found' and 状态['activeState']=='inactive':#缺席路径
                return 自身.单元缺席()#缺席
            if 状态['loadState']!='loaded':#未知加载
                raise 本地子进程错误(f"systemctl returned unknown state for {自身.单元}: {锁json({'loadState':状态['loadState'],'activeState':状态['activeState']})}")#抛错
            自身.建立='established'#已建立
            if 状态['activeState']=='inactive' or 状态['activeState']=='failed':#已停
                return False#已停
            if 状态['activeState'] not in ('active','activating','reloading','deactivating'):#未知活动
                raise 本地子进程错误(f"systemctl returned unknown ActiveState for {自身.单元}: {锁json(状态['activeState'])}")#抛错
            if 自身.空受管范围(状态['tasksCurrent']):#残留空范围
                自身.释放空范围()#释放
                return False#当作已停
            if 自身.杀失败 is not None:#抛杀失败
                if 直接在跑 and 自身.直接杀结算 is not None:#直接仍在且有结算
                    结算=自身.直接杀结算#取出
                    自身.直接杀结算=None#摘掉
                    try:#汇合物理结算
                        结算.等待()#等直接结局
                    except BaseException:#直接结局保留错误
                        pass#本屏障只汇合物理结算
                    return 自身.范围活动()#重查
                raise 自身.杀失败#抛杀失败
            return True#活动
        if not 缺失单元.search(输出):#非缺失
            if 'error' in 结果 and 结果['error'] is not None:#抛错误
                raise 结果['error']#抛错误
            raise 本地子进程错误(f"systemctl could not read {自身.单元}: {输出.strip() or ('exit '+str(结果['status']))}")#抛错
        return 自身.单元缺席()#缺席路径

    def 唤醒观察(自身):#唤醒观察
        """代际加一并唤醒等待。"""
        自身.唤醒代际+=1#代际+1
        自身._唤醒事件.set()#唤醒

    def 等待轮询(自身,延迟毫秒,代际):#等待轮询
        """睡或被唤醒；代际过期则立即返回。"""
        if 代际!=自身.唤醒代际:#代际过期
            return#结束
        自身._唤醒事件.clear()#清事件
        自身._唤醒代际快照=代际#登记
        截止=time.monotonic()+延迟毫秒/1000#截止
        while time.monotonic()<截止:#未到
            if 自身.唤醒代际!=代际:#已唤醒
                return#结束
            剩余=截止-time.monotonic()#剩余
            if 剩余<=0:#到点
                break#结束
            自身._唤醒事件.wait(min(0.02,剩余))#短等
            自身._唤醒事件.clear()#清

    def 等待退出(自身):#等待退出
        """等待受管范围变空。"""
        if 自身.已停:#已停
            return#结束
        with 自身._观察锁:#单例观察
            if 自身._观察 is None:#未建
                观察=操作任务()#观察任务
                自身._观察=观察#记下
                def 后台观察退出():#后台观察
                    """活动则等，停下后兑现。"""
                    try:#观察
                        轮询间隔毫秒=范围初始轮询间隔毫秒#轮询间隔
                        代际=自身.唤醒代际#代际
                        while 自身.范围活动():#活动则等
                            自身.等待轮询(轮询间隔毫秒,代际)#等待
                            代际=自身.唤醒代际#刷新代际
                            if 自身.建立=='established':#已建立
                                轮询间隔毫秒=min(轮询间隔毫秒*2,systemctl超时毫秒)#退避
                        自身.已停=True#停下
                        观察.兑现()#兑现
                    except BaseException as 错误:#失败可重试
                        with 自身._观察锁:#清观察
                            if 自身._观察 is 观察:#仍是本观察
                                自身._观察=None#清观察
                        观察.拒绝(错误)#重抛
                工作=线程(target=后台观察退出)#观察线程
                工作.daemon=True#不挡住退出
                工作.start()#启动
        自身._观察.等待()#等待

    def 清理(自身):#清理
        """释放提供方私有协议制品。"""
        清理Linux启动文件(自身.启动.文件)#清理文件

def 范围参数(单元基,调用,参数表):#scope 参数
    """systemd-run 的 scope 参数表。"""
    return ['--user','--scope','--quiet','--collect','--expand-environment=no',f'--unit={单元基}','--']+list(调用)+['--']+list(参数表)#参数表

def 直接结局(孩子,启动):#直接结局
    """等孩子退出并走启动结算。"""
    任务=操作任务()#结局任务
    def 盯退出():#退出监视
        """等退出后结算。"""
        try:#等孩子
            码=孩子.wait()#等直接孩子
            退出码=码#默认退出码
            信号名=None#默认无信号
            if 码 is not None and 码<0:#POSIX 负码表示信号
                退出码=None#死于信号
                try:#反查信号名
                    信号名=signal.Signals(-码).name#信号名
                except ValueError:#未知编号
                    信号名=None#未知
            任务.兑现(启动.结算结局({'exitCode':退出码,'signal':信号名}))#兑现
        except BaseException as 错误:#读失败
            失败=错误 if isinstance(错误,BaseException) else 本地子进程错误(str(错误))#失败
            任务.拒绝(失败)#拒绝
    工作=线程(target=盯退出)#退出监视线程
    工作.daemon=True#不挡住退出
    工作.start()#启动
    return 任务#结局任务

def 向Linux直接进程发信号(pid,发送):#向直接进程发信号
    """区分缺席 PID 与投递失败；已提交或 PID 缺席则为真。"""
    try:#提交
        if 发送():#已提交
            return True#成功
    except BaseException:#失败的信号仍允许独立缺席观察
        pass#吞
    try:#探活
        os.kill(pid,0)#存在性
        return False#仍在
    except OSError as 错误:#失败
        return 错误.errno==errno.ESRCH#缺席

def 向孩子组发信号(孩子,信号):#向孩子组发信号
    """负 pid 打组；TERM 组成功即可，KILL 还要直接提交。"""
    组已投递=False#组是否投递
    try:#组信号
        os.kill(-(孩子.pid),getattr(signal,信号))#负 pid
        组已投递=True#成功
    except OSError:#缺失或不可达的组仍允许直接进程尝试
        pass#吞
    if 组已投递 and 信号=='SIGTERM':#TERM 组成功即可
        return True#已投递
    def 发送直接():#直接进程信号
        """向直接 pid 发信号。"""
        os.kill(孩子.pid,getattr(signal,信号))#直接 pid
        return True#已提交
    return 向Linux直接进程发信号(孩子.pid,发送直接)#直接发

class Linux终端范围启动:#Linux 终端 scope 启动
    """精确一次性 scope/引导的 Linux PTY 调用与所有者。"""
    def __init__(自身,命令,参数,工作目录,环境,绑定所有者,结算结局,清理):#记下事实
        """记下调用事实与所有权回调。"""
        自身.command=命令#命令；线侧字段
        自身.args=参数#参数
        自身.cwd=工作目录#工作目录
        自身.env=环境#环境
        自身.绑定所有者=绑定所有者#绑定所有者
        自身.结算结局=结算结局#解析结局
        自身.清理=清理#清理

class 受管进程启动:#受管进程启动
    """公共 stdio 与结果生命周期消费的平台启动事实。"""
    def __init__(自身,标准输入,标准输出,标准错误,直接结局,所有者,控制=None):#记下
        """记下管道、直接结局、所有者与可选控制管。"""
        自身.标准输入=标准输入#stdin
        自身.标准输出=标准输出#stdout
        自身.标准错误=标准错误#stderr
        自身.直接结局=直接结局#直接结局任务
        自身.所有者=所有者#所有者
        自身.控制=控制#可选控制通道

def 准备Linux终端范围(规格,目标环境,内部=None):#准备 Linux 终端 scope
    """用同一启动请求与引导核心准备一个 Linux PTY scope。"""
    if 内部 is None:#缺省
        内部={}#空
    调用=内部['runnerInvocation'] if 'runnerInvocation' in 内部 and 内部['runnerInvocation'] is not None else 解析Runner调用()#调用
    文件=创建Linux启动文件({'cwd':规格['cwd'],'env':目标环境})#启动文件
    启动=Linux范围启动(文件,'terminal')#启动结算
    单元基=单元词干('dsh-terminal')#单元词干
    def 绑定所有者(直接):#绑定所有者
        """绑到 systemd scope 所有者。"""
        return Systemd范围所有者(f'{单元基}.scope',启动,直接,取内部(内部,'systemctl','systemctl'),取内部(内部,'spawnSync',同步跑),取内部(内部,'systemctlQuery',查询systemctl),取内部(内部,'sleep',可中止睡眠))#所有者
    def 结算(结局):#解析结局
        """委托启动结算。"""
        return 启动.结算结局(结局)#解析
    def 清理():#清理
        """清理启动文件。"""
        清理Linux启动文件(文件)#清理
    return Linux终端范围启动(取内部(内部,'systemdRun','systemd-run'),范围参数(单元基,调用,规格['argv']),os.getcwd(),runner环境(文件['requestPath'],调用),绑定所有者,结算,清理)#启动事实

def 启动Linux范围(规格,目标环境,内部=None):#启动 Linux scope
    """在瞬态用户 scope 内启动一个普通目标。"""
    if 内部 is None:#缺省
        内部={}#空
    调用=内部['runnerInvocation'] if 'runnerInvocation' in 内部 and 内部['runnerInvocation'] is not None else 解析Runner调用()#调用
    控制请求=规格['stdio']['control'] if 'control' in 规格['stdio'] else None#可选控制
    请求={'cwd':规格['cwd'],'env':目标环境}#启动请求
    if 控制请求 is not None:#有控制管
        请求['control']=控制请求#写入请求
    文件=创建Linux启动文件(请求)#文件
    启动=Linux范围启动(文件,'subprocess')#启动结算
    单元基=单元词干('dsh-subprocess')#单元
    入,出,错=runner标准流(规格)#直接 stdio
    派生=取内部(内部,'spawn',None)#测试 spawn
    try:#spawn
        if 派生 is not None:#测试覆盖
            孩子=派生(取内部(内部,'systemdRun','systemd-run'),范围参数(单元基,调用,规格['argv']))#测试 spawn
        else:#生产
            启动参数={'args':[取内部(内部,'systemdRun','systemd-run')]+范围参数(单元基,调用,规格['argv']),'cwd':os.getcwd(),'env':runner环境(文件['requestPath'],调用),'stdin':入,'stdout':出,'stderr':错,'start_new_session':True}#Popen 参数
            if 控制请求=='pipe':#显式控制通道
                控制父,控制子=socket.socketpair()#一对双工套接字
                def 放到控制描述符():#子进程把套接字放到 fd 7
                    """把继承套接字放到保留控制描述符。"""
                    os.dup2(控制子.fileno(),子进程控制描述符)#占 fd 7
                启动参数['pass_fds']=(控制子.fileno(),)#继承子端
                启动参数['preexec_fn']=放到控制描述符#放到 7
                孩子=Popen(**启动参数)#分离
                控制子.close()#父进程关掉子端
                孩子.控制=控制父#挂到孩子上供控制管道读取
            else:#无控制管
                孩子=Popen(**启动参数)#分离
    except BaseException:#失败
        清理Linux启动文件(文件)#清理
        raise#重抛
    直接=直接结局(孩子,启动)#直接结局任务
    def 是否在运行():#直接范围在跑
        """pid 仍在且未退出。"""
        return 孩子.pid is not None and 孩子.poll() is None#在跑
    def 发信号(信号):#向孩子组发信号
        """组信号。"""
        return 向孩子组发信号(孩子,信号)#发信号
    所有者=Systemd范围所有者(f'{单元基}.scope',启动,直接范围(是否在运行,发信号,直接),取内部(内部,'systemctl','systemctl'),取内部(内部,'spawnSync',同步跑),取内部(内部,'systemctlQuery',查询systemctl),取内部(内部,'sleep',可中止睡眠))#所有者
    return 受管进程启动(孩子.stdin,孩子.stdout,孩子.stderr,直接,所有者,控制管道(孩子,控制请求))#受管启动
