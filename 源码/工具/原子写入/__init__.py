"""零依赖的原子文件替换与写方协调。
`原子写文件` 以独占创建和调用方权限位写入随机后缀兄弟文件，再改名覆盖目标，因此读者只看到旧的或新的完整内容，被替换文件最终恰好带有声明的 mode。`带文件锁` 通过 `wx` 创建的 `<file>.lock` 兄弟跨进程串行化同一文件的写方，使读-改-写周期无法复活另一写方刚替换掉的状态；读者保持无锁，因为改名提交是原子的。
"""
import os,errno,time,secrets#路径、错误码、退避等待与随机临时名

# 写锁协议常量。这些是跨进程写协议的健壮性不变量，不是部署可调项：争用通常在重试期限内解决，过期则让争用方失败，而不猜测现有锁是否仍有所有者。
锁重试初始毫秒=20#首次锁重试间隔毫秒
锁重试上限毫秒=200#锁重试间隔上限毫秒
锁超时毫秒=2000#等待写锁的截止毫秒

def 取字段(对象,键):#读取映射或对象上的必填字段
    """读取映射或对象上的必填字段（对齐 TS 属性访问）。"""
    if isinstance(对象,dict):#映射
        return 对象[键]#按键
    return getattr(对象,键)#按属性

def 试取(对象,键):#读取可选字段
    """读取可选字段，缺席为 None。"""
    if isinstance(对象,dict):#映射
        return 对象.get(键)#按键
    return getattr(对象,键,None)#按属性

def 是否已存在(错误):#独占创建是否因路径已存在而失败
    """独占创建是否因路径已存在而失败。"""
    if getattr(错误,'code',None)=='EEXIST':#带Node风格码
        return True#争用
    return isinstance(错误,OSError) and 错误.errno==errno.EEXIST#Python已存在

def 原子写文件(文件名,内容,选项):#一步原子替换目标文件
    """一步原子替换 `文件名` 为 `内容`，并创建父目录。

    选项（对齐上游 `WriteFileAtomicOptions`）：
    - `mode`：打在新临时 inode 上并随改名带走的权限位（受进程 umask 约束）；必填。
    - `dirMode`：本调用所创建父目录的权限位（受 umask 约束；已有目录保留其 mode）。省略则用 mkdir 默认值——树里存放用户私有数据时传 `0o700`。

    内容先写入以独占创建（`wx`）打开的随机后缀兄弟：打开拒绝跟随种在临时路径上的符号链接，新 inode 带着 `mode` 穿过改名，因此替换权限更宽的文件时无需 chmod 竞态即可收窄。改名也会替换作为符号链接的目标本身，而不是写穿到其指向对象；同目录兄弟使改名留在同一文件系统。任何失败都会删除临时文件并再抛出失败。崩溃耐久性（fsync）不在范围内。
    """
    父目录=os.path.dirname(文件名) or '.'#目标父目录；无目录分量时对齐 Node `path.dirname` 的 '.'
    目录权限=试取(选项,'dirMode')#新建父目录权限位
    if 目录权限 is None:#省略dirMode则用mkdir默认
        os.makedirs(父目录,exist_ok=True)#递归创建缺失的祖先目录
    else:#有dirMode才传给makedirs
        os.makedirs(父目录,mode=目录权限,exist_ok=True)#带权限递归创建
    # TODO(settings-atomic-durability):使用会fsync文件与父目录并在Windows上保留仅所有者权限的替换。
    临时=文件名+'.'+secrets.token_hex(6)+'.tmp'#同目录随机后缀临时路径
    权限=取字段(选项,'mode')#替换inode的权限位
    try:#先写临时文件再改名提交
        标志=os.O_CREAT|os.O_EXCL|os.O_WRONLY#独占创建
        if os.name=='nt':#Windows
            标志|=os.O_BINARY#Windows二进制
        描述符=os.open(临时,标志,权限)#独占创建临时inode
        try:#写入内容
            os.write(描述符,内容.encode('utf-8'))#按UTF-8写入完整内容
        finally:#关掉描述符
            os.close(描述符)#关掉
        os.replace(临时,文件名)#原子改名覆盖目标
    except BaseException as 错误:#写或改名失败；清理临时后再抛，含中断路径
        try:#尽力删掉临时文件
            os.unlink(临时)#删除临时
        except OSError:#临时可能未建成或已搬走；只有这类删失败能到这里
            pass#吞掉清理失败
        raise 错误#原样再抛失败

def 带文件锁(文件名,操作):#跨进程串行化同一文件的写方
    """围绕一次操作为 `文件名` 持有跨进程写锁。锁是 `wx` 创建的兄弟（`<文件名>.lock`）；与 `原子写文件` 基于改名的提交配对后，读者保持无锁，只有写方争用。争用按指数退避，截止后以超时错误失败。争用方从不删除已有锁，因为文件年龄不能证明所有者已停；孤儿恢复是运维动作。父目录必须已存在。"""
    锁路径=文件名+'.lock'#写锁兄弟路径
    截止=time.time()*1000.0+锁超时毫秒#等待锁的截止时刻
    间隔=锁重试初始毫秒#当前退避间隔
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
            if not 是否已存在(错误):#非争用错误直接抛出
                raise 错误#原样抛出
        if time.time()*1000.0>=截止:#已过等待截止
            raise Exception('atomic-write: timed out waiting for the writer lock at '+锁路径)#超时等待写锁
        time.sleep(间隔/1000.0)#按当前间隔等待
        间隔=min(间隔*2,锁重试上限毫秒)#指数增大间隔并封顶
    try:#持锁执行操作
        return 操作()#跑完读-改-写后交回结果
    finally:#无论成败都释放锁
        try:#删除锁文件
            os.unlink(锁路径)#删除锁文件
        except OSError:#锁文件可能已被运维清掉；只有这类删失败能到这里
            pass#吞掉释放清理失败
