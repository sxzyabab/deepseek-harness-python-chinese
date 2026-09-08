"""主机路由与浏览器包共用的路径常量与线载荷形态。

对齐上游 `open-in-app/src/shared.ts`。路由字面量与 JSON 键保持英文。
"""

__all__=[#仅中文公开名
    '应用列表路由','图标前缀','打开路由',
]#公开面结束

应用列表路由='/open-in-app/apps'#GET：已探测到的应用标识列表
图标前缀='/open-in-app/icon'#GET 前缀：按应用标识取 PNG/SVG 图标
打开路由='/open-in-app/open'#POST：在指定应用中打开工作区目录
