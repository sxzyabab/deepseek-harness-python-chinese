"""跨进程写所有权锁，覆盖一个会话产物目录的整个写句柄生命周期。"""
import os,sys#路径与平台
from ..会话持久化.预备 import 持久化错误#持久化错误基类

租约文件名='session.lock'#锁文件名

class 会话已有写主错误(持久化错误):#已有写主
    """另一持有者仍占锁时。"""
    def __init__(自身,标识):#构造
        """记下被争用的会话身份。"""
        自身.id=标识#会话id
        super().__init__(f'session {标识!s} is already owned by another writer')#文案

class 会话写租约:#会话写租约
    """一把已持写锁；释放关闭描述符或句柄。"""
    def __init__(自身,种类,句柄,路径=None):#仅内部构造
        """记下已持锁。"""
        自身.种类=种类#posix或win32
        自身.句柄=句柄#文件对象或句柄
        自身.路径=路径#锁文件路径
        自身.已释放=False#是否已释放

    @staticmethod#取得租约
    def 取得(目录,标识):#取得租约
        """取得会话目录的内核写锁（同步）。"""
        os.makedirs(目录,mode=0o700,exist_ok=True)#确保目录存在
        路径=os.path.join(目录,租约文件名)#锁文件路径
        if sys.platform=='win32':#Windows分支
            import msvcrt#Win32文件锁
            文件=open(路径,'a+b')#打开或创建
            try:#尝试加锁
                文件.seek(0)#定位
                if 文件.read(1)==b'':#空则写一字节
                    文件.write(b'\0')#占位
                    文件.flush()#落盘
                文件.seek(0)#回到起点
                msvcrt.locking(文件.fileno(),msvcrt.LK_NBLCK,1)#非阻塞锁
            except OSError:#争用或失败
                文件.close()#关闭
                raise 会话已有写主错误(标识)#映射为已有写主
            return 会话写租约('win32',文件,路径)#返回Win32租约
        import fcntl#POSIX flock
        for _ in range(3):#最多三轮
            文件=open(路径,'a+b')#打开或创建
            try:#尝试加锁并校验inode
                try:#非阻塞排他锁
                    fcntl.flock(文件.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)#取得锁
                except BlockingIOError:#争用
                    文件.close()#关闭
                    raise 会话已有写主错误(标识)#映射
                已锁=os.fstat(文件.fileno())#已锁文件的stat
                try:#路径当前stat
                    当前=os.stat(路径)#stat
                except FileNotFoundError:#已消失
                    当前=None#无
                if 当前 is not None and 当前.st_ino==已锁.st_ino and 当前.st_dev==已锁.st_dev:#inode仍匹配
                    return 会话写租约('posix',文件,路径)#返回POSIX租约
            except 会话已有写主错误:#争用
                raise#继续抛出
            except OSError:#加锁或校验失败
                文件.close()#关闭描述符
                raise#继续抛出
            文件.close()#关闭后重试
        raise 会话已有写主错误(标识)#重试耗尽视为争用

    def 释放(自身):#释放租约
        """通过关闭描述符释放内核锁。幂等。"""
        if 自身.已释放:#已释放
            return#直接返回
        自身.已释放=True#标记已释放
        if 自身.种类=='win32':#Win32分支
            import msvcrt#Win32文件锁
            try:#尝试解锁
                自身.句柄.seek(0)#定位
                msvcrt.locking(自身.句柄.fileno(),msvcrt.LK_UNLCK,1)#解锁
            except OSError:#解锁失败忽略
                pass#忽略
        else:#POSIX
            import fcntl#POSIX flock
            try:#解锁
                fcntl.flock(自身.句柄.fileno(),fcntl.LOCK_UN)#解锁
            except OSError:#忽略
                pass#忽略
        自身.句柄.close()#关闭描述符

__all__=['租约文件名','会话已有写主错误','会话写租约']#公开面
