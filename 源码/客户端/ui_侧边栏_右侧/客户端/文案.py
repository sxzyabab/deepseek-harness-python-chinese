"""`sidebarRight` 命名空间词典，以及键集合权威源。

对齐上游 `ui-sidebar-right/src/client/locales.ts`。公开面仅中文名；词典键与英文字面量保持上游。
本栏用户可读文案均在此，含交给停靠套件的词——套件自身不持文案。
"""

__all__=['中文','英文','右侧侧栏文案键']#仅中文公开名

中文={#简体中文词条（键集合的权威源）
    'chrome.expand':'展开侧栏',#展开
    'chrome.collapse':'收起侧栏',#收起
    'chrome.toFullscreen':'全屏显示侧栏',#进全屏
    'chrome.exitFullscreen':'退出侧栏全屏',#退全屏
    'dock.emptyPane':'空面板',#空窗
    'dock.splitPane':'向右分栏',#分栏
    'dock.splitPaneDisabled':'已达两格上限',#已满
    'dock.splitPaneNarrow':'栏宽不足，拖宽侧栏后再分栏',#过窄
    'dock.closeTab':'关闭',#关签
    'dock.addTab':'新标签页',#加签
    'dock.dockFloat':'收回到侧栏',#收回
    'dock.closeFloat':'关闭',#关浮
    'tab.guide.title':'开始',#向导标题
    'tab.unavailable':'这类内容还没有可用的查看方式。',#无查看器
    'guide.lead':'侧栏用来放你想一直看着的东西。',#向导引语
    'guide.body':'会话里的文件和产物会开在这一栏，也可以从下面的入口打开。',#向导正文
}#中文词典结束

英文={#英文词条，对照中文权威源核验键齐全
    'chrome.expand':'Open the sidebar',#展开
    'chrome.collapse':'Close the sidebar',#收起
    'chrome.toFullscreen':'Show the sidebar fullscreen',#进全屏
    'chrome.exitFullscreen':'Exit sidebar fullscreen',#退全屏
    'dock.emptyPane':'Empty pane',#空窗
    'dock.splitPane':'Split to the right',#分栏
    'dock.splitPaneDisabled':'Two panes is the limit',#已满
    'dock.splitPaneNarrow':'Not enough width to split; widen the sidebar',#过窄
    'dock.closeTab':'Close',#关签
    'dock.addTab':'New tab',#加签
    'dock.dockFloat':'Send back to the sidebar',#收回
    'dock.closeFloat':'Close',#关浮
    'tab.guide.title':'Start',#向导标题
    'tab.unavailable':'Nothing here can view this kind of content yet.',#无查看器
    'guide.lead':'The sidebar holds what you want to keep looking at.',#向导引语
    'guide.body':'Files and artifacts from the conversation open in this column; the entries below open more.',#向导正文
}#英文词典结束

右侧侧栏文案键=tuple(中文.keys())#由中文词典键推导的键域
