import os,errno,time,secrets
__all__=[
    '锁重试初始毫秒','锁重试上限毫秒','锁超时毫秒',
    '是否已存在','原子写文件','带文件锁','原子写入错误',
]

# 写锁协议常量。这些是跨进程写协议的健壮性不变量，不是部署可调项：争用通常在重试期限内解决，过期则让争用方失败，而不猜测现有锁是否仍有所有者。
锁重试初始毫秒=20
锁重试上限毫秒=200
锁超时毫秒=2000
Windows瞬时改名错误=frozenset({'EACCES','EBUSY','EPERM'})
Windows改名重试初始毫秒=20
Windows改名重试上限毫秒=200
Windows改名重试次数=8

class 原子写入错误(Exception):
    """原子写入或写锁失败。"""
    def __init__(自身,消息):
        super().__init__(消息)

def 是否已存在(错误):
    """独占创建是否因路径已存在而失败。"""
    return isinstance(错误,OSError) and 错误.errno==errno.EEXIST

def 是否Windows瞬时改名错误(错误):
    """是否 Windows 报告对原子替换的瞬时干扰。"""
    if os.name!='nt':
        return False
    if not isinstance(错误,OSError):
        return False
    名=errno.errorcode.get(错误.errno)
    return 名 in Windows瞬时改名错误

def 原子改名临时(临时,文件名):
    """目标改名；Windows 对瞬时干扰有界重试。"""
    间隔=Windows改名重试初始毫秒
    重试=0
    while True:
        try:
            os.replace(临时,文件名)
            return
        except OSError as 错误:
            if not 是否Windows瞬时改名错误(错误):
                raise 错误
            if 重试>=Windows改名重试次数:
                raise 错误
        time.sleep(间隔/1000.0)
        间隔=min(间隔*2,Windows改名重试上限毫秒)
        重试+=1

def 是否锁争用(错误,锁路径):
    """独占创建是否因已有锁而失败；EPERM 仅在锁路径存在时算争用。"""
    if 是否已存在(错误):
        return True
    if not isinstance(错误,OSError) or errno.errorcode.get(错误.errno)!='EPERM':
        return False
    try:
        os.lstat(锁路径)
        return True
    except OSError:
        return False

def 原子写文件(文件名,内容,选项):
    """一步原子替换 `文件名` 为 `内容`，并创建父目录。

    选项：
    - `mode`：打在新临时 inode 上并随改名带走的权限位（受进程 umask 约束）；必填。
    - `dirMode`：本调用所创建父目录的权限位（受 umask 约束；已有目录保留其 mode）。省略则用 mkdir 默认值——树里存放用户私有数据时传 `0o700`。

    内容先写入以独占创建（`wx`）打开的随机后缀兄弟：打开拒绝跟随种在临时路径上的符号链接，新 inode 带着 `mode` 穿过改名，因此替换权限更宽的文件时无需 chmod 竞态即可收窄。改名也会替换作为符号链接的目标本身，而不是写穿到其指向对象；同目录兄弟使改名留在同一文件系统。Windows 替换对瞬时 `EACCES`、`EBUSY` 和 `EPERM` 在有界间隔内重试。任何失败都会删除临时文件并再抛出失败。崩溃耐久性（fsync）不在范围内。
    """
    父目录=os.path.dirname(文件名) or '.'#无目录分量时与 Node path.dirname 一样落到 '.'
    if 'dirMode' not in 选项:
        os.makedirs(父目录,exist_ok=True)
    else:
        os.makedirs(父目录,mode=选项['dirMode'],exist_ok=True)
    临时=文件名+'.'+secrets.token_hex(6)+'.tmp'
    权限=选项['mode']
    临时已建=False
    try:
        标志=os.O_CREAT|os.O_EXCL|os.O_WRONLY
        if os.name=='nt':
            标志|=os.O_BINARY
        描述符=os.open(临时,标志,权限)
        临时已建=True
        try:
            os.write(描述符,内容.encode('utf-8'))
        finally:
            os.close(描述符)
        原子改名临时(临时,文件名)
        临时已建=False
    finally:
        if 临时已建:
            try:
                os.unlink(临时)
            except OSError:
                pass#临时可能未建成或已搬走；只有这类删失败能到这里

def 带文件锁(文件名,操作,选项=None):
    """围绕一次操作为 `文件名` 持有跨进程写锁。锁是 `wx` 创建的兄弟（`<文件名>.lock`）；与 `原子写文件` 基于改名的提交配对后，读者保持无锁，只有写方争用。`EEXIST` 直接是争用；`EPERM` 仅在新鲜 lstat 确认锁路径存在时才是争用。Windows 对一次未确认的 EPERM 再试。争用按指数退避，截止后以超时错误失败。争用方从不删除已有锁。父目录必须已存在。"""
    if 选项 is None:
        选项={}
    锁路径=文件名+'.lock'
    等待毫秒=选项['waitMs'] if 'waitMs' in 选项 else 锁超时毫秒
    截止=time.time()*1000.0+等待毫秒
    间隔=锁重试初始毫秒
    已重试未确认权限=False
    while True:
        try:
            标志=os.O_CREAT|os.O_EXCL|os.O_WRONLY
            if os.name=='nt':
                标志|=os.O_BINARY
            描述符=os.open(锁路径,标志,0o600)
            try:
                os.write(描述符,(str(os.getpid())+'\n').encode('utf-8'))
            finally:
                os.close(描述符)
            break
        except OSError as 错误:
            if not 是否锁争用(错误,锁路径):
                if os.name!='nt' or errno.errorcode.get(错误.errno)!='EPERM' or 已重试未确认权限:
                    raise 错误
                已重试未确认权限=True
        if time.time()*1000.0>=截止:
            raise 原子写入错误('原子写入: 等待写锁超时')
        time.sleep(间隔/1000.0)
        间隔=min(间隔*2,锁重试上限毫秒)
    try:
        return 操作()
    finally:
        try:
            os.unlink(锁路径)
        except OSError:
            pass#锁文件可能已被运维清掉；只有这类删失败能到这里
