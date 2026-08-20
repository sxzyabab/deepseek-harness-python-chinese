"""仅用于spawn的工人入口，委托跑工人主逻辑。可执行逻辑留在引导模块以便进程内覆盖率。"""
from .引导 import 跑工人主逻辑#工人侧主执行逻辑

def 工人入口(端口,启动数据,流们=None):#工人线程入口
    """工人始终有父端口；大声守卫而不是在脱离宿主时继续跑。同进程线程工人勿传入宿主sys.stdout/stderr（会污染宿主）；独立工人进程/线程可传{'stdout':…,'stderr':…}。"""
    if 端口 is None:#非工人线程加载则失败
        raise RuntimeError('dsh-code-runtime-worker-thread: worker entry loaded outside a worker thread')#守卫
    跑工人主逻辑(端口,启动数据,流们)#启动工人主逻辑（流们缺省则不劫持写出）

default=工人入口#默认导出
