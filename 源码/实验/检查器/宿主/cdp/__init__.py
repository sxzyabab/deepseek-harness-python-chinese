"""Host realm 的源侧 CDP 能力声明。

对齐上游 `host/cdp/index.ts`。公开面仅中文名。
"""
from .控制台 import 控制台桥能力#Console能力
from .调试器 import 调试器桥能力#Debugger能力
from .堆分析器 import 堆分析器桥能力#HeapProfiler能力
from .分析器 import 分析器桥能力#Profiler能力
from .运行时 import 运行时桥能力#Runtime能力
from .源 import 源桥能力#Sources能力

__all__=['桥能力']#仅中文公开名

宿主桥能力=[#Host桥能力
    项 for 项 in (#过滤空
        运行时桥能力(''),#Runtime
        控制台桥能力(),#Console
        源桥能力(False),#Sources
        调试器桥能力(),#Debugger
        分析器桥能力(),#Profiler
        堆分析器桥能力(),#HeapProfiler
    ) if 项 is not None#过滤空
]#常量集

def 桥能力(_来源, _有源):#桥能力
    """收集 Host source-bridge 能力。"""
    return tuple(宿主桥能力)#返回常量集
