# 上游 npm：node-pty（伪终端分配）。Python 面用标准库 pty/subprocess 对齐 spawn 会话 API。
# 仅供 pydsh 内相对导入；禁止再以顶层名 import node_pty。

import os,signal,struct,threading#路径、信号、窗尺寸打包与读线程
from subprocess import Popen as 拉起进程#子进程

__all__=['spawn']#仅中文公开名；模块本身即伪终端库

class 拆除器:#对齐 node-pty 监听返回的 {dispose}
    """一次监听的拆除柄。"""
    def __init__(自身,拆除函数):
        """记下拆除函数。"""
        自身._拆除=拆除函数#拆除函数
        自身._已拆=False#是否已拆

    def dispose(自身):
        """幂等拆除。"""
        if 自身._已拆:#已拆
            return#结束
        自身._已拆=True#记下
        自身._拆除()#执行

class 伪终端会话:#对齐 IPty
    """已分配的本地伪终端会话。"""
    def __init__(自身,进程,主端,平台):
        """钉进程与主端 fd。"""
        自身.pid=进程.pid#壳 pid
        自身._进程=进程#Popen
        自身._主端=主端#主端 fd；Windows 无 PTY 时为 None
        自身._平台=平台#win32 或其它
        自身._数据监听=[]#onData 回调
        自身._退出监听=[]#onExit 回调
        自身._锁=threading.Lock()#监听表互斥
        自身._已退出=False#是否已发退出
        自身._已暂停=False#pause 门闩
        自身._暂停门=threading.Event()#resume 开门
        自身._暂停门.set()#默认可读
        if 主端 is not None:#有可读主端
            线程=threading.Thread(target=自身._读循环,daemon=True)#读线程
            线程.start()#启动
        等退=threading.Thread(target=自身._等退出,daemon=True)#等进程
        等退.start()#启动

    def onData(自身,回调):
        """登记数据回调；返回可 dispose 的拆除器。"""
        with 自身._锁:#改表
            自身._数据监听.append(回调)#追加
        def 拆除():
            """摘掉本回调。"""
            with 自身._锁:#改表
                try:#可能已不在
                    自身._数据监听.remove(回调)#摘掉
                except ValueError:#已不在
                    pass#忽略
        return 拆除器(拆除)#拆除柄

    def onExit(自身,回调):
        """登记退出回调；参数为 {exitCode, signal}。"""
        with 自身._锁:#改表
            自身._退出监听.append(回调)#追加
            if 自身._已退出:#已退出则补发
                码=自身._进程.poll()#退出码
                回调({'exitCode':码 if 码 is not None else 0,'signal':0})#补发
        def 拆除():
            """摘掉本回调。"""
            with 自身._锁:#改表
                try:#可能已不在
                    自身._退出监听.remove(回调)#摘掉
                except ValueError:#已不在
                    pass#忽略
        return 拆除器(拆除)#拆除柄

    def write(自身,数据):
        """写入子进程；文本按 utf-8。"""
        if 自身._主端 is None:#无主端
            raise OSError('node_pty: no master fd')#拒绝
        if isinstance(数据,str):#文本
            数据=数据.encode('utf-8')#转字节
        elif not isinstance(数据,bytes):#其它缓冲
            数据=bytes(数据)#收成 bytes
        os.write(自身._主端,数据)#写出

    def resize(自身,列,行):
        """改窗尺寸；无主端或非 POSIX 则空操作。"""
        if 自身._主端 is None or 自身._平台=='win32':#不可设
            return#空操作
        try:#TIOCSWINSZ
            import fcntl,termios#ioctl
            包=struct.pack('HHHH',int(行 or 24),int(列 or 80),0,0)#行列
            fcntl.ioctl(自身._主端,termios.TIOCSWINSZ,包)#设尺寸
        except (OSError,ImportError,AttributeError):#平台不支持
            return#空操作

    def kill(自身,信号名=None):
        """向会话发信号；缺省 SIGKILL。Windows 上忽略信号名直接终止。"""
        if 自身._平台=='win32':#无 POSIX 信号
            自身._进程.terminate()#终止
            return#结束
        编号=signal.SIGKILL#默认强杀
        if isinstance(信号名,str) and hasattr(signal,信号名):#具名信号
            编号=getattr(signal,信号名)#取编号
        try:#可能已死
            os.kill(自身.pid,编号)#发信号
        except OSError:#已死
            pass#忽略

    def pause(自身):
        """暂停读循环派发。"""
        自身._已暂停=True#记下
        自身._暂停门.clear()#关门

    def resume(自身):
        """恢复读循环派发。"""
        自身._已暂停=False#清
        自身._暂停门.set()#开门

    def _读循环(自身):
        """从主端读并派发 onData。"""
        while not 自身._已退出:#未退出
            自身._暂停门.wait()#可能被 pause
            try:#读一块
                块=os.read(自身._主端,4096)#读
            except OSError:#主端关
                break#结束
            if not 块:#EOF
                break#结束
            文本=块.decode('utf-8','surrogateescape')#对齐 node 字符串面
            with 自身._锁:#派发
                列表=list(自身._数据监听)#副本
            for 回调 in 列表:#逐个
                回调(文本)#派发

    def _等退出(自身):
        """等进程结束并派发 onExit。"""
        自身._进程.wait()#阻塞到退出
        码=自身._进程.returncode#退出码
        信号编号=0#非信号
        退出码=码 if 码 is not None else 0#缺省 0
        if 自身._平台!='win32' and 码 is not None and 码<0:#POSIX 死于信号
            信号编号=-码#信号编号
            退出码=0#死于信号时 exitCode 语义由句柄再解
        with 自身._锁:#改状态
            自身._已退出=True#记下
            列表=list(自身._退出监听)#副本
        for 回调 in 列表:#逐个
            回调({'exitCode':退出码,'signal':信号编号})#派发
        if 自身._主端 is not None:#有主端
            try:#关主端
                os.close(自身._主端)#关
            except OSError:#已关
                pass#忽略
        自身._暂停门.set()#解开可能卡住的读

def spawn(文件,参数,选项=None):
    """对齐 node-pty spawn(file, args, options) → IPty。"""
    选项=选项 or {}#缺省空
    参数表=list(参数) if 参数 is not None else []#参数
    环境=选项.get('env')#环境
    工作目录=选项.get('cwd')#工作目录
    行=选项.get('rows')#行
    列=选项.get('cols')#列
    平台='win32' if os.name=='nt' else os.name#平台标签
    if 平台=='win32':#尚无 ConPTY 绑定
        raise OSError('node_pty: Windows ConPTY backend is not wired in this Python build')#响亮失败
    import pty#POSIX 伪终端
    主端,从端=pty.openpty()#分配
    if 行 is not None or 列 is not None:#要设尺寸
        try:#TIOCSWINSZ
            import fcntl,termios#ioctl
            包=struct.pack('HHHH',int(行 or 24),int(列 or 80),0,0)#行列
            fcntl.ioctl(主端,termios.TIOCSWINSZ,包)#设
        except (OSError,ImportError,AttributeError):#忽略
            pass#继续
    try:#拉起
        进程=拉起进程(
            [文件]+参数表,#argv
            stdin=从端,stdout=从端,stderr=从端,#三路绑从端
            cwd=工作目录,env=环境,#工作目录与环境
            start_new_session=True,close_fds=True,#新会话
        )#结束拉起
    except Exception:#失败
        os.close(主端)#关主
        os.close(从端)#关从
        raise#原样
    os.close(从端)#父进程只留主端
    return 伪终端会话(进程,主端,平台)#会话
