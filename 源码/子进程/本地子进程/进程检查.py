import os,re,signal,struct,sys,sysconfig,importlib.util,platform as 平台库,stat as 文件状态#读proc、匹配数字名、信号、小端整型、平台与标准库载入
from .终端 import 本地子进程错误#本包错误
标准库子进程规格=importlib.util.spec_from_file_location('dsh_stdlib_subprocess',os.path.join(sysconfig.get_path('stdlib'),'subprocess.py'))#标准库subprocess路径
标准库子进程=importlib.util.module_from_spec(标准库子进程规格)#标准库模块壳
标准库子进程规格.loader.exec_module(标准库子进程)#装入标准库subprocess
同步跑=标准库子进程.run#macOS /bin/ps

数字名模式=re.compile(r'[0-9]+\Z')#pid/tid数字名；ASCII数字且锚在串尾
僵尸态模式=re.compile(r'[ZXx]\Z')#僵尸或死状态
epoll标准输入模式=re.compile(r'^tfd:[ \t]+0\b')#epoll fdinfo 目标fd为0
ps三列模式=re.compile(r'^[ \t]*([0-9]+)[ \t]+([0-9]+)[ \t]+(.+?)[ \t]*\Z')#ps pid ppid lstart

__all__=(#仅中文公开名
    '进程身份','进程检查器内部','解析ProcStat','组内有活成员',
    'Posix进程检查器','Linux进程检查器','Mac进程检查器','创建进程检查器',
)#公开面结束

class 进程身份:#精确进程身份，防止PID复用后的拆除升级打到别人
    """PID 加上启动身份。"""
    def __init__(自身,pid,started):#钉pid与启动时刻
        """保存精确身份。"""
        自身.pid=pid#数字pid
        自身.started=started#启动时刻（Linux jiffies或macOS lstart）

def 默认读文件(路径):#生产默认：读文本文件
    """打开路径并读出全部文本。"""
    return open(路径,'r',encoding='utf-8').read()#读文本文件

def 默认列目录(路径):#生产默认：列目录
    """列出目录名。"""
    return os.listdir(路径)#列目录

def 默认读链接(路径):#生产默认：读符号链接
    """读符号链接目标。"""
    return os.readlink(路径)#链接目标

def 默认状态(路径):#生产默认：文件状态
    """取设备状态。"""
    信息=os.stat(路径)#stat
    return {'rdev':信息.st_rdev,'isCharacterDevice':文件状态.S_ISCHR(信息.st_mode)}#设备号与类型

def 默认打开(路径):#生产默认：只读打开
    """只读打开路径。"""
    return os.open(路径,os.O_RDONLY)#打开只读

def 默认执行(文件,参数):#生产默认：同步exec
    """同步执行并捕获标准输出文本。"""
    return 同步跑([文件]+list(参数),check=True,capture_output=True,text=True).stdout#同步exec

def 默认杀(pid,信号):#生产默认：发信号
    """向 pid 投递信号。"""
    os.kill(pid,信号)#发信号

class 进程检查器内部:#可注入系统调用边界
    """文件系统、进程表与信号系统调用周围的可测试边界。"""
    def __init__(自身,读文件=None,列目录=None,读链接=None,状态=None,打开=None,读=None,关闭=None,执行=None,杀=None):#注入或用生产默认
        """构造可测试边界。"""
        自身.读文件=读文件 if 读文件 is not None else 默认读文件#读文本文件
        自身.列目录=列目录 if 列目录 is not None else 默认列目录#列目录
        自身.读链接=读链接 if 读链接 is not None else 默认读链接#读符号链接
        自身.状态=状态 if 状态 is not None else 默认状态#取设备状态
        自身.打开=打开 if 打开 is not None else 默认打开#打开只读
        自身.读=读 if 读 is not None else 自身.默认读#定位读
        自身.关闭=关闭 if 关闭 is not None else os.close#关描述符
        自身.执行=执行 if 执行 is not None else 默认执行#同步exec
        自身.杀=杀 if 杀 is not None else 默认杀#发信号

    def 默认读(自身,fd,缓冲,长度,位置):#无注入时的定位读
        """把定位读落到 pread 或 lseek+read。"""
        if hasattr(os,'pread'):#有pread
            数据=os.pread(fd,长度,位置)#定位读
            缓冲[:len(数据)]=数据#写入调用方缓冲
            return len(数据)#读到的字节
        os.lseek(fd,位置,os.SEEK_SET)#定位
        数据=os.read(fd,长度)#读
        缓冲[:len(数据)]=数据#写入调用方缓冲
        return len(数据)#读到的字节

默认内部=进程检查器内部()#生产默认：真实系统调用

def 解析ProcStat(文本):#解析Linux /proc/<pid>/stat
    """解析 Linux `/proc/<pid>/stat` 里用到的字段，含括号包裹的 comm 文本；畸形输入为 None。"""
    开=文本.find('(')#comm左括号
    关=文本.rfind(')')#comm右括号（comm内可含括号）
    if 开<=0 or 关<=开:#没有合法comm包裹
        return None#畸形
    try:#数字字段可能畸形
        pid=int(文本[:开].strip())#括号前是pid
    except ValueError:#pid不是整数
        return None#畸形
    其余=文本[关+2:].strip().split()#括号后的空白分隔字段
    if len(其余)<20:#字段不够
        return None#畸形
    状态=其余[0] if 其余[0] else ''#状态字符
    try:#其余数字字段
        父pid=int(其余[1])#ppid
        进程组=int(其余[2])#pgrp
        会话=int(其余[3])#session
        终端设备=int(其余[4])#tty_nr
        前台组=int(其余[5])#tpgid
        启动=其余[19]#starttime
    except ValueError:#数字畸形
        return None#畸形
    if len(状态)!=1:#状态必须单字符
        return None#畸形
    return {'pid':pid,'parentPid':父pid,'pgrp':进程组,'session':会话,'state':状态,'ttyDevice':终端设备,'tpgid':前台组,'started':启动}#已校验字段

def 读LinuxStat(内部,pid):#读并解析一个pid的stat
    """读并解析一个 pid 的 `/proc/<pid>/stat`；不可读当作进程已走。"""
    try:#条目可能在读时消失
        return 解析ProcStat(内部.读文件('/proc/'+str(pid)+'/stat'))#畸形行也当缺失
    except OSError:#无法读/proc条目
        return None#当作进程已走

def Linux设备号(值):#归一化 tty_nr
    """把有符号 32 位设备号归一成无符号。"""
    return 值&0xFFFFFFFF#无符号32位

def 读Linux终端设备(内部,pid,tty设备,tid=None):#解析stdin是否仍是该终端
    """解析 stdin 是否仍是该终端设备；失败则 None。"""
    终端设备=Linux设备号(tty设备)#归一化
    if 终端设备==0:#无终端
        return None#不可比
    路径='/proc/'+str(pid)+'/fd/0' if tid is None else '/proc/'+str(pid)+'/task/'+str(tid)+'/fd/0'#stdin描述符
    try:#fd可能消失
        目标=内部.读链接(路径)#符号链接目标
        if 目标=='/dev/tty':#别名
            return 终端设备#用shell的tty_nr
        状态=内部.状态(路径)#直接设备
        if 状态['isCharacterDevice'] and Linux设备号(状态['rdev'])==终端设备:#设备号匹配
            return 终端设备#匹配
        return None#不匹配
    except OSError:#读不了stdin设备
        return None#当作不可比

def 组内有活成员(进程组号,内部=None):#Linux进程组存活探针
    """报告一个 Linux 进程组是否有正在执行的成员。False 表示组里只剩僵尸/死条目；None 表示进程表无法证明。"""
    if 内部 is None:#缺省真系统调用
        内部=默认内部#生产默认
    try:#/proc可能不可读
        条目列表=内部.列目录('/proc')#列全部条目
    except OSError:#读不了/proc
        return None#无法证明
    见过=False#是否见过该组的任何条目
    for 条目 in 条目列表:#每个/proc名
        if not 数字名模式.fullmatch(条目):#跳过非pid
            continue#下一条
        状态行=读LinuxStat(内部,int(条目))#读stat
        if 状态行 is None or 状态行['pgrp']!=进程组号:#不是该组
            continue#下一条
        见过=True#见过该组
        if not 僵尸态模式.fullmatch(状态行['state']):#非僵尸/死→有活成员
            return True#有活成员
    return False if 见过 else None#见过则只有僵尸；没见过则无法证明缺席

def 数字条目(内部,路径):#目录里的数字名
    """列目录中的数字名（pid/tid）；读失败返回 None，与空目录区分。"""
    try:#目录可能不可读
        return [int(条目) for 条目 in 内部.列目录(路径) if 数字名模式.fullmatch(条目)]#只收pid/tid
    except (ValueError,OSError):#读不了该目录或名字不是整数
        return None#读失败与空目录区分

def 读系统调用(内部,pid,tid):#读线程当前syscall
    """读 `/proc/<pid>/task/<tid>/syscall`；失败或用户态则 None。"""
    try:#条目可能不可读或正在跑用户态
        文本=内部.读文件('/proc/'+str(pid)+'/task/'+str(tid)+'/syscall').strip()#一行
        if 文本=='running' or 文本.startswith('-1 '):#不在内核或无法采样
            return None#当作不在等
        字段=文本.split()#空白分隔
        号=int(字段[0])#调用号（十进制）
        参数=[]#最多6个参数
        for 段 in 字段[1:7]:#十六进制参数
            参数.append(int(段,16))#解析
        return {'number':号,'args':参数}#已解析
    except (ValueError,OSError):#读失败或数字畸形
        return None#当作不在等

def 读内存(内部,pid,地址,长度):#读目标进程地址空间一块
    """读目标进程地址空间一块；失败则 None。"""
    fd=None#/proc/pid/mem
    try:#打开或读可能被拒绝
        fd=内部.打开('/proc/'+str(pid)+'/mem')#打开mem
        缓冲=bytearray(长度)#目标缓冲
        数=内部.读(fd,缓冲,长度,地址)#从address读
        if isinstance(数,bytes):#pread风格直接返回字节
            return 数#实际读到的
        return bytes(缓冲[:数])#实际读到的
    except OSError:#打不开或读不了
        return None#当作无法判断
    finally:#无论成败都关
        if fd is not None:#曾经打开
            内部.关闭(fd)#关mem

def fd集含标准输入(内部,pid,地址):#select fd_set是否含fd 0
    """select 的 readfds 最低位是否表示 stdin。"""
    if 地址==0:#空指针
        return False#不含
    内存=读内存(内部,pid,地址,8)#读8字节
    if 内存 is None or len(内存)==0:#读不了
        return False#不含
    return 内存[0]%2==1#最低位是stdin

def poll含标准输入(内部,pid,地址,数量):#pollfd数组是否在等stdin
    """pollfd 数组是否在等 stdin（fd=0 且 POLLIN）。"""
    if 地址==0 or 数量<=0:#空指针或空数组
        return False#不等
    内存=读内存(内部,pid,地址,min(数量,1024)*8)#最多看1024项
    if 内存 is None:#读不了
        return False#不等
    偏移=0#逐项
    while 偏移+8<=len(内存):#每项8字节：fd+events+revents
        fd=struct.unpack_from('<i',内存,偏移)[0]#fd小端
        事件=struct.unpack_from('<h',内存,偏移+4)[0]#events小端
        if fd==0 and (事件&0x001)!=0:#fd0+POLLIN
            return True#在等stdin
        偏移+=8#下一项
    return False#没有stdin等待

def epoll含标准输入(内部,pid,tid,epollfd):#epoll实例是否盯着stdin
    """epoll 实例的 fdinfo 是否登记了目标 fd 0。"""
    try:#fdinfo可能不可读
        文本=内部.读文件('/proc/'+str(pid)+'/task/'+str(tid)+'/fdinfo/'+str(epollfd))#epoll fdinfo
        for 行 in 文本.split('\n'):#逐行
            if epoll标准输入模式.match(行.strip()):#目标fd为0
                return True#盯着stdin
        return False#没有
    except OSError:#读失败
        return False#当作不等

系统调用表={#按arch的与stdin等待相关的调用号
    'x64':{'read':0,'select':23,'pselect':270,'poll':7,'ppoll':271,'epollWait':232,'epollPwait':281},#x86_64
    'x86_64':{'read':0,'select':23,'pselect':270,'poll':7,'ppoll':271,'epollWait':232,'epollPwait':281},#别名
    'arm64':{'read':63,'pselect':72,'ppoll':73,'epollPwait':22},#aarch64无select/poll/epoll_wait包装
    'aarch64':{'read':63,'pselect':72,'ppoll':73,'epollPwait':22},#别名
}#结束系统调用表

已支持系统调用表=list({id(表):表 for 表 in 系统调用表.values()}.values())#去重后的表清单

def Linux系统调用表(架构):#主表+备选表
    """本 arch 主表优先，其余已支持表作备选。"""
    主表=系统调用表.get(架构)#本arch主表
    if 主表 is None:#不支持
        return None#无
    return [主表]+[表 for 表 in 已支持系统调用表 if 表 is not 主表]#主表优先

def 系统调用在等标准输入(内部,pid,tid,系统调用,表列表):#当前syscall是否在等stdin
    """当前 syscall 是否在等 fd 0。"""
    参数=系统调用['args']#参数表
    a0=参数[0] if len(参数)>0 else 0#第一参
    a1=参数[1] if len(参数)>1 else 0#第二参
    a2=参数[2] if len(参数)>2 else 0#第三参
    for 表 in 表列表:#逐表匹配
        if 系统调用['number']==表['read']:#read(0,...)
            return a0==0#fd为0
        if 系统调用['number']==表.get('select') or 系统调用['number']==表['pselect']:#select/pselect
            return a0>=1 and fd集含标准输入(内部,pid,a1)#nfds≥1且readfds含stdin
        if 系统调用['number']==表.get('poll') or 系统调用['number']==表['ppoll']:#poll/ppoll
            return a1>=1 and poll含标准输入(内部,pid,a0,a1)#nfds≥1且数组含stdin POLLIN
        if 系统调用['number']==表.get('epollWait') or 系统调用['number']==表['epollPwait']:#epoll_wait/pwait
            return a2>=1 and epoll含标准输入(内部,pid,tid,a0)#maxevents≥1且epfd盯着stdin
    return False#其他调用不算等stdin

def 静止(状态):#是否静止
    """僵尸与死状态回答在表里但从不回答仍在跑。"""
    return 状态 is not None and 僵尸态模式.fullmatch(状态) is not None#僵尸/死

def 建进程树(条目列表,根pid):#后序遍历：孩子先于祖先
    """从带父指针的条目建后序进程树。"""
    按pid={条目['pid']:条目 for 条目 in 条目列表}#pid→条目
    根=按pid.get(根pid)#根
    if 根 is None:#根不在表里
        return []#空
    按父={}#父→孩子
    for 条目 in 条目列表:#建邻接
        孩子列表=按父.get(条目['parentPid'])#已有孩子
        if 孩子列表 is None:#尚无
            孩子列表=[]#新建
            按父[条目['parentPid']]=孩子列表#写回
        孩子列表.append(条目)#加上这个
    已访=set()#防环
    结果=[]#后序结果
    def 访问(条目):#深度优先
        """先孩子再自己。"""
        if 条目['pid'] in 已访:#已访
            return#跳过
        已访.add(条目['pid'])#记下
        for 孩子 in 按父.get(条目['pid'],[]):#先孩子
            访问(孩子)#递归
        结果.append(进程身份(条目['pid'],条目['started']))#再自己
    访问(根)#从根走
    return 结果#孩子在前

class Posix进程快照:#一次POSIX表观察
    """一次进程表观察；complete 表示扫描是否未漏不可读行。"""
    def __init__(自身,行列表,完整):#钉行集与完整性
        """保存行与完整性。"""
        自身._行列表=行列表#行
        自身.complete=完整#完整性
        自身._按pid={行['pid']:行 for 行 in 行列表}#按pid索引

    def 树(自身,根pid):#后序树
        """观察到的根与子孙，孩子在前。"""
        return 建进程树(自身._行列表,根pid)#复用建树

    def 会话(自身,会话号):#会话成员
        """观察到的会话成员；表省略会话 id 时为空。"""
        return [进程身份(行['pid'],行['started']) for 行 in 自身._行列表 if 行.get('session')==会话号]#匹配才收

    def 存活(自身,身份):#快照内探活
        """该精确身份当时是否为非静止进程。"""
        行=自身._按pid.get(身份.pid)#按pid取
        return 行 is not None and 行['started']==身份.started and not 静止(行.get('state'))#身份匹配且非静止

class Posix进程检查器:#POSIX共用：组/进程信号
    """POSIX 共用：组/进程信号；子类补平台前台/快照/存活。"""
    def __init__(自身,内部):#注入系统调用
        """保存 internals。"""
        自身.内部=内部#系统调用边界

    def 信号组(自身,进程组号,信号):#负pid=整组
        """向整组投递信号。"""
        自身.内部.杀(-进程组号,信号)#向组投递

    def 信号进程(自身,身份,信号):#精确身份仍活才打
        """按精确身份发信号，避免 PID 复用。"""
        if 自身.是否存活(身份):#仍是原进程
            自身.内部.杀(身份.pid,getattr(signal,信号) if isinstance(信号,str) else 信号)#投递

    def 前台进程组(自身,壳pid):#子类实现
        """平台前台 pgid。"""
        raise NotImplementedError('foregroundPgid')#子类必须实现

    def 是否在等标准输入(自身,进程组号,壳pid):#子类实现
        """平台 stdin 等待。"""
        raise NotImplementedError('isStdinWaiting')#子类必须实现

    def 快照(自身):#子类实现
        """平台共享快照。"""
        raise NotImplementedError('snapshot')#子类必须实现

    def 是否存活(自身,身份):#子类实现
        """平台存活。"""
        raise NotImplementedError('isAlive')#子类必须实现

class Linux进程检查器(Posix进程检查器):#Linux：/proc
    """Linux：经 `/proc` 做前台、stdin 等待、快照与存活检查。"""
    def __init__(自身,架构,内部):#钉arch以选syscall号
        """交给 POSIX 基类并保存架构。"""
        super().__init__(内部)#保存internals
        自身.架构=架构#CPU架构

    def 前台进程组(自身,壳pid):#shell的tpgid
        """shell 的 tpgid；≤0 表示无前台。"""
        状态行=读LinuxStat(自身.内部,壳pid)#stat字段
        if 状态行 is None:#进程已走
            return None#无前台
        前台组=状态行['tpgid']#tpgid
        return 前台组 if 前台组>0 else None#≤0表示无前台

    def 是否在等标准输入(自身,进程组号,壳pid):#组内是否有线程在等shell终端stdin
        """组内是否有线程在等 shell 终端 stdin。"""
        表列表=Linux系统调用表(自身.架构)#ABI表
        if 表列表 is None:#未知arch无法判断
            return False#无法判断
        壳=读LinuxStat(自身.内部,壳pid)#shell stat
        if 壳 is None:#shell已走
            return False#否
        终端设备=读Linux终端设备(自身.内部,壳pid,壳['ttyDevice'])#shell终端
        if 终端设备 is None:#没有可比对的终端
            return False#否
        进程列表=数字条目(自身.内部,'/proc')#每个进程
        if 进程列表 is None:#/proc不可读
            return False#否
        for pid in 进程列表:#每个进程
            状态行=读LinuxStat(自身.内部,pid)#可能已消失
            if 状态行 is None or 状态行['pgrp']!=进程组号:#不是该组
                continue#下个进程
            线程列表=数字条目(自身.内部,'/proc/'+str(pid)+'/task')#每个线程
            if 线程列表 is None:#task不可读
                continue#下个进程
            for tid in 线程列表:#每个线程
                调用=读系统调用(自身.内部,pid,tid)#当前调用
                if 调用 is not None and 系统调用在等标准输入(自身.内部,pid,tid,调用,表列表) and 读Linux终端设备(自身.内部,pid,状态行['ttyDevice'],tid)==终端设备:#在等stdin且同终端
                    return True#命中
        return False#没有线程在等

    def 是否存活(自身,身份):#启动时刻匹配且非僵尸/死
        """启动时刻匹配且非僵尸/死。"""
        状态行=读LinuxStat(自身.内部,身份.pid)#当前stat
        if 状态行 is None:#进程已走
            return False#不活
        return 状态行['started']==身份.started and not 静止(状态行['state'])#身份仍是原进程且能执行

    def 快照(自身):#一次/proc快照
        """一次 `/proc` 快照；目录不可读则抛错。"""
        进程列表=数字条目(自身.内部,'/proc')#目录项
        if 进程列表 is None:#不可读
            raise 本地子进程错误('Cannot inspect processes: /proc directory is unreadable')#不可读
        完整=True#完整性
        行列表=[]#行
        for pid in 进程列表:#每个pid
            状态行=读LinuxStat(自身.内部,pid)#可能已消失
            if 状态行 is None:#漏行
                完整=False#不完整
                continue#跳过
            行列表.append({'pid':pid,'parentPid':状态行['parentPid'],'started':状态行['started'],'session':状态行['session'],'state':状态行['state']})#收下
        return Posix进程快照(行列表,完整)#快照

def mac进程表(内部):#一次/bin/ps快照
    """一次 `/bin/ps -axo pid=,ppid=,lstart=` 快照；返回行与完整性。"""
    文本=内部.执行('/bin/ps',['-axo','pid=,ppid=,lstart='])#整表
    完整=True#完整性
    行列表=[]#结果
    for 行 in 文本.split('\n'):#每行pid ppid lstart
        匹配=ps三列模式.match(行)#三列
        if 匹配 is None:#空行或畸形
            if len(行.strip())>0:#非空畸形
                完整=False#不完整
            continue#跳过
        行列表.append({'pid':int(匹配.group(1)),'parentPid':int(匹配.group(2)),'started':匹配.group(3),'session':None,'state':None})#lstart当启动身份
    return {'rows':行列表,'complete':完整}#表

class Mac进程检查器(Posix进程检查器):#macOS：ps
    """macOS：经 `/bin/ps` 做前台、快照与存活检查；不采样 syscall。"""
    def 前台进程组(自身,壳pid):#ps -o tpgid
        """`ps -o tpgid=`；≤0 或非整数则无前台。"""
        try:#进程可能已走
            值=int(自身.内部.执行('/bin/ps',['-o','tpgid=','-p',str(壳pid)]).strip())#只打tpgid
            return 值 if 值>0 else None#≤0则无前台
        except (ValueError,OSError,标准库子进程.CalledProcessError):#ps失败或非整数
            return None#当作没有前台

    def 是否在等标准输入(自身,进程组号,壳pid):#macOS不采样syscall
        """macOS 不采样 syscall，无法判断则不当作在等。"""
        return False#无法判断则不当作在等

    def 是否存活(自身,身份):#ps表里仍有同一pid+lstart
        """ps 表里仍有同一 pid+lstart。"""
        for 条目 in mac进程表(自身.内部)['rows']:#精确身份
            if 条目['pid']==身份.pid and 条目['started']==身份.started:#命中
                return True#仍活
        return False#已走

    def 快照(自身):#一次ps快照
        """一次 ps 快照。"""
        表=mac进程表(自身.内部)#表
        return Posix进程快照(表['rows'],表['complete'])#包成共享观察

def 节点平台():#对齐Node process.platform
    """把 sys.platform 粗映射到 Node 平台名。"""
    名=sys.platform#本机
    if 名=='win32':#Windows
        return 'win32'#Node名
    if 名=='darwin':#macOS
        return 'darwin'#Node名
    if 名.startswith('linux'):#Linux
        return 'linux'#Node名
    return 名#原样

def 机器架构():#对齐Node process.arch粗映射
    """把本机 machine 粗映射到 Node arch 名。"""
    机器=平台库.machine().lower()#本机
    if 机器 in ('x86_64','amd64'):#x64
        return 'x64'#Node名
    if 机器 in ('aarch64','arm64'):#arm64
        return 'arm64'#Node名
    return 机器#原样

def 创建进程检查器(平台=None,架构=None,内部=None):#按平台选实现
    """创建受支持平台的检查器，或在插件加载时失败。"""
    if 平台 is None:#默认本机
        平台=节点平台()#对齐Node
    if 架构 is None:#默认本机arch
        架构=机器架构()#本机
    if 内部 is None:#默认真系统调用
        内部=默认内部#生产默认
    if 平台=='linux':#Linux
        return Linux进程检查器(架构,内部)#/proc
    if 平台=='darwin':#macOS
        return Mac进程检查器(内部)#/bin/ps
    raise 本地子进程错误('subprocess-local: terminal inspection is unsupported on platform '+str(平台))#其余平台加载失败
