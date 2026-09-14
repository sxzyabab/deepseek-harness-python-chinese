import threading#并发上限
from .代次 import 校验jsonl当代代#当代校验

最大并发校验数=2#进程级并发上限

class _校验调度器:#校验调度器
    """限制同时进行的整代校验数。"""
    def __init__(自身,上限=最大并发校验数):#构造
        """记下上限。"""
        自身.上限=上限#上限
        自身._锁=threading.Semaphore(上限)#信号量

    def 运行(自身,操作,信号=None):#受许可保护运行
        """取得许可后运行操作。"""
        if 信号 is not None and (getattr(信号,'aborted',False) or getattr(信号,'已中止',False)):#已中止
            raise InterruptedError('迁移校验已中止')#中止
        自身._锁.acquire()#取得
        try:#执行
            if 信号 is not None and (getattr(信号,'aborted',False) or getattr(信号,'已中止',False)):#再检查
                raise InterruptedError('迁移校验已中止')#中止
            return 操作()#运行
        finally:#释放
            自身._锁.release()#归还

_调度器=_校验调度器()#进程级调度器

def 进程内校验当代代(路径,压缩,期望标识,期望事件数,期望前缀=None,信号=None):#进程内校验
    """在本进程内校验一份当代代（Python 端口不启 worker）。"""
    def 执行校验():#操作
        """调用代次校验。"""
        return 校验jsonl当代代(路径,压缩,期望标识,期望事件数,期望前缀)#校验
    return _调度器.运行(执行校验,信号)#经调度

__all__=['进程内校验当代代','最大并发校验数']#公开面
