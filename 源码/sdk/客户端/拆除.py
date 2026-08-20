"""运行时子进程的私有拆除阶梯：先标准输入 EOF，再 SIGTERM，再 SIGKILL。

对齐上游 `sdk/client/src/dispose.ts`。公开面仅中文名。SDK 客户端运行在任何 harness 上下文之外，因此不能挂靠 subprocess 服务。
"""
import sys,time#平台判定与宽限等待
import subprocess#超时等待

__all__=['拆除运行时进程']#仅中文公开名

def 时限内退出(子进程,毫秒):#在时限内等待子进程退出
    """两种结果都不会在子进程上留下残留监听。"""
    if 子进程.poll() is not None:#已退出
        return True#成功
    try:#有界等待
        子进程.wait(timeout=毫秒/1000.0)#按秒
        return True#在时限内退出
    except subprocess.TimeoutExpired:#超时
        return False#未退出

def 强制终止于时限(子进程,毫秒):#在时限内 SIGKILL 并等待退出
    """若宽限内没有退出边沿则抛错。"""
    if 子进程.poll() is not None:#已退出
        return#无需杀
    已接受=False#kill 是否被接受
    try:#尝试强制终止
        子进程.kill()#SIGKILL / TerminateProcess
        已接受=True#已发出
    except ProcessLookupError:#已不在
        return#已退出
    except BaseException as 错误:#kill 本身抛错
        raise Exception('SIGKILL failed') from 错误#带 cause
    if 时限内退出(子进程,毫秒):#宽限内退出
        return#成功
    处置='accepted' if 已接受 else 'refused'#记录是否被接受
    raise Exception('runtime process did not exit within '+str(毫秒)+'ms after SIGKILL was '+处置)#超时

def 拆除运行时进程(子进程,宽限,平台=None):#将运行时拆除到静默
    """仅在退出后返回。POSIX 先发 SIGTERM 再发 SIGKILL；Windows 直接强制终止。"""
    if 平台 is None:#默认当前宿主
        平台=sys.platform#平台
    if 子进程.poll() is not None:#已经不在了
        return#没有可收割的东西
    # 1. 关闭标准输入，允许协作拆除与持久状态刷新。
    if 子进程.stdin is not None:#有 stdin
        try:#关闭
            子进程.stdin.close()#EOF
        except BaseException:#关闭失败不阻断阶梯
            pass#继续
    if 时限内退出(子进程,宽限['disposeEofGraceMs']):#EOF 宽限内退出
        return#结束
    # 2. POSIX 获得可捕获的优雅信号；Windows 信号一律强制终止。
    if 平台!='win32':#非 Windows 才发 SIGTERM
        try:#优雅终止
            子进程.terminate()#SIGTERM
        except ProcessLookupError:#已退出
            return#结束
        if 时限内退出(子进程,宽限['disposeGraceMs']):#优雅窗口内退出
            return#结束
    # 3. 强制杀死并等待有界退出边沿。
    强制终止于时限(子进程,宽限['disposeGraceMs'])#最后一层
