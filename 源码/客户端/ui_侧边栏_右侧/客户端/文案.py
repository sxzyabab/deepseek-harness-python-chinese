
__all__=['中文','英文','右侧侧栏文案键']#仅中文公开名

中文={#简体中文词条（键集合的权威源）
    'chrome.expand':'打开侧边栏',#展开
    'chrome.expandAria':'打开右侧边栏',#展开无障碍名
    'chrome.collapse':'收起侧边栏',#收起
    'chrome.collapseAria':'收起右侧边栏',#收起无障碍名
    'chrome.toFullscreen':'全屏',#进全屏
    'chrome.exitFullscreen':'退出全屏',#退全屏
    'dock.emptyPane':'空面板',#空窗
    'dock.splitPane':'分栏',#分栏
    'dock.splitPaneDisabled':'已达两格上限',#已满
    'dock.splitPaneNarrow':'栏宽不足，拖宽侧边栏后再分栏',#过窄
    'dock.closeTab':'关闭',#关签
    'dock.addTab':'新标签页',#加签
    'dock.dockFloat':'收回到侧边栏',#收回
    'dock.closeFloat':'关闭',#关浮
    'dock.drop.center':'移到这里',#投放中心
    'dock.drop.left':'左分栏',#投放左
    'dock.drop.right':'右分栏',#投放右
    'dock.drop.top':'上分栏',#投放上
    'dock.drop.bottom':'下分栏',#投放下
    'tab.guide.title':'开始',#向导标题
    'tab.unavailable':'这类内容还没有可用的查看方式。',#无查看器
}#中文词典结束

英文={#英文词条，对照中文权威源核验键齐全
    'chrome.expand':'Open sidebar',#展开
    'chrome.expandAria':'Open right sidebar',#展开无障碍名
    'chrome.collapse':'Collapse sidebar',#收起
    'chrome.collapseAria':'Collapse right sidebar',#收起无障碍名
    'chrome.toFullscreen':'Fullscreen',#进全屏
    'chrome.exitFullscreen':'Exit fullscreen',#退全屏
    'dock.emptyPane':'Empty pane',#空窗
    'dock.splitPane':'Split',#分栏
    'dock.splitPaneDisabled':'Two panes is the limit',#已满
    'dock.splitPaneNarrow':'Not enough width to split, widen the sidebar',#过窄
    'dock.closeTab':'Close',#关签
    'dock.addTab':'New tab',#加签
    'dock.dockFloat':'Send back to the sidebar',#收回
    'dock.closeFloat':'Close',#关浮
    'dock.drop.center':'Move here',#投放中心
    'dock.drop.left':'Add left split',#投放左
    'dock.drop.right':'Add right split',#投放右
    'dock.drop.top':'Add top split',#投放上
    'dock.drop.bottom':'Add bottom split',#投放下
    'tab.guide.title':'Start',#向导标题
    'tab.unavailable':'Nothing here can view this kind of content yet.',#无查看器
}#英文词典结束

右侧侧栏文案键=tuple(中文.keys())#由中文词典键推导的键域
