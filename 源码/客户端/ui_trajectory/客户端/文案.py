"""`trajectory` 命名空间词典（视图页签标签与工具栏文案）。

对齐上游 `ui-trajectory/src/client/locales.ts`。公开面仅中文名。
"""

__all__=['命名空间','轨迹文案键','中文','英文']#仅中文公开名

命名空间='trajectory'#词典命名空间名

轨迹文案键=(#轨迹词典键集合（两种语言的权威源）
    'view.trajectory',#视图页签标签
    'toolbar.aria',#工具栏无障碍名
    'toolbar.duration',#时长刻度
    'toolbar.useActualDuration',#按实际时长
    'toolbar.useEqualWidth',#等宽操作
    'toolbar.actualTime',#实际时间
    'toolbar.turns',#轮次
    'toolbar.expandTurns',#展开轮次
    'toolbar.collapseTurns',#收起轮次
    'toolbar.calls',#调用
    'toolbar.expandCalls',#展开调用
    'toolbar.collapseCalls',#收起调用
    'toolbar.search',#搜索轨迹
    'toolbar.searchPlaceholder',#搜索占位
)#键集合结束

中文={#简体中文词条
    'view.trajectory':'轨迹',#视图页签标签
    'toolbar.aria':'轨迹工具栏',#工具栏无障碍名
    'toolbar.duration':'Duration',#时长刻度
    'toolbar.useActualDuration':'Use actual duration',#按实际时长
    'toolbar.useEqualWidth':'Use equal-width operations',#等宽操作
    'toolbar.actualTime':'实际时间',#实际时间
    'toolbar.turns':'Turns',#轮次
    'toolbar.expandTurns':'Expand turns',#展开轮次
    'toolbar.collapseTurns':'Collapse turns',#收起轮次
    'toolbar.calls':'Calls',#调用
    'toolbar.expandCalls':'Expand calls',#展开调用
    'toolbar.collapseCalls':'Collapse calls',#收起调用
    'toolbar.search':'搜索轨迹',#搜索轨迹
    'toolbar.searchPlaceholder':'搜索',#搜索占位
}#中文结束

英文={#英文词条
    'view.trajectory':'Trajectory',#视图页签标签
    'toolbar.aria':'Trajectory toolbar',#工具栏无障碍名
    'toolbar.duration':'Duration',#时长刻度
    'toolbar.useActualDuration':'Use actual duration',#按实际时长
    'toolbar.useEqualWidth':'Use equal-width operations',#等宽操作
    'toolbar.actualTime':'Actual time',#实际时间
    'toolbar.turns':'Turns',#轮次
    'toolbar.expandTurns':'Expand turns',#展开轮次
    'toolbar.collapseTurns':'Collapse turns',#收起轮次
    'toolbar.calls':'Calls',#调用
    'toolbar.expandCalls':'Expand calls',#展开调用
    'toolbar.collapseCalls':'Collapse calls',#收起调用
    'toolbar.search':'Search trajectory',#搜索轨迹
    'toolbar.searchPlaceholder':'Search',#搜索占位
}#英文结束
