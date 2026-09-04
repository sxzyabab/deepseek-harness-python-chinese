"""Worker 的进程表。浏览器 Worker 无法 fork，因此
`node:child_process` 垫片自建表：每个正在运行的命令一条记录，
`process.kill` 与子进程服务的树形记账都按 pid 寻址。

与两侧消费者分开存放，因为它们从相反方向需要它——
垫片负责登记条目，`process` 全局负责发信号。

对齐上游 `webworker-runtime/src/node/process-table.ts`。公开面仅中文名。
"""
__all__=['登记进程','释放进程','进程存活','信号进程']#仅中文公开名

_表项们={}#pid到表项
_最近pid=1#最近分配的pid；Pid 1 是 Worker 宿主自身

def 登记进程():#预留pid并登记
    """在命令启动前预留一个 pid，以便句柄能同步报告。

    返回:
        新表项，此时尚无 process。
    """
    global _最近pid#递增槽
    _最近pid+=1#递增pid
    表项={'pid':_最近pid,'signal':None,'process':None}#新建表项
    _表项们[表项['pid']]=表项#写入表
    return 表项#交回表项

def 释放进程(pid):#释放表项
    """命令结束后丢弃对应表项。"""
    _表项们.pop(pid,None)#按pid删除

def 进程存活(pid):#探测是否仍在表中
    """该 pid 对应的命令是否仍在运行。

    负值寻址进程组，此处恰好只含组内领头的那一个进程。
    """
    return abs(pid) in _表项们#负pid按绝对值查

def 信号进程(pid,信号):#投递信号
    """向一条正在运行的命令投递信号。

    `SIGKILL` 无论命令在做什么都会停下；其它信号则要求它
    在下一个命令边界停止。
    """
    表项=_表项们.get(abs(pid))#按绝对值取表项
    if 表项 is None: return False#无此进程
    if 表项['signal'] is None: 表项['signal']=信号#首次信号记下
    进程=表项.get('process')#运行中命令
    if 进程 is not None:#有进程句柄
        if 信号=='SIGKILL': 进程.destroy()#强杀
        else: 进程.interrupt()#软中断
    return True#已投递
