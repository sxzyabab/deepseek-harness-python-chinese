"""描述浏览器 Client realm 的源侧 CDP 能力声明。

对齐上游 `client/cdp/index.ts`。公开面仅中文名。
"""
from .控制台 import 控制台桥能力#Console
from .调试器 import 调试器桥能力#Debugger
from .堆分析器 import 堆分析器桥能力#HeapProfiler
from .分析器 import 分析器桥能力#Profiler
from .运行时 import 运行时桥能力#Runtime
from .源 import 源桥能力#Sources

__all__=['桥能力']#仅中文公开名

def 桥能力(来源,有源):#桥能力
    """描述需要 Worker→页面桥消息的 Client 操作。"""
    return tuple(项 for 项 in (#能力列表
        运行时桥能力(来源),#Runtime
        控制台桥能力(),#Console
        源桥能力(有源),#Sources
        调试器桥能力(),#Debugger
        分析器桥能力(),#Profiler
        堆分析器桥能力(),#HeapProfiler
    ) if 项 is not None)#过滤空
