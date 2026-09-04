"""Worker 进程启动器所用的虚拟可执行项注册表。

对齐上游 `webworker-runtime/src/shell/process/virtual-executables.ts`。公开面仅中文名。
"""
from ...module_system.posix路径 import 基名#路径基名
from .地锁 import 地锁可执行#landlock可执行项

__all__=['解析虚拟可执行']#仅中文公开名

# 结果形态（对齐上游联合）：
# 退出：{'kind':'exit','exitCode':int,'stdout':str,'stderr':str}
# 委托：{'kind':'delegate','argv':list,'filesystem':dict,'missingExecutable':退出}
# 同步异步标记：{'kind':'asynchronous'}

可执行表={地锁可执行['name']:地锁可执行}#注册表

def 解析虚拟可执行(路径):#按路径解析
    """按逻辑名解析 Worker 平台可执行项。"""
    return 可执行表.get(基名(路径))#按基名查表
