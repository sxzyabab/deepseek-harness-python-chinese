import os,errno,time,secrets#路径、错误码、退避等待与随机临时名
__all__=[#仅中文公开名
    '锁重试初始毫秒','锁重试上限毫秒','锁超时毫秒',
    '是否已存在','原子写文件','带文件锁','原子写入错误',
]#公开面结束

# 写锁协议常量。这些是跨进程写协议的健壮性不变量，不是部署可调项：争用通常在重试期限内解决，过期则让争用方失败，而不猜测现有锁是否仍有所有者。
锁重试初始毫秒=20#首次锁重试间隔毫秒
锁重试上限毫秒=200#锁重试间隔上限毫秒
锁超时毫秒=2000#等待写锁的截止毫秒
Windows瞬时改名错误=frozenset({'EACCES','EBUSY','EPERM'})#Windows瞬时改名错误码名
Windows改名重试初始毫秒=20#改名首次退避
Windows改名重试上限毫秒=200#改名退避上限
Windows改名重试次数=8#改名最多重试次数

class 原子写入错误(Exception):#本包异常基类
    """原子写入或写锁失败。"""
    def __init__(自身,消息):#记下英文消息
        """用原样英文消息构造。"""
        super().__init__(消息)#英文消息

def 是否已存在(错误):#独占创建是否因路径已存在而失败
    """独占创建是否因路径已存在而失败。"""
    return isinstance(错误,OSError) and 错误.errno==errno.EEXIST#Python已存在

def 是否Windows瞬时改名错误(错误):#Windows瞬时干扰
    """是否 Windows 报告对原子替换的瞬时干扰。"""
    if os.name!='nt':#非 Windows
        return False#否
    if not isinstance(错误,OSError):#非系统错误
        return False#否
    名=errno.errorcode.get(错误.errno)#错误码名
    return 名 in Windows瞬时改名错误#在集合内

def 原子改名临时(临时,文件名):#带重试的原子改名
    """目标改名；Windows 对瞬时干扰有界重试。"""
    间隔=Windows改名重试初始毫秒#当前退避
    重试=0#已重试次数
    while True:#直到成功或超限
        try:#尝试改名
            os.replace(临时,文件名)#原子改名覆盖
            return#成功
        except OSError as 错误:#改名失败
            if not 是否Windows瞬时改名错误(错误):#非瞬时
                raise 错误#原样抛
            if 重试>=Windows改名重试次数:#超限
                raise 错误#最终失败
        time.sleep(间隔/1000.0)#退避
        间隔=min(间隔*2,Windows改名重试上限毫秒)#指数增大
        重试+=1#计数

def 是否锁争用(错误,锁路径):#独占创建是否因锁争用
    """独占创建是否因已有锁而失败；EPERM 仅在锁路径存在时算争用。"""
    if 是否已存在(错误):#EEXIST
        return True#争用
    if not isinstance(错误,OSError) or errno.errorcode.get(错误.errno)!='EPERM':#非EPERM
        return False#否
    try:#EPERM时确认锁存在
        os.lstat(锁路径)#探测
        return True#存在则争用
    except OSError:#锁存在未证实
        return False#保持原始EPERM权威

def 原子写文件(文件名,内容,选项):#一步原子替换目标文件
    """一步原子替换 `文件名` 为 `内容`，并创建父目录。

    选项（对齐上游 `WriteFileAtomicOptions`）：
    - `mode`：打在新临时 inode 上并随改名带走的权限位（受进程 umask 约束）；必填。
    - `dirMode`：本调用所创建父目录的权限位（受 umask 约束；已有目录保留其 mode）。省略则用 mkdir 默认值——树里存放用户私有数据时传 `0o700`。

    内容先写入以独占创建（`wx`）打开的随机后缀兄弟：打开拒绝跟随种在临时路径上的符号链接，新 inode 带着 `mode` 穿过改名，因此替换权限更宽的文件时无需 chmod 竞态即可收窄。改名也会替换作为符号链接的目标本身，而不是写穿到其指向对象；同目录兄弟使改名留在同一文件系统。Windows 替换对瞬时 `EACCES`、`EBUSY` 和 `EPERM` 在有界间隔内重试。任何失败都会删除临时文件并再抛出失败。崩溃耐久性（fsync）不在范围内。
    """
    父目录=os.path.dirname(文件名) or '.'#目标父目录；无目录分量时对齐 Node `path.dirname` 的 '.'
    if 'dirMode' not in 选项:#省略dirMode则用mkdir默认
        os.makedirs(父目录,exist_ok=True)#递归创建缺失的祖先目录
    else:#有dirMode才传给makedirs
        os.makedirs(父目录,mode=选项['dirMode'],exist_ok=True)#带权限递归创建
    # TODO(settings-atomic-durability):使用会fsync文件与父目录并在Windows上保留仅所有者权限的替换。
    临时=文件名+'.'+secrets.token_hex(6)+'.tmp'#同目录随机后缀临时路径
    权限=选项['mode']#替换inode的权限位
    临时已建=False#是否已独占建成临时文件
    try:#先写临时文件再改名提交
        标志=os.O_CREAT|os.O_EXCL|os.O_WRONLY#独占创建
        if os.name=='nt':#Windows
            标志|=os.O_BINARY#Windows二进制
        描述符=os.open(临时,标志,权限)#独占创建临时inode
        临时已建=True#建成
        try:#写入内容
            os.write(描述符,内容.encode('utf-8'))#按UTF-8写入完整内容
        finally:#关掉描述符
            os.close(描述符)#关掉
        原子改名临时(临时,文件名)#带Windows重试的原子改名
        临时已建=False#改名后临时路径不再存在
    finally:#失败则清理临时
        if 临时已建:#仍留着临时文件
            try:#尽力删掉临时文件
                os.unlink(临时)#删除临时
            except OSError:#临时可能未建成或已搬走；只有这类删失败能到这里
                pass#吞掉清理失败

def 带文件锁(文件名,操作,选项=None):#跨进程串行化同一文件的写方
    """围绕一次操作为 `文件名` 持有跨进程写锁。锁是 `wx` 创建的兄弟（`<文件名>.lock`）；与 `原子写文件` 基于改名的提交配对后，读者保持无锁，只有写方争用。`EEXIST` 直接是争用；`EPERM` 仅在新鲜 lstat 确认锁路径存在时才是争用。Windows 对一次未确认的 EPERM 再试。争用按指数退避，截止后以超时错误失败。争用方从不删除已有锁。父目录必须已存在。"""
    if 选项 is None:#缺省选项
        选项={}#空
    锁路径=文件名+'.lock'#写锁兄弟路径
    等待毫秒=选项['waitMs'] if 'waitMs' in 选项 else 锁超时毫秒#等待上限
    截止=time.time()*1000.0+等待毫秒#等待锁的截止时刻
    间隔=锁重试初始毫秒#当前退避间隔
    已重试未确认权限=False#是否已重试未确认EPERM
    while True:#直到拿到锁或超时
        try:#尝试独占创建锁文件
            标志=os.O_CREAT|os.O_EXCL|os.O_WRONLY#独占创建
            if os.name=='nt':#Windows
                标志|=os.O_BINARY#Windows二进制
            描述符=os.open(锁路径,标志,0o600)#wx创建锁
            try:#写入pid
                os.write(描述符,(str(os.getpid())+'\n').encode('utf-8'))#写入pid
            finally:#关掉描述符
                os.close(描述符)#关掉
            break#拿到锁，离开重试循环
        except OSError as 错误:#创建锁失败
            if not 是否锁争用(错误,锁路径):#非争用
                if os.name!='nt' or errno.errorcode.get(错误.errno)!='EPERM' or 已重试未确认权限:#不可重试
                    raise 错误#原样抛出
                已重试未确认权限=True#标记已重试
        if time.time()*1000.0>=截止:#已过等待截止
            raise 原子写入错误('atomic-write: timed out waiting for the writer lock at '+锁路径)#超时等待写锁
        time.sleep(间隔/1000.0)#按当前间隔等待
        间隔=min(间隔*2,锁重试上限毫秒)#指数增大间隔并封顶
    try:#持锁执行操作
        return 操作()#跑完读-改-写后交回结果
    finally:#无论成败都释放锁
        try:#删除锁文件
            os.unlink(锁路径)#删除锁文件
        except OSError:#锁文件可能已被运维清掉；只有这类删失败能到这里
            pass#吞掉释放清理失败
