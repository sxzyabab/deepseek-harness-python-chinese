"""command 命名空间词典（popupSelect 外壳文案）。

对齐上游 `ui-commands/src/client/locales.ts`。公开面仅中文名。
"""

__all__=['命名空间','中文','英文']#仅中文公开名

命名空间='command'#词表命名空间

中文={#简体中文
    'search.placeholder':'搜索…',#占位
    'search.aria':'筛选选项',#搜索无障碍
    'status.loading':'正在加载选项…',#加载
    'status.applying':'正在应用…',#应用
    'status.empty':'无选项',#空
    'overlay.aria':'/{command} 选项',#浮层
    'listbox.aria':'/{command} 匹配项',#列表
    'retry':'重试',#重试
}#中文结束

英文={#英文
    'search.placeholder':'Search…',#占位
    'search.aria':'Filter options',#搜索
    'status.loading':'Loading options…',#加载
    'status.applying':'Applying…',#应用
    'status.empty':'No options',#空
    'overlay.aria':'/{command} options',#浮层
    'listbox.aria':'/{command} matches',#列表
    'retry':'Retry',#重试
}#英文结束
