"""命令表再导出别名（对齐曾用中文名 `索引` 的引用面）。

对齐上游 `webworker-runtime/src/shell/programs/index.ts`。公开面仅中文名。
实现见同目录 `__init__.py`；本文件仅提供历史别名，避免与包根循环导入。
"""
from .内建 import 内建程序 as 内建程序们#别名
from .文件 import 文件程序 as 文件程序们#别名

__all__=['内建程序们','文件程序们']#仅中文公开名
# 标准程序 / 标准程序表 / which程序：from ..programs import 标准程序
