"""与界域无关的 Runtime、Console、Source 与 Debugger 协议类型。

对齐上游 `shared/cdp/index.ts`。公开面仅中文名。
"""
from .能力 import *#导出能力
from .控制台 import *#导出Console
from .调试器 import *#导出Debugger
from .错误 import *#导出错误类型
from .标识 import *#导出标识
from .操作 import *#导出操作
from .属性 import *#导出属性
from .远程对象 import *#导出远程对象
from .源 import *#导出源元数据
from .领域 import *#导出领域后端

__all__=[]#由子模块公开面聚合
