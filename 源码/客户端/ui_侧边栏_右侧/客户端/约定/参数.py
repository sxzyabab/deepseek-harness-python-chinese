"""导航参数：按打开对象分型的声明合并面。

对齐上游 `ui-sidebar-right/src/client/contract/params.ts`。公开面仅中文名。
Python 无声明合并；资源类型参数与页面种类参数以可选 dict 承载，运行时不校验。
正文按 `navigation.address` 的方案与类型收窄 `params`。
"""

__all__=[#仅中文公开名
    '右侧侧栏资源参数','右侧侧栏标签参数','右侧侧栏导航参数',
]#公开面结束

# 运行时形态：None 或 JSON 形 dict；具体键由打开方与正文约定
右侧侧栏资源参数=object#类型占位：资源打开 params
右侧侧栏标签参数=object#类型占位：页面打开 params
右侧侧栏导航参数=object#类型占位：navigation.params
