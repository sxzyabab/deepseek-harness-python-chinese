'停靠窗和浮动窗现在属于哪一页。读的时候才从页面把身份取回来'

__all__=['从元素取右侧侧栏目标','可见侧栏窗格','观察侧栏焦点']


def _数据集(元素,名):
    'dataset 上的驼峰名。没有就看同名属性'
    数据=getattr(元素,'dataset',None)
    if 数据 is not None:
        值=getattr(数据,名,None)
        if 值 is not None:
            return 值
    属性名=''
    for 字 in 名:
        if 字.isupper():
            属性名+='-'+字.lower()
        else:
            属性名+=字
    return 元素.getAttribute('data-'+属性名)


def 从元素取右侧侧栏目标(元素,会话标识,布局,出现次):
    '从元素往上找会话、窗格和签。陈旧、藏起或外面的元素没有目标'
    if 元素 is None or not 元素.isConnected:
        return None
    拥有=元素.closest('[data-sidebar-right-session]')
    if 拥有 is None or _数据集(拥有,'sidebarRightSession')!=会话标识:
        return None
    容器=元素.closest('[data-dockkit-pane], [data-dockkit-float]')
    if 容器 is None:
        return None
    窗格标识=_数据集(容器,'dockkitPane')
    if 窗格标识 is None:
        窗格标识=_数据集(容器,'dockkitFloat')
    if 窗格标识 is None or 容器.closest('[hidden], [aria-hidden="true"]') is not None:
        return None
    窗=布局['nodes'].get(窗格标识)
    if 窗 is None or 窗.get('kind')!='pane' or (窗['host']=='dock' and not 布局['expanded']):
        return None
    签元素=元素.closest('[data-dockkit-tab], [data-sidebar-right-tab]')
    标签标识=None
    if 签元素 is not None:
        标签标识=_数据集(签元素,'dockkitTab')
        if 标签标识 is None:
            标签标识=_数据集(签元素,'sidebarRightTab')
    if 标签标识 is None:
        标签标识=窗.get('activeTabId')
    if 标签标识 is not None and (标签标识 not in 窗['tabs'] or 标签标识 not in 布局['tabs']):
        return None
    持有=None if 标签标识 is None else 出现次(标签标识)
    标记=元素.closest('[data-sidebar-right-occurrence]')
    if 标记 is None and 签元素 is not None:
        标记=签元素.querySelector('[data-sidebar-right-occurrence]')
    if 标记 is not None and _数据集(标记,'sidebarRightOccurrence')!=(None if 持有 is None else 持有['id']):
        return None
    修订=None
    if 持有 is not None:
        修订=持有['navigation'].getSnapshot()['revision']
    return {
        'sessionId':会话标识,
        'paneId':窗格标识,
        'host':窗['host'],
        'tabId':标签标识,
        'occurrence':持有,
        'navigationRevision':修订,
    }


def 可见侧栏窗格(文档,会话标识,窗格标识):
    '先要指定的窗，再要活动窗，最后要这个会话还在的第一格'
    节点表=文档.querySelectorAll('[data-dockkit-pane], [data-dockkit-float]')
    窗表=[]
    for 窗 in 节点表:
        拥有=窗.closest('[data-sidebar-right-session]')
        if 拥有 is None or _数据集(拥有,'sidebarRightSession')!=会话标识:
            continue
        if 窗.closest('[hidden], [aria-hidden="true"]') is not None:
            continue
        是浮窗=窗.hasAttribute('data-dockkit-float')
        if not 是浮窗 and not 拥有.hasAttribute('data-sidebar-right-open'):
            continue
        窗表.append(窗)
    for 窗 in 窗表:
        标识=_数据集(窗,'dockkitPane')
        if 标识 is None:
            标识=_数据集(窗,'dockkitFloat')
        if 标识==窗格标识:
            return 窗
    for 窗 in 窗表:
        if 窗.hasAttribute('data-dockkit-pane-active') or 窗.hasAttribute('data-dockkit-float-active'):
            return 窗
    if len(窗表)==0:
        return None
    return 窗表[0]


def 观察侧栏焦点(文档):
    '窗格节点被换掉时，把焦点放回还在的那一格'
    活动=[True]
    已聚焦=[None]
    移除观察=[None]

    def 移除回调():
        '节点拆掉之后，焦点若落在 body 上，就找接替的窗'
        当前=已聚焦[0]
        if 当前 is None or 当前['element'].isConnected:
            return
        先前=当前
        已聚焦[0]=None
        移除观察[0].disconnect()
        if 文档.activeElement is not 文档.body:
            return
        挪走=None
        if 先前['occurrence'] is not None:
            for 标记 in 文档.querySelectorAll('[data-sidebar-right-occurrence]'):
                if _数据集(标记,'sidebarRightOccurrence')==先前['occurrence']:
                    挪走=标记.closest('[data-dockkit-pane], [data-dockkit-float]')
                    break
        窗格标识=先前['paneId']
        if 挪走 is not None:
            读到=_数据集(挪走,'dockkitPane')
            if 读到 is None:
                读到=_数据集(挪走,'dockkitFloat')
            if 读到 is not None:
                窗格标识=读到
        窗=可见侧栏窗格(文档,先前['sessionId'],窗格标识)
        if 窗 is not None:
            窗.focus({'preventScroll':True})

    移除观察[0]=文档.defaultView.MutationObserver(移除回调)

    def 捕获():
        '记下当前焦点所在的窗'
        移除观察[0].disconnect()
        已聚焦[0]=None
        元素=文档.activeElement
        if 元素 is None:
            return
        窗=元素.closest('[data-dockkit-pane], [data-dockkit-float]')
        if 窗 is None:
            return
        拥有=窗.closest('[data-sidebar-right-session]')
        if 拥有 is None:
            return
        会话标识=_数据集(拥有,'sidebarRightSession')
        窗格标识=_数据集(窗,'dockkitPane')
        if 窗格标识 is None:
            窗格标识=_数据集(窗,'dockkitFloat')
        if 会话标识 is None or 窗格标识 is None:
            return
        签=元素.closest('[data-dockkit-tab]')
        if 签 is None:
            签=窗.querySelector('[role="tab"][aria-selected="true"], [data-dockkit-float-title]')
        标记=元素.closest('[data-sidebar-right-occurrence]')
        if 标记 is None and 签 is not None:
            标记=签.querySelector('[data-sidebar-right-occurrence]')
        出现=None if 标记 is None else _数据集(标记,'sidebarRightOccurrence')
        已聚焦[0]={'element':元素,'sessionId':会话标识,'paneId':窗格标识,'occurrence':出现}
        移除观察[0].observe(拥有,{'childList':True,'subtree':True})
        if 拥有.parentElement is not None:
            移除观察[0].observe(拥有.parentElement,{'childList':True})

    def 焦点离开(事件):
        '焦点离开文档就把记录清掉'
        if 事件.relatedTarget is None and 已聚焦[0] is not None and 已聚焦[0]['element'].isConnected:
            已聚焦[0]=None
            移除观察[0].disconnect()

    def 指针(事件):
        '点在窗格里、又不是控件上，就把焦点给窗格'
        路径=事件.composedPath()
        元素=None
        for 值 in 路径:
            if getattr(值,'nodeType',None)==1:
                元素=值
                break
        if 元素 is None:
            return
        窗=元素.closest('[data-sidebar-right-session] [data-dockkit-pane], [data-sidebar-right-session] [data-dockkit-float]')
        if 窗 is None:
            已聚焦[0]=None
            移除观察[0].disconnect()
        控件=元素.closest('button, input, textarea, select, a, [contenteditable], [tabindex], iframe')
        if 窗 is not None and (控件 is None or 控件 is 窗):
            窗.focus({'preventScroll':True})

    def 模糊():
        '窗口失焦后的微任务里再捕获一次'
        def 再捕获():
            '还在观察才捕获'
            if 活动[0]:
                捕获()
        文档.defaultView.queueMicrotask(再捕获)

    文档.addEventListener('focusin',捕获)
    文档.addEventListener('focusout',焦点离开)
    文档.addEventListener('pointerdown',指针,True)
    if 文档.defaultView is not None:
        文档.defaultView.addEventListener('blur',模糊)
        文档.defaultView.addEventListener('focus',捕获)
    捕获()

    def 拆除():
        '摘掉全部监听'
        活动[0]=False
        移除观察[0].disconnect()
        文档.removeEventListener('focusin',捕获)
        文档.removeEventListener('focusout',焦点离开)
        文档.removeEventListener('pointerdown',指针,True)
        if 文档.defaultView is not None:
            文档.defaultView.removeEventListener('blur',模糊)
            文档.defaultView.removeEventListener('focus',捕获)

    return 拆除
