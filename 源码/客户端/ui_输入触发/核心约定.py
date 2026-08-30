"""冻结的纯核心约定：触发探测与菜单归约，零 React / DOM / cordis。仅类型形。

对齐上游 `ui-input-trigger/src/core/contract.ts`。公开面仅中文名。
实现住在探测.py / 菜单归约.py；服务壳把它们接到 ctx。
"""

__all__=[#仅中文公开名
    '触发命中','菜单状态','菜单事件','检测触发形','菜单归约形','精确匹配形',
    '菜单关闭态',
]#公开面结束

#触发命中：光标下已探测到的触发词
#字段 trigger / query / position / span
触发命中=dict#触发命中形

#菜单状态：每个来源一组；空的就绪组会自动关闭菜单
#字段 open / hit / generation / groups[{source,status,items}] / highlight
菜单状态=dict#菜单状态形

#菜单事件：hit / source-settled / source-failed / move / close
菜单事件=dict#菜单归约事件形

#检测触发形：(draft,caret,guard) -> 触发命中|None
检测触发形=object#探测函数形

#菜单归约形：(state,ev) -> state；事件过期或无操作时返回同一引用
菜单归约形=object#纯菜单归约器形

#精确匹配形：(groups,source,name) -> 候选|None
精确匹配形=object#按精确名查找形

菜单关闭态={#菜单关闭初值
    'open':False,#关闭
    'hit':None,#无命中
    'generation':0,#代次
    'groups':[],#无组
    'highlight':None,#无高亮
}#关闭态结束
