'一块窗格：标签条、正文，以及拖拽时的投放提示。手势都从回调离开'
import pywebbridge
from ...ui_基础界面组件.icons import 图标
from ...ui_基础界面组件.提示泡 import 提示泡
from ..引擎.树 import 取标签
from .标签标题 import 标签标题
from .标签菜单 import 标签菜单
from .渲染 import 类名,有类,标有无,标值,清空,挂上,注入样式

__all__=['标签条','投放提示','标签面板']

面板框='M9.67272 0.522841C10.8339 0.522841 11.76 0.522714 12.4963 0.602493C13.2453 0.683657 13.8789 0.854248 14.4264 1.25197C14.7504 1.48739 15.0355 1.77247 15.2709 2.0965C15.6686 2.64394 15.8392 3.27758 15.9204 4.02655C16.0002 4.7629 16 5.68895 16 6.85014V9.14986C16 10.3111 16.0002 11.2371 15.9204 11.9735C15.8392 12.7224 15.6686 13.3561 15.2709 13.9035C15.0355 14.2275 14.7504 14.5126 14.4264 14.748C13.8789 15.1458 13.2453 15.3163 12.4963 15.3975C11.76 15.4773 10.8339 15.4772 9.67272 15.4772H6.3273C5.16611 15.4772 4.24006 15.4773 3.50371 15.3975C2.75474 15.3163 2.1211 15.1458 1.57366 14.748C1.24963 14.5126 0.964549 14.2275 0.729131 13.9035C0.331407 13.3561 0.160817 12.7224 0.0796529 11.9735C-0.000126137 11.2371 1.25338e-09 10.3111 1.25338e-09 9.14986V6.85014C1.25329e-09 5.68895 -0.000126137 4.7629 0.0796529 4.02655C0.160817 3.27758 0.331407 2.64394 0.729131 2.0965C0.964549 1.77247 1.24963 1.48739 1.57366 1.25197C2.1211 0.854248 2.75474 0.683657 3.50371 0.602493C4.24006 0.522714 5.16611 0.522841 6.3273 0.522841H9.67272ZM4.1828 14.0873L5.54303 14.1118C5.78636 14.1128 6.04709 14.1169 6.3273 14.1169H9.67272C10.8639 14.1169 11.7032 14.1164 12.3493 14.0465C12.9824 13.9779 13.3497 13.8494 13.6268 13.6482C13.8354 13.4966 14.0195 13.3125 14.1711 13.1039C14.3723 12.8268 14.5007 12.4595 14.5693 11.8264C14.6393 11.1803 14.6398 10.341 14.6398 9.14986V6.85014C14.6398 5.65896 14.6393 4.81967 14.5693 4.1736C14.5007 3.54048 14.3723 3.17318 14.1711 2.89609C14.0195 2.68747 13.8354 2.50337 13.6268 2.35179C13.3497 2.1506 12.9824 2.02212 12.3493 1.95353C11.7032 1.88358 10.8639 1.88307 9.67272 1.88307H6.3273C6.04709 1.88307 5.78636 1.8862 5.54303 1.88715L4.1828 1.91166C3.99125 1.9216 3.8148 1.93577 3.65076 1.95353C3.01764 2.02212 2.65034 2.1506 2.37325 2.35179C2.16463 2.50337 1.98052 2.68747 1.82895 2.89609C1.62776 3.17318 1.49928 3.54048 1.43069 4.1736C1.36074 4.81967 1.36023 5.65896 1.36023 6.85014V9.14986C1.36023 10.341 1.36074 11.1803 1.43069 11.8264C1.49928 12.4595 1.62776 12.8268 1.82895 13.1039C1.98052 13.3125 2.16463 13.4966 2.37325 13.6482C2.65034 13.8494 3.01764 13.9779 3.65076 14.0465C3.81478 14.0642 3.99127 14.0774 4.1828 14.0873Z'
区位填充={
    'center':'M4.56 3.48H11.44A1.6 1.6 0 0 1 13.04 5.08V10.92A1.6 1.6 0 0 1 11.44 12.52H4.56A1.6 1.6 0 0 1 2.96 10.92V5.08A1.6 1.6 0 0 1 4.56 3.48Z',
    'left':'M4 0.523H8V15.477H4A4 4 0 0 1 0 11.477V4.523A4 4 0 0 1 4 0.523Z',
    'right':'M8 0.523H12A4 4 0 0 1 16 4.523V11.477A4 4 0 0 1 12 15.477H8Z',
    'top':'M0 8V4.523A4 4 0 0 1 4 0.523H12A4 4 0 0 1 16 4.523V8Z',
    'bottom':'M0 8H16V11.477A4 4 0 0 1 12 15.477H4A4 4 0 0 1 0 11.477Z',
}

def 图形(文档):
    '16 像素的空 svg'
    图=文档.createElementNS('http://www.w3.org/2000/svg','svg')
    图.setAttribute('width','16')
    图.setAttribute('height','16')
    图.setAttribute('viewBox','0 0 16 16')
    图.setAttribute('fill','none')
    图.setAttribute('aria-hidden','true')
    return 图

def 路径(文档,数据,填充=None):
    '一条 path。没给填充就用描边'
    条=文档.createElementNS('http://www.w3.org/2000/svg','path')
    条.setAttribute('d',数据)
    if 填充 is None:
        条.setAttribute('stroke','currentColor')
    else:
        条.setAttribute('fill',填充)
    return 条

class 停靠提示:
    '一块落点卡片：虚线框、区位字形和说明'
    def __init__(自身,属性):
        '画出这一区的提示'
        自身.属性=属性
        自身.根=None
        自身.渲染()

    def 渲染(自身):
        '按区位和是否正在指向来画'
        窗口=自身.属性['window']
        文档=窗口.document
        区=自身.属性['zone']
        根=文档.createElement('div')
        根.className='dockHint'
        根.setAttribute('data-dockkit-dock-zone',区)
        标有无(根,'data-dockkit-drop-active',自身.属性['active'])
        卡=文档.createElement('div')
        卡.className='dockHintCard'
        图=图形(文档)
        框=路径(文档,面板框,'currentColor')
        框.setAttribute('fill-rule','evenodd')
        框.setAttribute('clip-rule','evenodd')
        图.appendChild(框)
        图.appendChild(路径(文档,区位填充[区],'currentColor'))
        卡.appendChild(图)
        字=文档.createElement('span')
        字.className='dockHintLabel'
        字.textContent=自身.属性['labels']['dropZone'][区]
        卡.appendChild(字)
        根.appendChild(卡)
        自身.根=根
        return 根

class 标签条:
    '窗格的标签条：拖出、放下、分割和关闭'
    def __init__(自身,属性):
        '记下窗格并画出条带'
        自身.属性=属性
        自身.根=None
        自身.芯片盒=None
        自身.芯片={}
        自身.标题={}
        自身.菜单=None
        自身.菜单标签=None
        自身.滚动听=None
        自身.尺寸观察=None
        自身.渲染()

    def 回调(自身):
        '当前这份回调'
        return 自身.属性['callbacks']

    def 条带下标(自身):
        '拖拽如果落在这条带上，插入槽是多少'
        目标=自身.回调().get('dropTarget')
        窗格=自身.属性['pane']
        if 目标 is not None and 目标['kind']=='strip' and 目标['paneId']==窗格['id']:
            return 目标['index']
        return None

    def 激活(自身,标签标识):
        '点一下或按键选中。已经是活动窗格里的当前标签就什么都不做'
        状态=自身.属性['state']
        窗格=自身.属性['pane']
        if 状态['activePaneId']==窗格['id'] and 窗格['activeTabId']==标签标识:
            return
        自身.回调()['onFocusTab'](标签标识)

    def 聚焦芯片(自身,标签标识):
        '把焦点挪到这一张芯片'
        芯片=自身.芯片.get(标签标识)
        if 芯片 is None:
            return
        芯片.focus()

    def 关菜单(自身):
        '关掉打开着的菜单'
        自身.菜单标签=None
        if 自身.菜单 is not None:
            自身.菜单.拆除()
            自身.菜单=None

    def 开菜单(自身,标签标识,锚):
        '同一张再按一次就关掉，否则打开'
        if 自身.菜单标签==标签标识:
            自身.关菜单()
            return
        自身.菜单标签=标签标识
        回调=自身.回调()
        可关=回调['canCloseTab'](标签标识)
        标签=取标签(自身.属性['state'],标签标识)
        窗口=自身.属性['window']

        def 解散():
            '菜单自己关掉'
            自身.关菜单()

        def 关闭():
            '菜单里的关闭'
            自身.关菜单()
            回调['onCloseTab'](标签标识)

        附加=None
        if 回调.get('renderTabMenuItems') is not None:
            附加=回调['renderTabMenuItems'](标签,解散)
        菜单属性={
            'window':窗口,
            'labels':回调['labels'],
            'anchor':锚,
            'onDismiss':解散,
            'extras':附加,
        }
        if 可关:
            菜单属性['onClose']=关闭
        if 自身.菜单 is None:
            自身.菜单=标签菜单(菜单属性)
        else:
            自身.菜单.更新(菜单属性)

    def 套滚动(自身):
        '按滚出去的边写 data-dockkit-strip-scroll，并让活动芯片露出来'
        盒=自身.芯片盒
        if 盒 is None:
            return
        起=盒.scrollLeft>1
        止=盒.scrollLeft+盒.clientWidth<盒.scrollWidth-1
        if 起 and 止:
            侧='start end'
        elif 起:
            侧='start'
        elif 止:
            侧='end'
        else:
            侧=None
        标值(盒,'data-dockkit-strip-scroll',侧)
        窗格=自身.属性['pane']
        活动=窗格['activeTabId']
        if 活动 is None or 活动 not in 自身.芯片:
            return
        芯片=自身.芯片[活动]
        界=盒.getBoundingClientRect()
        盒芯片=芯片.getBoundingClientRect()
        褪=24
        if 盒芯片.left<界.left:
            盒.scrollLeft+=盒芯片.left-界.left-褪
        elif 盒芯片.right>界.right:
            盒.scrollLeft+=盒芯片.right-界.right+褪

    def 装滚动(自身):
        '滚动和尺寸变化时重写淡出边'
        盒=自身.芯片盒
        窗口=自身.属性['window']
        if 自身.滚动听 is not None:
            盒.removeEventListener('scroll',自身.滚动听)
        def 滚动():
            '滚动后重算淡出'
            自身.套滚动()
        自身.滚动听=滚动
        盒.addEventListener('scroll',滚动,{'passive':True})
        if 自身.尺寸观察 is not None:
            自身.尺寸观察.disconnect()
            自身.尺寸观察=None
        if hasattr(窗口,'ResizeObserver'):
            def 变了():
                '盒子变了就重算淡出'
                自身.套滚动()
            自身.尺寸观察=窗口.ResizeObserver(变了)
            自身.尺寸观察.observe(盒)

    def 画芯片(自身,文档,标签标识,序号,选定,可关,安静):
        '一张芯片，含标题和可选的关闭'
        状态=自身.属性['state']
        回调=自身.回调()
        标签=取标签(状态,标签标识)
        芯片=文档.createElement('div')
        芯片.setAttribute('role','tab')
        芯片.setAttribute('aria-selected','true' if 选定 else 'false')
        芯片.tabIndex=0 if 选定 else -1
        拖=回调.get('draggingTabId')==标签标识
        芯片.className=类名('tab',选定 and 'tabActive',安静 and 'tabQuiet',拖 and 'tabDragging')
        芯片.setAttribute('data-dockkit-tab',标签标识)
        标有无(芯片,'data-dockkit-tab-quiet',安静)
        标题内容=标签['title']
        if 回调.get('renderTabTitle') is not None:
            绘=回调['renderTabTitle'](标签)
            if 绘 is not None:
                标题内容=绘
        标题=标签标题({'window':自身.属性['window'],'children':标题内容})
        芯片.appendChild(标题.根)
        自身.标题[标签标识]=标题
        if 可关:
            钮=文档.createElement('button')
            钮.setAttribute('type','button')
            钮.className='tabClose'
            钮.setAttribute('aria-label',回调['labels']['closeTab'])
            if 回调['labels'].get('closeTabShortcut'):
                钮.setAttribute('aria-keyshortcuts',回调['labels']['closeTabShortcut'])
            钮.setAttribute('data-dockkit-tab-close',标签标识)
            图标('close-fill-14',{'window':自身.属性['window'],'parent':钮,'size':14})

            def 按下关(事件,钮=钮):
                '关闭钮自己的按下不能变成拖拽'
                事件.stopPropagation()

            def 点关(事件,标识=标签标识):
                '关掉这张标签'
                事件.stopPropagation()
                自身.回调()['onCloseTab'](标识)

            钮.addEventListener('pointerdown',按下关)
            钮.addEventListener('click',点关)
            快捷=回调['labels'].get('closeTabKeys')
            泡=提示泡({
                'window':自身.属性['window'],
                'label':回调['labels']['closeTab'],
                'side':'bottom',
                'delayMs':500,
                'disabled':自身.菜单标签 is not None,
                'shortcutKeys':快捷,
                'children':钮,
            })
            芯片.appendChild(泡.渲染())

        def 按下(事件,标识=标签标识):
            '主按是拖拽的起点。次键留给菜单'
            if 事件.button==2:
                return
            自身.回调()['onTabPressed'](标识,事件)

        def 点击(事件,标识=标签标识):
            '松开在芯片上才聚焦。拖到别处不会点到这里'
            事件.stopPropagation()
            自身.激活(标识)

        def 按键(事件,标识=标签标识,芯片=芯片):
            '左右和首尾在芯片之间移动焦点。回车和空格才选中'
            if 事件.target is not 芯片:
                return
            if 事件.altKey or 事件.ctrlKey or 事件.metaKey or 事件.shiftKey or getattr(事件,'isComposing',False):
                return
            序=自身.属性['pane']['tabs']
            个数=len(序)
            位=序.index(标识)
            键=事件.key
            下一=None
            if 键=='ArrowLeft':
                下一=序[(位-1+个数)%个数]
            elif 键=='ArrowRight':
                下一=序[(位+1)%个数]
            elif 键=='Home':
                下一=序[0]
            elif 键=='End':
                下一=序[len(序)-1]
            if 下一 is not None:
                事件.preventDefault()
                自身.聚焦芯片(下一)
                return
            if 键=='Enter' or 键==' ':
                事件.preventDefault()
                自身.激活(标识)

        def 次键(事件,标识=标签标识,芯片=芯片):
            '次键打开或关掉这张的菜单'
            事件.preventDefault()
            自身.开菜单(标识,芯片)

        芯片.addEventListener('pointerdown',按下)
        芯片.addEventListener('click',点击)
        芯片.addEventListener('keydown',按键)
        芯片.addEventListener('contextmenu',次键)
        自身.芯片[标签标识]=芯片
        return 芯片

    def 槽(自身,文档,序号,是插入):
        '芯片之间的槽。被投放瞄中时改成插入记号'
        槽=文档.createElement('div')
        槽.className=类名('slot',是插入 and 'slotCaret')
        if 是插入:
            槽.setAttribute('data-dockkit-caret',str(序号))
        return 槽

    def 渲染(自身):
        '画出整条标签条'
        窗口=自身.属性['window']
        文档=窗口.document
        注入样式(文档)
        状态=自身.属性['state']
        窗格=自身.属性['pane']
        回调=自身.回调()
        for 标题 in 自身.标题.values():
            标题.拆除()
        自身.标题={}
        自身.芯片={}
        自身.关菜单()
        if 自身.根 is not None:
            父=自身.根.parentNode
            自身.根.remove()
        else:
            父=自身.属性.get('parent')
        根=文档.createElement('div')
        根.className='tabStrip'
        根.setAttribute('role','tablist')
        根.setAttribute('data-dockkit-strip',窗格['id'])
        标有无(根,'data-window-drag',len(状态['floats'])==0)
        盒=文档.createElement('div')
        盒.className='stripTabs'
        盒.setAttribute('role','presentation')
        盒.setAttribute('data-dockkit-strip-tabs',窗格['id'])
        插入=自身.条带下标()
        for 序号,标签标识 in enumerate(窗格['tabs']):
            选定=标签标识==窗格['activeTabId']
            可关=回调['canCloseTab'](标签标识)
            安静=(not 可关) and len(窗格['tabs'])==1
            if 序号>0 or 插入==序号:
                盒.appendChild(自身.槽(文档,序号,插入==序号))
            盒.appendChild(自身.画芯片(文档,标签标识,序号,选定,可关,安静))
        if 插入==len(窗格['tabs']):
            盒.appendChild(自身.槽(文档,插入,True))
        根.appendChild(盒)
        自身.芯片盒=盒
        if 回调['canAddTab'](窗格['id']):
            加=文档.createElement('button')
            加.setAttribute('type','button')
            加.className='addTab'
            加.setAttribute('aria-label',回调['labels']['addTab'])
            加.setAttribute('data-dockkit-add-tab',窗格['id'])
            图标('plus-16',{'window':窗口,'parent':加,'size':14})

            def 点加(事件):
                '条带末尾的加号'
                事件.stopPropagation()
                自身.回调()['onAddTab'](自身.属性['pane']['id'])

            加.addEventListener('click',点加)
            根.appendChild(提示泡({
                'window':窗口,
                'label':回调['labels']['addTab'],
                'side':'bottom',
                'delayMs':500,
                'children':加,
            }).渲染())
        填=文档.createElement('div')
        填.className='stripFill'
        填.setAttribute('data-dockkit-strip-fill','')
        根.appendChild(填)
        阻断=回调['splitBlock'](窗格['id'])
        if not (回调.get('hideSplitWhenBlocked') and 阻断 is not None):
            if 阻断=='budget':
                说明=回调['labels']['splitPaneDisabled']
            elif 阻断=='width':
                说明=回调['labels']['splitPaneNarrow']
            else:
                说明=回调['labels']['splitPane']
            包=文档.createElement('span')
            if 阻断 is not None:
                包.tabIndex=0
                包.setAttribute('aria-label',说明)
            钮=文档.createElement('button')
            钮.setAttribute('type','button')
            钮.className='iconButton'
            钮.setAttribute('aria-label',回调['labels']['splitPane'])
            if 回调['labels'].get('splitPaneShortcut'):
                钮.setAttribute('aria-keyshortcuts',回调['labels']['splitPaneShortcut'])
            钮.disabled=阻断 is not None
            钮.setAttribute('data-dockkit-split-button',窗格['id'])
            标值(钮,'data-dockkit-split-blocked',阻断)
            图=图形(文档)
            图.appendChild(路径(文档,'M13.5 1.5H2.5C1.94772 1.5 1.5 1.94772 1.5 2.5V13.5C1.5 14.0523 1.94772 14.5 2.5 14.5H13.5C14.0523 14.5 14.5 14.0523 14.5 13.5V2.5C14.5 1.94772 14.0523 1.5 13.5 1.5Z'))
            图.appendChild(路径(文档,'M8 1.5V14.5'))
            钮.appendChild(图)

            def 点分(事件):
                '切开这块窗格'
                事件.stopPropagation()
                自身.回调()['onSplitPane'](自身.属性['pane']['id'])

            钮.addEventListener('click',点分)
            包.appendChild(钮)
            根.appendChild(提示泡({
                'window':窗口,
                'label':说明,
                'side':'bottom',
                'delayMs':500,
                'shortcutKeys':回调['labels'].get('splitPaneKeys'),
                'children':包,
            }).渲染())
        if 窗格['id']==回调.get('chromePaneId') and 回调.get('chrome') is not None:
            铬=文档.createElement('div')
            铬.className='stripChrome'
            铬.setAttribute('data-dockkit-strip-chrome','')

            def 点铬(事件):
                '嵌入方控件自己报意图，不能再记一笔窗格焦点'
                事件.stopPropagation()

            铬.addEventListener('click',点铬)
            挂上(铬,回调['chrome'])
            根.appendChild(铬)
        自身.根=根
        if 父 is not None:
            父.appendChild(根)
        自身.装滚动()
        自身.套滚动()
        return 根

    def 套预览(自身):
        '只改拖拽样式和插入槽，不换掉按下的那张芯片'
        回调=自身.回调()
        窗格=自身.属性['pane']
        拖=回调.get('draggingTabId')
        for 标识,芯片 in 自身.芯片.items():
            有类(芯片,'tabDragging',标识==拖)
        插入=自身.条带下标()
        盒=自身.芯片盒
        if 盒 is None:
            return
        旧=[]
        子=盒.firstChild
        while 子 is not None:
            下一=子.nextSibling
            if 子.getAttribute('data-dockkit-caret') is not None or (isinstance(子.className,str) and 'slot' in 子.className.split()):
                旧.append(子)
            子=下一
        for 节点 in 旧:
            节点.remove()
        文档=盒.ownerDocument
        序=list(窗格['tabs'])
        for 序号,标签标识 in enumerate(序):
            芯片=自身.芯片.get(标签标识)
            if 芯片 is None:
                continue
            if 序号>0 or 插入==序号:
                盒.insertBefore(自身.槽(文档,序号,插入==序号),芯片)
        if 插入==len(序):
            盒.appendChild(自身.槽(文档,插入,True))

    def 更新(自身,属性):
        '状态变了就整条重画'
        自身.属性=属性
        return 自身.渲染()

    def 拆除(自身):
        '卸滚动、标题和菜单'
        if 自身.芯片盒 is not None and 自身.滚动听 is not None:
            自身.芯片盒.removeEventListener('scroll',自身.滚动听)
        if 自身.尺寸观察 is not None:
            自身.尺寸观察.disconnect()
            自身.尺寸观察=None
        for 标题 in 自身.标题.values():
            标题.拆除()
        自身.关菜单()

class 投放提示:
    '窗格正文上的落点提示。没有指向这块时什么都不画'
    def __init__(自身,属性):
        '记下窗格'
        自身.属性=属性
        自身.根=None
        自身.渲染()

    def 渲染(自身):
        '按当前投放目标画出遮罩和卡片'
        窗口=自身.属性['window']
        文档=窗口.document
        回调=自身.属性['callbacks']
        窗格=自身.属性['pane']
        目标=回调.get('dropTarget')
        区=None
        if 目标 is not None and 目标.get('kind')=='zone' and 目标.get('paneId')==窗格['id']:
            区=目标['zone']
        if 自身.根 is None:
            自身.根=文档.createElement('div')
        else:
            清空(自身.根)
        if 区 is None:
            return 自身.根
        罩=文档.createElement('div')
        罩.className='dockScrim'
        罩.setAttribute('data-dockkit-dock-scrim','')
        自身.根.appendChild(罩)
        if 回调.get('horizontalDrops') and 区!='center':
            自身.根.appendChild(停靠提示({
                'window':窗口,'zone':'left','active':区=='left','labels':回调['labels'],
            }).根)
            自身.根.appendChild(停靠提示({
                'window':窗口,'zone':'right','active':区=='right','labels':回调['labels'],
            }).根)
        else:
            自身.根.appendChild(停靠提示({
                'window':窗口,'zone':区,'active':True,'labels':回调['labels'],
            }).根)
        return 自身.根

    def 更新(自身,属性):
        '投放目标变了就重画提示'
        自身.属性=属性
        return 自身.渲染()

class 标签面板:
    '递归布局里的一块窗格'
    def __init__(自身,属性):
        '画出条带和正文'
        自身.属性=属性
        自身.根=None
        自身.条=None
        自身.提示=None
        自身.渲染()

    def 渲染(自身):
        '条带在上，正文在下。空窗格写嵌入方的空文案'
        窗口=自身.属性['window']
        文档=窗口.document
        注入样式(文档)
        状态=自身.属性['state']
        窗格=自身.属性['pane']
        回调=自身.属性['callbacks']
        if 自身.根 is not None and 自身.根.parentNode is not None:
            父=自身.根.parentNode
        else:
            父=自身.属性.get('parent')
        if 自身.条 is not None:
            自身.条.拆除()
        根=文档.createElement('section')
        根.className='pane'
        根.setAttribute('data-dockkit-pane',窗格['id'])
        根.tabIndex=-1
        标有无(根,'data-dockkit-pane-active',状态['activePaneId']==窗格['id'])

        def 点窗(事件):
            '点在窗格上，且还不是活动窗格，就聚焦它'
            if 自身.属性['state']['activePaneId']!=自身.属性['pane']['id']:
                自身.属性['callbacks']['onFocusPane'](自身.属性['pane']['id'])

        根.addEventListener('click',点窗)
        条属性={'window':窗口,'state':状态,'pane':窗格,'callbacks':回调,'parent':根}
        自身.条=标签条(条属性)
        身=文档.createElement('div')
        身.className='paneBody'
        if 窗格['activeTabId'] is None:
            空=文档.createElement('p')
            空.className='empty'
            空.textContent=回调['labels']['emptyPane']
            身.appendChild(空)
        else:
            挂上(身,回调['renderTab'](取标签(状态,窗格['activeTabId'])))
        自身.提示=投放提示({'window':窗口,'pane':窗格,'callbacks':回调})
        身.appendChild(自身.提示.根)
        根.appendChild(身)
        if 自身.根 is not None:
            自身.根.replaceWith(根)
        elif 父 is not None:
            父.appendChild(根)
        自身.根=根
        return 根

    def 套预览(自身,回调):
        '预览只动条带和投放提示'
        自身.属性['callbacks']=回调
        if 自身.条 is not None:
            自身.条.属性['callbacks']=回调
            自身.条.套预览()
        if 自身.提示 is not None:
            自身.提示.更新({'window':自身.属性['window'],'pane':自身.属性['pane'],'callbacks':回调})

    def 更新(自身,属性):
        '布局变了就重画这块窗格'
        自身.属性=属性
        return 自身.渲染()

    def 拆除(自身):
        '卸掉条带'
        if 自身.条 is not None:
            自身.条.拆除()
