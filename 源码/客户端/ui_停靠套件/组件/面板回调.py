"""组件间共享的窗格回调约定。

对齐上游 `ui-dockkit/src/components/render.ts`。公开面仅中文名。
对外约定在适配模块；本模块装配窗格子树需要的已结算回调与预览。
"""

__all__=[#仅中文公开名
    '分割阻断预算',
    '分割阻断宽度',
    '建面板回调',
]#公开面结束

分割阻断预算='budget'#窗格预算
分割阻断宽度='width'#半格不够宽


def 建面板回调(
    聚焦标签,聚焦窗格,分割窗格,加标签,关标签,
    标签按下,分割条按下,分割阻断,可加标签,
    投放目标,拖中标签标识,文案,渲染标签,
    渲染标签标题=None,渲染标签菜单项=None,
    饰条窗格标识=None,饰条=None,
    阻断时隐藏分割=False,可否关闭标签=None,水平投放=False,
):
    """装配窗格回调 dict（键与标签面板/窗格树约定一致，含上游形 on* 键）。"""
    return {#回调
        'onFocusTab':聚焦标签,
        'onFocusPane':聚焦窗格,
        'onSplitPane':分割窗格,
        'onAddTab':加标签,
        'onCloseTab':关标签,
        'onTabPressed':标签按下,
        'onDividerPressed':分割条按下,
        'splitBlock':分割阻断,
        'hideSplitWhenBlocked':阻断时隐藏分割,
        'canAddTab':可加标签,
        'canCloseTab':可否关闭标签,
        'dropTarget':投放目标,
        'horizontalDrops':水平投放,
        'draggingTabId':拖中标签标识,
        'labels':文案,
        'renderTab':渲染标签,
        'renderTabTitle':渲染标签标题,
        'renderTabMenuItems':渲染标签菜单项,
        'chromePaneId':饰条窗格标识,
        'chrome':饰条,
    }#回调结束
