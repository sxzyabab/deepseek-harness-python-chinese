"""停靠与浮动侧栏页的活 DOM 归属。
焦点从当前挂载会话的 markup 捕获；节点被换掉时尽量保焦点与选区。
"""
import builtins#页面全局

__all__=['从元素取右侧侧栏目标','可见侧栏窗格','观察侧栏焦点']#仅中文公开名

元素类型=builtins.Element#DOM Element
变动观察=builtins.MutationObserver#MutationObserver
微任务=builtins.queueMicrotask#queueMicrotask

def 从元素取右侧侧栏目标(元素,会话标识,布局,出现次):
    """从活拥有方 markup 读窗格与页签身份，含嵌入 iframe。
    元素为产品文档里聚焦或指针激活的元素；会话标识为侧栏当前绘制的会话；
    布局为该会话当前已提交布局；出现次为已提交页签的当前 occurrence 查找。
    返回捕获的页；陈旧、隐藏或域外元素为 None。
    """
    if 元素 is None or not 元素.isConnected:#无效
        return None#无
    拥有方=元素.closest('[data-sidebar-right-session]')#会话根
    if 拥有方 is None or getattr(拥有方.dataset,'sidebarRightSession',None)!=会话标识:#非本会话
        return None#无
    容器=元素.closest('[data-dockkit-pane], [data-dockkit-float]')#窗格容器
    窗格标识=(getattr(容器.dataset,'dockkitPane',None) if 容器 is not None else None)
    if 窗格标识 is None and 容器 is not None:#浮层
        窗格标识=getattr(容器.dataset,'dockkitFloat',None)#浮窗 id
    if 窗格标识 is None or (容器 is not None and 容器.closest('[hidden], [aria-hidden="true"]') is not None):#隐藏
        return None#无
    窗格=布局['nodes'][窗格标识] if 窗格标识 in 布局['nodes'] else None#节点
    if 窗格 is None or 窗格['kind']!='pane' or (窗格['host']=='dock' and not 布局['expanded']):#非法
        return None#无
    签元素=元素.closest('[data-dockkit-tab], [data-sidebar-right-tab]')#页签元素
    标签标识=None#页签 id
    if 签元素 is not None:#有签元素
        标签标识=getattr(签元素.dataset,'dockkitTab',None) or getattr(签元素.dataset,'sidebarRightTab',None)#签 id
    if 标签标识 is None:#回落活动签
        标签标识=窗格['activeTabId'] if 'activeTabId' in 窗格 else None#活动签
    if 标签标识 is not None and (标签标识 not in 窗格['tabs'] or 标签标识 not in 布局['tabs']):#陈旧签
        return None#无
    持有=None if 标签标识 is None else 出现次(标签标识)#出现次
    标记=元素.closest('[data-sidebar-right-occurrence]')#本元素标记
    if 标记 is None and 签元素 is not None:#签内找
        标记=签元素.querySelector('[data-sidebar-right-occurrence]')#签内标记
    if 标记 is not None:#有标记
        持有标识=持有['id'] if isinstance(持有,dict) and 'id' in 持有 else getattr(持有,'id',None)#持有 id
        if getattr(标记.dataset,'sidebarRightOccurrence',None)!=持有标识:#标记过期
            return None#无
    修订=None#导航修订
    if 持有 is not None:#有出现次
        导航=持有['navigation'] if isinstance(持有,dict) and 'navigation' in 持有 else getattr(持有,'navigation',None)#导航
        if 导航 is not None:#有
            修订=导航.getSnapshot()['revision']#修订号
    return {#目标
        'sessionId':会话标识,#会话
        'paneId':窗格标识,#窗格
        'host':窗格['host'],#宿主
        'tabId':标签标识,#页签
        'occurrence':持有,#出现次
        'navigationRevision':修订,#修订
    }#目标结束

def 可见侧栏窗格(文档,会话标识,窗格标识):
    """找某会话的可见窗格，优先请求窗格，再回退活动窗格。
    文档含停靠与浮动窗格；会话标识为可能接收焦点的会话；
    窗格标识为操作改布局前偏好的窗格。
    返回仍存活的可见窗格；会话无窗格时为 None。
    """
    窗表=[]#可见窗
    for 窗 in 文档.querySelectorAll('[data-dockkit-pane], [data-dockkit-float]'):#全窗
        拥有方=窗.closest('[data-sidebar-right-session]')#会话根
        if (拥有方 is not None
            and getattr(拥有方.dataset,'sidebarRightSession',None)==会话标识
            and 窗.closest('[hidden], [aria-hidden="true"]') is None
            and (窗.hasAttribute('data-dockkit-float') or 拥有方.hasAttribute('data-sidebar-right-open'))):#可见
            窗表.append(窗)#收下
    for 窗 in 窗表:#优先请求窗
        标识=getattr(窗.dataset,'dockkitPane',None) or getattr(窗.dataset,'dockkitFloat',None)#id
        if 标识==窗格标识:#命中
            return 窗#请求窗
    for 窗 in 窗表:#活动窗
        if 窗.hasAttribute('data-dockkit-pane-active') or 窗.hasAttribute('data-dockkit-float-active'):#活动
            return 窗#活动窗
    return 窗表[0] if len(窗表)>0 else None#首个或无

def 观察侧栏焦点(文档):
    """观察窗格焦点；DOM 节点被替换时保留焦点，尽量保住文本选区。
    文档为侧栏拥有监听生命周期的产品文档。
    返回全部 document/window 监听的拆除器。
    """
    活跃=[True]#寿命开关
    已焦=[None]#{element,sessionId,paneId,occurrence}
    def 移除回调(_记录):
        """节点被卸时把焦点挪到同 occurrence 的新窗格。"""
        焦=已焦[0]#当前
        if 焦 is None or 焦['element'].isConnected:#仍连通
            return#止
        先前=焦#先前
        已焦[0]=None#清
        移除.disconnect()#停观察
        if 文档.activeElement is not 文档.body:#焦点不在 body
            return#止
        挪到=None#新窗
        if 先前['occurrence'] is not None:#有 occurrence
            for 标记 in 文档.querySelectorAll('[data-sidebar-right-occurrence]'):#找标记
                if getattr(标记.dataset,'sidebarRightOccurrence',None)==先前['occurrence']:#命中
                    挪到=标记.closest('[data-dockkit-pane], [data-dockkit-float]')#窗
                    break#止
        新窗标识=None#新窗 id
        if 挪到 is not None:#有新窗
            新窗标识=getattr(挪到.dataset,'dockkitPane',None) or getattr(挪到.dataset,'dockkitFloat',None)#id
        目标窗=可见侧栏窗格(文档,先前['sessionId'],新窗标识 if 新窗标识 is not None else 先前['paneId'])#可见窗
        if 目标窗 is not None:#有
            目标窗.focus({'preventScroll':True})#聚焦
    移除=变动观察(移除回调)#移除观察
    def 捕获(_事件=None):
        """记下当前焦点归属并观察拥有方移除。"""
        移除.disconnect()#先停
        已焦[0]=None#清
        元素=文档.activeElement#焦点
        if 元素 is None:#无
            return#止
        窗=元素.closest('[data-dockkit-pane], [data-dockkit-float]')#窗格
        if 窗 is None:#无窗
            return#止
        拥有方=窗.closest('[data-sidebar-right-session]')#会话根
        if 拥有方 is None:#无
            return#止
        会话标识=getattr(拥有方.dataset,'sidebarRightSession',None)#会话
        窗格标识=getattr(窗.dataset,'dockkitPane',None) or getattr(窗.dataset,'dockkitFloat',None)#窗格
        if 会话标识 is None or 窗格标识 is None:#缺身份
            return#止
        签=元素.closest('[data-dockkit-tab]')#页签
        if 签 is None:#回落活动签/浮层标题
            签=窗.querySelector('[role="tab"][aria-selected="true"], [data-dockkit-float-title]')#回落
        标记=元素.closest('[data-sidebar-right-occurrence]')#本元素标记
        if 标记 is None and 签 is not None:#签内找
            标记=签.querySelector('[data-sidebar-right-occurrence]')#签内
        已焦[0]={#记下
            'element':元素,#元素
            'sessionId':会话标识,#会话
            'paneId':窗格标识,#窗格
            'occurrence':getattr(标记.dataset,'sidebarRightOccurrence',None) if 标记 is not None else None,#出现次
        }#结束
        移除.observe(拥有方,{'childList':True,'subtree':True})#观察会话席
        #整会话座位与页签体一并观察移除
        if 拥有方.parentElement is not None:#有父
            移除.observe(拥有方.parentElement,{'childList':True})#观察父
    def 焦点离开(事件):
        """相关目标空且原元素仍连通则清跟踪。"""
        焦=已焦[0]#当前
        if 事件.relatedTarget is None and 焦 is not None and 焦['element'].isConnected:#丢焦点
            已焦[0]=None#清
            移除.disconnect()#停
    def 指针按下(事件):
        """点击窗格空白时把焦点落到窗格。"""
        元素=None#命中元素
        for 值 in 事件.composedPath():#路径
            if isinstance(值,元素类型):#元素
                元素=值#记下
                break#止
        if 元素 is None:#无
            return#止
        窗=元素.closest('[data-sidebar-right-session] [data-dockkit-pane], [data-sidebar-right-session] [data-dockkit-float]')#窗
        if 窗 is None:#点在域外
            已焦[0]=None#清
            移除.disconnect()#停
        控件=元素.closest('button, input, textarea, select, a, [contenteditable], [tabindex], iframe')#控件
        if 窗 is not None and (控件 is None or 控件 is 窗):#空白点窗
            窗.focus({'preventScroll':True})#聚焦窗
    def 失焦(_事件=None):
        """窗口失焦后微任务再捕获。"""
        def 再捕():
            """仍活跃才捕获。"""
            if 活跃[0]:#活跃
                捕获()#捕获
        微任务(再捕)#微任务
    文档.addEventListener('focusin',捕获)#焦点入
    文档.addEventListener('focusout',焦点离开)#焦点出
    文档.addEventListener('pointerdown',指针按下,True)#指针捕获
    视窗=文档.defaultView#窗口
    if 视窗 is not None:#有
        视窗.addEventListener('blur',失焦)#窗失焦
        视窗.addEventListener('focus',捕获)#窗获焦
    捕获()#初捕
    def 拆除():
        """卸全部监听与观察。"""
        活跃[0]=False#停
        移除.disconnect()#停观察
        文档.removeEventListener('focusin',捕获)#卸
        文档.removeEventListener('focusout',焦点离开)#卸
        文档.removeEventListener('pointerdown',指针按下,True)#卸
        if 视窗 is not None:#有窗
            视窗.removeEventListener('blur',失焦)#卸
            视窗.removeEventListener('focus',捕获)#卸
    return 拆除#拆除器
