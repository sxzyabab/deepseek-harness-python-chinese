"""布局模型与操作词汇。纯约定：无运行时副作用、无宿主概念。

对齐上游 `ui-dockkit/src/contract/types.ts`。公开面仅中文名。
模型是归一化的递归分割树。`nodes` 按标识存放分割与窗格；`rootId` 是停靠根；
`floats` 自底到顶列出浮动窗格。浮动面板不是第二概念——它是 `host` 为 `'float'`、
容量一标签、不画标签条的窗格。

标识在 Python 侧为字符串；前缀约定由铸造器保证窗格、分割、标签互不冒充。
跨包与本包状态一律 dict；判别字面量是线协议，原样英文。

布局状态（LayoutState）键：nodes, tabs, rootId, floats, activePaneId, expanded, mode。
分割节点：kind='split', id, axis, children, sizes。
窗格节点：kind='pane', id, host, tabs, activeTabId, rect。
标签记录：id, kind, contentId, title。
浮窗矩形：x, y, width, height。
操作（LayoutOp）以 type 判别：split/merge/openTab/closeTab/moveTab/reorderTab/
focusTab/focusPane/resize/float/unfloat/moveFloat/resizeFloat/setExpanded/setMode/
insertPane/insertTab/restoreFocus；施加结果为 {state, inverse}。
"""

__all__=[#仅中文公开名
    '停靠错误',
    '分割轴行',
    '分割轴列',
    '分割方向前',
    '分割方向后',
    '停靠区位表',
    '停靠模式推挤',
    '停靠模式全屏',
    '窗格宿主停靠',
    '窗格宿主浮动',
    '节点种分割',
    '节点种窗格',
    '焦点操作种表',
]#公开面结束

分割轴行='row'#行分割
分割轴列='column'#列分割
分割方向前='before'#参考窗格前
分割方向后='after'#参考窗格后
停靠区位表=('center','top','right','bottom','left')#五区位
停靠模式推挤='push'#挤占邻域
停靠模式全屏='fullscreen'#盖住视口
窗格宿主停靠='dock'#停靠树内
窗格宿主浮动='float'#视口浮层
节点种分割='split'#分割节点
节点种窗格='pane'#窗格节点
焦点操作种表=frozenset({'focusTab','focusPane','restoreFocus'})#仅挪焦点的操作种


class 停靠错误(Exception):
    """本包停靠布局失败。"""

    def __init__(自身,消息):
        """记下英文消息。"""
        super().__init__(消息)#消息原样英文
