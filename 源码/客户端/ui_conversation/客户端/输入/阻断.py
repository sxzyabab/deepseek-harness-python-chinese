"""Composer 阻断：其它插件让某会话输入栏失效的唯一途径。

对齐上游 `ui-conversation/src/client/input/blocks.ts`。
实现落在包根 `阻断.py`；本模块再导出，供输入机子包统一入口。
"""
from ..阻断 import 快照仓库,阻断登记表#实现

__all__=['快照仓库','阻断登记表']#仅中文公开名
