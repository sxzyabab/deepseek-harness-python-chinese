"""套件对外约定：状态进、意图出。

对齐上游 `ui-dockkit/src/contract/adapter.ts`。公开面仅中文名。
宿主特有的一切经此进入——已本地化文案、标签正文、每一次手势净结果。
套件本身不持副本、不持图标集、不解释标签的 `kind`。

文案字段名与意图方法名是线协议面，原样英文；嵌入方按这些键/名供给。
"""

__all__=[#仅中文公开名
    '停靠文案键表',
    '停靠意图名表',
]#公开面结束

# 文案字段名是线协议面：嵌入方按这些键供给已本地化字符串
停靠文案键表=(#停靠文案字段
    'emptyPane',#空窗格正文
    'splitPane',#可分割时的分割控件
    'splitPaneDisabled',#窗格预算耗尽
    'splitPaneNarrow',#宽度不够两半
    'closeTab',#关标签
    'addTab',#加标签
    'dockFloat',#收回浮动
    'closeFloat',#关浮动
)#文案键结束

# 意图方法名是线协议面：嵌入方存储或控制器同名实现
停靠意图名表=(#停靠意图方法
    'focusTab',#聚焦标签
    'focusPane',#聚焦窗格
    'splitPane',#分割窗格
    'addTab',#加标签
    'closeTab',#关标签
    'duplicateTab',#复制标签
    'floatTab',#浮动标签
    'unfloatPane',#收回浮动
    'placeTab',#安放标签
    'dropTab',#投放标签
    'moveFloat',#平移浮动
    'resizeFloat',#缩放浮动
    'resizeSplit',#缩放分割
)#意图名结束
