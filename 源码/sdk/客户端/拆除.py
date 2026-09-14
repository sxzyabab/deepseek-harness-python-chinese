import sys,subprocess#平台判定与超时等待

__all__=['拆除运行时进程','SDK拆除错误']#仅中文公开名

class SDK拆除错误(Exception):
    """拆除阶梯失败。"""

def 时限内退出(子进程,毫秒):
    """两种结果都不会在子进程上留下残留监听。"""
    if 子进程.poll() is not None:#已退出
        return True#成功
    try:
        子进程.wait(timeout=毫秒/1000.0)#按秒
        return True#在时限内退出
    except subprocess.TimeoutExpired:
        return False#未退出

def 强制终止于时限(子进程,毫秒):
    """若宽限内没有退出边沿则抛错。"""
    if 子进程.poll() is not None:#已退出
        return#无需杀
    已接受=False#kill 是否被接受
    try:
        子进程.kill()#SIGKILL / TerminateProcess
        已接受=True#已发出
    except ProcessLookupError:
        return#已退出
    except OSError as 错误:
        raise SDK拆除错误('SIGKILL 失败') from 错误#带 cause
    if 时限内退出(子进程,毫秒):#宽限内退出
        return#成功
    处置='已接受' if 已接受 else '已拒绝'#记录是否被接受
    raise SDK拆除错误('运行时进程在 SIGKILL '+处置+' 后 '+str(毫秒)+' 毫秒内仍未退出')#超时

def 拆除运行时进程(子进程,宽限,平台=None):
    """仅在退出后返回。POSIX 先发 SIGTERM 再发 SIGKILL；Windows 直接强制终止。宽限为 dict。"""
    if 平台 is None:#默认当前宿主
        平台=sys.platform#平台
    if 子进程.poll() is not None:#已经不在了
        return#没有可收割的东西
    if 子进程.stdin is not None:#有 stdin
        try:
            子进程.stdin.close()#EOF
        except OSError:
            pass#关闭失败不阻断阶梯
    if 时限内退出(子进程,宽限['disposeEofGraceMs']):#EOF 宽限内退出
        return#结束
    if 平台!='win32':#非 Windows 才发 SIGTERM
        try:
            子进程.terminate()#SIGTERM
        except ProcessLookupError:
            return#结束
        if 时限内退出(子进程,宽限['disposeGraceMs']):#优雅窗口内退出
            return#结束
    强制终止于时限(子进程,宽限['disposeGraceMs'])#最后一层
