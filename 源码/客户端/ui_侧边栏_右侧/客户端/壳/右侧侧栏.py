'右栏席：一棵面板，正文和标题交给已登记的类型'
from ....模块.客户端.通告 import 取握手窗口
import os
from ....ui_对话.异常 import 注入模块样式文件,标样式模块
from ....ui_停靠套件.组件.停靠面 import 停靠面
from ....ui_停靠套件.引擎.约束 import 可分割
from ....ui_停靠套件.引擎.树 import 停靠窗格标识列表
from ....ui_停靠套件.引擎.规划 import 查找窗格内容标签
from ....ui_基础界面组件.icons import 图标左栏16
from ....ui_基础界面组件.提示泡 import 提示泡
from ..文案 import 中文
from ..停靠文案 import 停靠标签
from ..约定.种子 import 向导种类,页面地址
from ..约定.槽位 import 席名右侧签正文,席名右侧签标题,席名右侧签菜单项

__all__=['右栏席','停靠意图','标签槽','面板铬','侧栏面板','窄视口全屏阈值']

样式路径=os.path.join(os.path.dirname(__file__),'右侧侧栏.module.css')
样式模块='sidebar-right'
窄视口全屏阈值=768


def _窗口(属性):
    '调用方带来的窗口，否则用桥上的窗口'
    if isinstance(属性,dict) and 属性.get('window') is not None:
        return 属性['window']
    return 取握手窗口()


def _订(钩子,回调):
    '选择器钩子上挂着的订阅'
    订=getattr(钩子,'_subscribe',None)
    if callable(订):
        return 订(回调)
    return None


def _有无(节点,名,开):
    '开着就挂上属性，关掉就摘掉'
    if 开:
        节点.setAttribute(名,'')
        return
    节点.removeAttribute(名)


def _找键(条目表,标识):
    '快捷键目录里这一条'
    if not isinstance(条目表,(list,tuple)):
        return None
    for 行 in 条目表:
        if 行.get('id')==标识:
            return 行
    return None


class 停靠意图:
    '停靠套件回调的名字保持英文，里面写的是这一会话的存储动作'

    def __init__(自身,会话标识,动作,打开标签,关闭标签,分栏):
        '记下这一会话'
        自身.会话标识=会话标识
        自身.动作=动作
        自身.打开标签=打开标签
        自身.关闭标签=关闭标签
        自身.分栏=分栏

    def focusTab(自身,标签标识):
        '聚焦这张签'
        自身.动作['聚焦标签'](自身.会话标识,标签标识)

    def focusPane(自身,窗格标识):
        '聚焦这一格'
        自身.动作['聚焦窗格'](自身.会话标识,窗格标识)

    def splitPane(自身,窗格标识):
        '分栏走控制器；没有就直接写存储'
        if 自身.分栏 is not None:
            自身.分栏(窗格标识)
            return
        自身.动作['分窗格'](自身.会话标识,窗格标识)

    def addTab(自身,窗格标识):
        '新标签是向导，只看这一格'
        自身.打开标签(向导种类,{'paneId':窗格标识,'revealIfOpened':False})

    def closeTab(自身,标签标识):
        '关闭走控制器，好让资源先清理'
        if 自身.关闭标签 is not None:
            自身.关闭标签(标签标识)
            return
        自身.动作['关闭标签'](自身.会话标识,标签标识)

    def duplicateTab(自身,标签标识):
        '复制这张签'
        自身.动作['复制标签'](自身.会话标识,标签标识)

    def floatTab(自身,标签标识,矩形=None):
        '浮出'
        自身.动作['浮出标签'](自身.会话标识,标签标识,矩形)

    def unfloatPane(自身,窗格标识):
        '收回浮动窗'
        自身.动作['收回浮窗'](自身.会话标识,窗格标识)

    def placeTab(自身,标签标识,到窗,下标):
        '放到条上的这个位置'
        自身.动作['安置标签'](自身.会话标识,标签标识,到窗,下标)

    def dropTab(自身,标签标识,窗格标识,区):
        '投到这一格的这个区位'
        自身.动作['投放标签'](自身.会话标识,标签标识,窗格标识,区)

    def moveFloat(自身,窗格标识,横,纵):
        '挪动浮动窗'
        自身.动作['移动浮动'](自身.会话标识,窗格标识,横,纵)

    def resizeFloat(自身,窗格标识,矩形):
        '缩放浮动窗'
        自身.动作['缩放浮动'](自身.会话标识,窗格标识,矩形)

    def resizeSplit(自身,分割标识,尺寸表):
        '拖分割条'
        自身.动作['调整分割'](自身.会话标识,分割标识,尺寸表)


class 全屏字形:
    '扩到视口的四个角'

    def __init__(自身,窗口):
        '记下窗口'
        自身.窗口=窗口
        自身.根=None

    def 渲染(自身):
        '画出 svg'
        文档=自身.窗口.document
        图=文档.createElementNS('http://www.w3.org/2000/svg','svg')
        图.setAttribute('width','16')
        图.setAttribute('height','16')
        图.setAttribute('viewBox','0 0 16 16')
        图.setAttribute('fill','none')
        图.setAttribute('aria-hidden','true')
        路=文档.createElementNS('http://www.w3.org/2000/svg','path')
        路.setAttribute('d','M2.33203 10.4054V13.1681C2.33229 13.444 2.55605 13.6681 2.83203 13.6681H5.49512V14.6681H2.83203C2.00376 14.6681 1.33229 13.9963 1.33203 13.1681V10.4054H2.33203ZM14.6689 13.1681C14.6687 13.996 13.9968 14.6676 13.1689 14.6681H10.4951V13.6681H13.1689C13.4445 13.6676 13.6687 13.4437 13.6689 13.1681V10.4054H14.6689V13.1681ZM13.1689 1.33118C13.9969 1.33163 14.6688 2.00315 14.6689 2.83118V5.4054H13.6689V2.83118C13.6688 2.55544 13.4446 2.33162 13.1689 2.33118H10.4951V1.33118H13.1689ZM5.49512 2.33118H2.83203C2.55598 2.33118 2.33218 2.55516 2.33203 2.83118V5.4054H1.33203V2.83118C1.33218 2.00288 2.00369 1.33118 2.83203 1.33118H5.49512V2.33118Z')
        路.setAttribute('fill','currentColor')
        图.appendChild(路)
        自身.根=图
        return 图


class 退出全屏字形:
    '从全屏收回的两角'

    def __init__(自身,窗口):
        '记下窗口'
        自身.窗口=窗口
        自身.根=None

    def 渲染(自身):
        '画出 svg'
        文档=自身.窗口.document
        图=文档.createElementNS('http://www.w3.org/2000/svg','svg')
        图.setAttribute('width','16')
        图.setAttribute('height','16')
        图.setAttribute('viewBox','0 0 16 16')
        图.setAttribute('fill','none')
        图.setAttribute('aria-hidden','true')
        第一=文档.createElementNS('http://www.w3.org/2000/svg','path')
        第一.setAttribute('d','M9 2.5V6C9 6.26522 9.10536 6.51957 9.29289 6.70711C9.48043 6.89464 9.73478 7 10 7H13.5')
        第一.setAttribute('stroke','currentColor')
        第二=文档.createElementNS('http://www.w3.org/2000/svg','path')
        第二.setAttribute('d','M7 13.5V10C7 9.73478 6.89464 9.48043 6.70711 9.29289C6.51957 9.10536 6.26522 9 6 9H2.5')
        第二.setAttribute('stroke','currentColor')
        图.appendChild(第一)
        图.appendChild(第二)
        自身.根=图
        return 图


class 面板铬:
    '条尾的全屏和收起'

    def __init__(自身,窗口,会话标识,全屏,动作,快捷键表,切换全屏):
        '记下这一会话的呈现'
        自身.窗口=窗口
        自身.属性={'window':窗口}
        自身.会话标识=会话标识
        自身.全屏=全屏
        自身.动作=动作
        自身.快捷键表=快捷键表
        自身.切换全屏=切换全屏
        自身.根=None

    def 渲染(自身):
        '两个按钮'
        文档=自身.窗口.document
        注入模块样式文件(文档,'右侧侧栏样式',样式路径,样式模块)
        根=文档.createElement('span')
        下一='push' if 自身.全屏 else 'fullscreen'
        模式文=中文['chrome.exitFullscreen'] if 自身.全屏 else 中文['chrome.toFullscreen']
        模式键=_找键(自身.快捷键表,'pane.fullscreen.toggle')
        切换键=_找键(自身.快捷键表,'sidebar.right.toggle')

        def 造钮(文案,无障碍,快捷,数据名,数据值,点击,图):
            '一个图标按钮，外包提示'
            钮=文档.createElement('button')
            钮.type='button'
            钮.className='iconButton'
            标样式模块(钮,样式模块)
            钮.setAttribute('aria-label',无障碍)
            if 快捷 is not None and 快捷.get('aria'):
                钮.setAttribute('aria-keyshortcuts',快捷['aria'])
            if 数据值 is None:
                钮.setAttribute(数据名,'')
            else:
                钮.setAttribute(数据名,数据值)
            钮.addEventListener('click',lambda 事件: 点击())
            if 图 is not None:
                钮.appendChild(图)
            提示=文案
            if 快捷 is not None and 快捷.get('keys'):
                提示=提示+' '+' '.join(str(键) for 键 in 快捷['keys'])
            泡=提示泡({'window':自身.窗口,'label':提示,'side':'bottom','children':钮})
            return 泡.渲染()

        def 切模式():
            '全屏或退出'
            if callable(自身.切换全屏):
                自身.切换全屏()

        def 收起():
            '展开和收起对调'
            自身.动作['切换展开'](自身.会话标识)

        模式图=退出全屏字形(自身.窗口).渲染() if 自身.全屏 else 全屏字形(自身.窗口).渲染()
        根.appendChild(造钮(模式文,模式文,模式键,'data-sidebar-right-mode',下一,切模式,模式图))
        收起图=图标左栏16({'window':自身.窗口,'className':'collapseGlyph'})
        if 收起图 is not None:
            标样式模块(收起图,样式模块)
        根.appendChild(造钮(中文['chrome.collapse'],中文['chrome.collapseAria'],切换键,'data-sidebar-right-toggle',None,收起,收起图))
        自身.根=根
        return 根


class 标签槽:
    '一张签的正文或标题。没有登记的类型就用后备'

    def __init__(自身,窗口,面板,签,席名,后备):
        '记下这张签'
        自身.窗口=窗口
        自身.属性={'window':窗口}
        自身.面板=面板
        自身.签=签
        自身.席名=席名
        自身.后备=后备
        自身.根=None
        自身.卸保留=None

    def 渲染(自身):
        '外包一层，里面是槽位或后备'
        文档=自身.窗口.document
        注入模块样式文件(文档,'右侧侧栏样式',样式路径,样式模块)
        出现=自身.面板['occurrence'](自身.签)
        用类型=自身.面板['useTabTypes']
        定义=None
        if callable(用类型):
            def 取定义(类型表):
                '种类对上的那个'
                for 项 in 类型表:
                    if 项.get('kind')==自身.签.get('kind'):
                        return 项
                return None
            定义=用类型(取定义)
        保留=自身.席名==席名右侧签正文 and 定义 is not None and 定义.get('keepMounted') is True
        if 保留 and 自身.卸保留 is None and callable(自身.面板.get('retainTab')):
            自身.卸保留=自身.面板['retainTab'](自身.签['id'],出现['signal'])
        elif not 保留 and callable(自身.卸保留):
            自身.卸保留()
            自身.卸保留=None
        钩上下文={
            'tabId':自身.签['id'],
            'shortcuts':自身.面板.get('shortcuts') or (),
            'title':自身.席名==席名右侧签标题,
            'fullscreen':自身.面板.get('fullscreen'),
            'active':自身.面板.get('active'),
            'signal':出现['signal'],
            'actions':出现['tabActions'],
            'useStore':自身.面板.get('useStore'),
            'useTabNavigation':自身.面板.get('useTabNavigation'),
        }
        键=定义['id'] if 定义 is not None and 定义.get('id') else 自身.签.get('kind')
        画槽=自身.面板.get('renderSlot')
        内容=None
        if callable(画槽):
            内容=画槽(自身.席名,{},{'entryKey':键,'fallback':自身.后备,'hookContext':钩上下文})
        标签名='span' if 自身.席名==席名右侧签标题 else 'div'
        类名='tabTitle' if 自身.席名==席名右侧签标题 else 'tabBody'
        根=文档.createElement(标签名)
        根.className=类名
        标样式模块(根,样式模块)
        根.setAttribute('data-sidebar-right-tab',str(自身.签['id']))
        根.setAttribute('data-sidebar-right-occurrence',str(出现['id']))
        if 内容 is None:
            if isinstance(自身.后备,str):
                根.textContent=自身.后备
            elif 自身.后备 is not None and hasattr(自身.后备,'tagName'):
                根.appendChild(自身.后备)
        elif hasattr(内容,'tagName'):
            根.appendChild(内容)
        elif getattr(内容,'根',None) is not None:
            根.appendChild(内容.根)
        自身.根=根
        return 根


class 侧栏面板:
    '面板盒子和里面的停靠面'

    def __init__(自身,窗口,份额):
        '记下这一会话的表面'
        自身.窗口=窗口
        自身.份额=份额
        自身.根=None
        自身.身体=None
        自身.停靠=None

    def 渲染(自身):
        '更新盒子，再重画停靠面'
        文档=自身.窗口.document
        注入模块样式文件(文档,'右侧侧栏样式',样式路径,样式模块)
        表面=自身.份额['surface']
        全屏=自身.份额['fullscreen']
        宽=自身.份额['width']
        展开=表面['layout']['expanded'] is True
        if 自身.根 is None:
            自身.根=文档.createElement('div')
            自身.根.className='panel'
            标样式模块(自身.根,样式模块)
            自身.身体=文档.createElement('div')
            自身.身体.className='panelBody'
            标样式模块(自身.身体,样式模块)
            自身.根.appendChild(自身.身体)
        像素='100vw' if 全屏 else str(宽)+'px'
        自身.根.style.width=像素
        自身.根.style.setProperty('--dsh-sidebar-width',像素)
        自身.根.setAttribute('data-sidebar-right-session',str(自身.份额['sessionId']))
        自身.根.setAttribute('data-sidebar-right-panel','fullscreen' if 全屏 else 'push')
        _有无(自身.根,'data-sidebar-right-open',展开)
        藏起=(not 展开) and len(表面['layout'].get('floats') or [])==0
        if 藏起:
            自身.根.setAttribute('aria-hidden','true')
        else:
            自身.根.removeAttribute('aria-hidden')
        快捷=自身.份额.get('shortcuts') or ()
        意图=停靠意图(
            自身.份额['sessionId'],
            自身.份额['actions'],
            自身.份额['openTab'],
            自身.份额.get('closeTab'),
            自身.份额.get('splitPane'),
        )
        铬=面板铬(自身.窗口,自身.份额['sessionId'],全屏,自身.份额['actions'],快捷,自身.份额.get('toggleFullscreen'))

        def 渲正文(签):
            '正文槽。没有类型就写明还不能看'
            段=文档.createElement('p')
            段.className='unavailable'
            标样式模块(段,样式模块)
            段.setAttribute('data-sidebar-right-unavailable','')
            段.textContent=中文['tab.unavailable']
            return 标签槽(自身.窗口,自身.份额,签,席名右侧签正文,段)

        def 渲标题(签):
            '标题槽。没有类型就用打开时记下的字'
            return 标签槽(自身.窗口,自身.份额,签,席名右侧签标题,签.get('title') or '')

        def 渲菜单(签,解散):
            '菜单尾部的额外项'
            画槽=自身.份额.get('renderSlot')
            if not callable(画槽):
                return None
            return 画槽(席名右侧签菜单项,{'tab':签,'dismiss':解散,'window':自身.窗口})

        def 可加(窗格标识):
            '这一格还没有向导才能再加'
            return 查找窗格内容标签(表面['layout'],窗格标识,页面地址(向导种类),向导种类) is None

        布局=表面['layout']
        能分=可分割(布局) and len(停靠窗格标识列表(布局))<2
        if 自身.停靠 is None:
            自身.停靠=停靠面(
                布局,能分,意图,
                停靠标签(None,_找键(快捷,'pane.split'),_找键(快捷,'page.close')),
                渲正文,渲标题,渲菜单,铬,可加,'horizontal',0.2,False,自身.份额.get('reportRoom'),
            )
            自身.停靠.窗口=自身.窗口
        else:
            自身.停靠.状态=布局
            自身.停靠.可分割=能分
            自身.停靠.意图=意图
            自身.停靠.文案=停靠标签(None,_找键(快捷,'pane.split'),_找键(快捷,'page.close'))
            自身.停靠.渲标签=渲正文
            自身.停靠.渲标签标题=渲标题
            自身.停靠.渲菜单附加=渲菜单
            自身.停靠.铬=铬
            自身.停靠.可加标签=可加
            自身.停靠.投放模式='horizontal'
            自身.停靠.最小份额=0.2
            自身.停靠.房间回调=自身.份额.get('reportRoom')
            自身.停靠.窗口=自身.窗口
        面=自身.停靠.渲染()
        while 自身.身体.firstChild is not None:
            自身.身体.firstChild.remove()
        if 面 is not None:
            自身.身体.appendChild(面)
        return 自身.根


class 右栏席:
    '这一会话的面板。没有表面时先打开一份空的'

    def __init__(自身,属性=None):
        '记下份额并画出'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.面板=None
        自身._退订=[]
        自身._已报隐藏=False
        自身.渲染()
        自身._订阅()

    def __call__(自身,属性=None):
        '再次绘制'
        if 属性 is not None:
            自身.属性=属性
        return 自身.渲染()

    def _订阅(自身):
        '存储、快捷键、类型变了就重画'
        def 变更():
            '还挂着才重画'
            if 自身.根 is not None and getattr(自身.根,'isConnected',True) is False:
                for 退 in 自身._退订:
                    退()
                自身._退订.clear()
                return
            自身.渲染()
        for 名 in ('useStore','useShortcuts','useTabTypes'):
            退=_订(自身.属性.get(名),变更)
            if 退 is not None:
                自身._退订.append(退)

    def 渲染(自身):
        '读表面，汇报呈现，画出或拆掉面板'
        窗口=_窗口(自身.属性)
        会话标识=自身.属性.get('sessionId')
        用存储=自身.属性.get('useStore')
        动作=自身.属性.get('actions') or {}
        表面=None
        if callable(用存储):
            def 取表面(状态):
                '这一会话的表面'
                return 状态['bySession'].get(会话标识)
            表面=用存储(取表面)
        活动=自身.属性.get('active') is True
        if 活动 and 表面 is None and '打开' in 动作:
            动作['打开'](会话标识)
            if callable(用存储):
                表面=用存储(取表面)
        视口=自身.属性.get('viewportWidth') or 0
        自动全屏=视口<窄视口全屏阈值
        能显示=自身.属性.get('canShow')
        全屏=自动全屏 or (表面 is not None and 表面['layout'].get('mode')=='fullscreen')
        显示=活动 and 表面 is not None and 表面['layout']['expanded'] is True
        if 显示 and not 全屏 and 能显示 is False and '设展开' in 动作:
            动作['设展开'](会话标识,False)
            if callable(用存储):
                表面=用存储(取表面)
            全屏=自动全屏 or (表面 is not None and 表面['layout'].get('mode')=='fullscreen')
            显示=活动 and 表面 is not None and 表面['layout']['expanded'] is True
        轨道=显示 and not 自动全屏
        报自动=自身.属性.get('reportAutoFullscreen')
        if callable(报自动):
            报自动(自动全屏)
        同步=自身.属性.get('syncPresentation')
        量房间=自身.属性.get('measureRoom')

        def 报告房间(可放表):
            '把套件量到的半格结果交给服务'
            if not callable(量房间):
                return

            def 能分(窗格标识):
                '没量到的窗当作放得下'
                项=可放表.get(窗格标识) if isinstance(可放表,dict) else None
                if not isinstance(项,dict):
                    return True
                return 项.get('row') is not False

            量房间(能分)

        if 表面 is None:
            if 自身.根 is not None:
                自身.根.remove()
                自身.根=None
            if not 活动 and callable(同步) and not 自身._已报隐藏:
                同步({'shown':False,'track':False,'fullscreen':False})
                自身._已报隐藏=True
            elif 活动 and callable(同步):
                自身._已报隐藏=False
                同步({'shown':False,'track':False,'fullscreen':全屏})
            return 自身
        用快捷=自身.属性.get('useShortcuts')
        快捷=()
        if callable(用快捷):
            def 原样(条目表):
                '整份目录'
                return 条目表
            读到=用快捷(原样)
            if isinstance(读到,(list,tuple)):
                快捷=读到
        份额={
            'sessionId':会话标识,
            'surface':表面,
            'actions':动作,
            'renderSlot':自身.属性.get('renderSlot'),
            'openTab':自身.属性.get('openTab'),
            'closeTab':自身.属性.get('closeTab'),
            'splitPane':自身.属性.get('splitPane'),
            'toggleFullscreen':自身.属性.get('toggleFullscreen'),
            'shortcuts':快捷,
            'useTabTypes':自身.属性.get('useTabTypes'),
            'useTabNavigation':自身.属性.get('useTabNavigation'),
            'useStore':用存储,
            'occurrence':自身.属性.get('occurrence'),
            'fullscreen':全屏,
            'active':活动,
            'retainTab':自身.属性.get('retainTab'),
            'width':自身.属性.get('width'),
            'reportRoom':报告房间,
        }
        if 自身.面板 is None:
            自身.面板=侧栏面板(窗口,份额)
        else:
            自身.面板.份额=份额
        自身.根=自身.面板.渲染()
        父=自身.属性.get('parent')
        if 父 is not None and 自身.根 is not None and getattr(自身.根,'parentNode',None) is None:
            父.appendChild(自身.根)
        if not 活动 and callable(同步) and not 自身._已报隐藏:
            同步({'shown':False,'track':False,'fullscreen':False})
            自身._已报隐藏=True
        elif 活动 and callable(同步):
            自身._已报隐藏=False
            同步({'shown':显示,'track':轨道,'fullscreen':全屏})
        return 自身
