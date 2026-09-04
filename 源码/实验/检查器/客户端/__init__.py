"""实验性 Inspector Cordis 插件的浏览器 Client 入口。

对齐上游 `client/index.ts`。公开面仅中文名。
"""
from .插件 import 应用,名称,注入,apply#Client插件

__all__=['应用','名称','注入']#仅中文公开名
