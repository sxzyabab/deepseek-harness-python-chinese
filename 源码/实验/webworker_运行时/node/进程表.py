__all__=['登记进程','释放进程','进程存活','信号进程']

_表项表={}
_最近pid=1#最近分配的pid；Pid 1 是 Worker 宿主自身

def 登记进程():
    """在命令启动前预留一个 pid，以便句柄能同步报告。

    返回:
        新表项，此时尚无 process。
    """
    global _最近pid
    _最近pid+=1
    表项={'pid':_最近pid,'signal':None,'process':None}
    _表项表[表项['pid']]=表项
    return 表项

def 释放进程(pid):
    """命令结束后丢弃对应表项。"""
    _表项表.pop(pid,None)

def 进程存活(pid):
    """该 pid 对应的命令是否仍在运行。

    负值寻址进程组，此处恰好只含组内领头的那一个进程。
    """
    return abs(pid) in _表项表

def 信号进程(pid,信号):
    """向一条正在运行的命令投递信号。

    `SIGKILL` 无论命令在做什么都会停下；其它信号则要求它
    在下一个命令边界停止。
    """
    键=abs(pid)
    if 键 not in _表项表:
        return False
    表项=_表项表[键]
    if 表项['signal'] is None:
        表项['signal']=信号
    进程=表项['process'] if 'process' in 表项 else None
    if 进程 is not None:
        if 信号=='SIGKILL': 进程.destroy()
        else: 进程.interrupt()
    return True
