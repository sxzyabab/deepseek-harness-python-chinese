"""仅用于spawn的工作线程入口，委托执行工作线程主逻辑。可执行逻辑留在引导模块以便进程内覆盖率。"""
from .引导 import 执行工作线程主逻辑#工作线程侧主执行逻辑

def 工作线程入口(端口,启动载荷,流表=None):#工作线程入口
    """工作线程始终有父端口；大声守卫而不是在脱离宿主时继续跑。同进程线程勿传入宿主sys.stdout/stderr（会污染宿主）；独立工作线程进程/线程可传{'stdout':…,'stderr':…}。"""
    if 端口 is None:#非工作线程加载则失败
        raise RuntimeError('dsh-code-runtime-worker-thread: worker entry loaded outside a worker thread')#守卫
    执行工作线程主逻辑(端口,启动载荷,流表)#启动工作线程主逻辑（流表缺省则不劫持写出）

default=工作线程入口#默认导出
