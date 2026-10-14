from nicegui import ui as 界面
from ...异常 import 异常原文
from ....ui_停靠套件.引擎 import 查找窗格内容标签,可分割,停靠窗格标识列表#树
from ....ui_停靠套件.组件.停靠面 import 停靠面#停靠表面
from ....ui_停靠套件.组件.浮动层 import 浮动层#浮窗
from ..约定.种子 import 向导种类,页面地址#向导
from ..约定.槽位 import 席名右侧签正文,席名右侧签标题,席名右侧签菜单项#席名
from ..停靠文案 import 停靠标签#文案投影

__all__=['右栏席','意图面','样式表','窄视口全屏阈值']#仅中文公开名

窄视口全屏阈值=768#低于此宽派生全屏

样式表='''#对齐 SidebarRight.module.css
.panel{position:absolute;top:0;right:0;bottom:0;z-index:10;display:flex;flex-direction:column;min-width:0}
.panelBody{display:flex;flex:1 1 auto;min-height:0;min-width:0;background:var(--dsw-alias-bg-base);border-left:0.5px solid var(--dsw-alias-border-l1);transform:translateX(100%);visibility:hidden;transition:transform var(--ds-transition-duration-slow) var(--ds-ease-in-out),visibility 0s linear var(--ds-transition-duration-slow)}
.panel[data-sidebar-right-open] .panelBody{transform:none;visibility:visible;transition:transform var(--ds-transition-duration-slow) var(--ds-ease-in-out)}
.panel[data-sidebar-right-panel='fullscreen']{position:fixed;inset:0;z-index:40}
.panel[data-sidebar-right-panel='fullscreen'] .panelBody{border:none}
@media (prefers-reduced-motion:reduce){.panelBody,.panel[data-sidebar-right-open] .panelBody{transition:none}}
.iconButton{display:inline-flex;flex:none;align-items:center;justify-content:center;width:28px;height:28px;padding:6px;color:var(--dsw-alias-label-secondary);line-height:1;background:transparent;border:none;border-radius:var(--dsw-radius-sm);cursor:pointer}
button.q-btn.iconButton{width:28px;height:28px;min-height:28px;padding:6px;color:var(--dsw-alias-label-secondary) !important;background:transparent !important;box-shadow:none !important}
.iconButton:hover,button.q-btn.iconButton:hover{background:var(--dsw-alias-interactive-bg-hover) !important}
.iconButton svg{width:15px;height:15px}
.collapseGlyph{transform:scaleX(-1)}
.tabTitle{display:contents}
.tabBody{display:flex;flex-direction:column;height:100%;min-height:0;min-width:0;overflow:hidden}
.unavailable{margin:0;padding:12px;color:var(--dsw-alias-label-tertiary);font-size:var(--dsh-content-font-size-secondary, 13px)}
.floatHost{position:fixed;inset:0;z-index:60;pointer-events:none}
'''#样式表结束

界面.add_css(样式表,shared=True)

全屏标记='<svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M2.33203 10.4054V13.1681C2.33229 13.444 2.55605 13.6681 2.83203 13.6681H5.49512V14.6681H2.83203C2.00376 14.6681 1.33229 13.9963 1.33203 13.1681V10.4054H2.33203ZM14.6689 13.1681C14.6687 13.996 13.9968 14.6676 13.1689 14.6681H10.4951V13.6681H13.1689C13.4445 13.6676 13.6687 13.4437 13.6689 13.1681V10.4054H14.6689V13.1681ZM13.1689 1.33118C13.9969 1.33163 14.6688 2.00315 14.6689 2.83118V5.4054H13.6689V2.83118C13.6688 2.55544 13.4446 2.33162 13.1689 2.33118H10.4951V1.33118H13.1689ZM5.49512 2.33118H2.83203C2.55598 2.33118 2.33218 2.55516 2.33203 2.83118V5.4054H1.33203V2.83118C1.33218 2.00288 2.00369 1.33118 2.83203 1.33118H5.49512V2.33118Z" fill="currentColor"/></svg>'#进全屏
退出全屏标记='<svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M9 2.5V6C9 6.26522 9.10536 6.51957 9.29289 6.70711C9.48043 6.89464 9.73478 7 10 7H13.5" stroke="currentColor" stroke-width="1"/><path d="M7 13.5V10C7 9.73478 6.89464 9.48043 6.70711 9.29289C6.51957 9.10536 6.26522 9 6 9H2.5" stroke="currentColor" stroke-width="1"/></svg>'#退全屏
收起标记='<svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M13.5 1.5H2.5C1.94772 1.5 1.5 1.94772 1.5 2.5V13.5C1.5 14.0523 1.94772 14.5 2.5 14.5H13.5C14.0523 14.5 14.5 14.0523 14.5 13.5V2.5C14.5 1.94772 14.0523 1.5 13.5 1.5Z" stroke="currentColor" stroke-width="1"/><path d="M5.5 1.5V14.5" stroke="currentColor" stroke-width="1"/></svg>'#收起，镜像后指向右


class 意图面:#停靠手势
    '方法名跟停靠套件的调用一致，把一次手势写成该会话的存储动作'

    def __init__(自身,会话标识,动作,开标签,关标签=None,分窗=None):
        '记下会话、动作和可选的关签、分栏'
        自身.会话标识=会话标识#会话
        自身.动作=动作#存储动作
        自身.开标签=开标签#开向导
        自身.关标签=关标签#经资源清理关签
        自身.分窗=分窗#经控制器分栏

    def focusTab(自身,签):
        '聚焦标签'
        自身.动作['focusTab'](自身.会话标识,签)#焦

    def focusPane(自身,窗):
        '聚焦窗格'
        自身.动作['focusPane'](自身.会话标识,窗)#焦

    def splitPane(自身,窗):
        '分栏'
        if callable(自身.分窗):#控制器
            自身.分窗(窗)#分
            return#止
        自身.动作['splitPane'](自身.会话标识,窗)#分

    def addTab(自身,窗):
        '在该窗开向导'
        自身.开标签(向导种类,{'paneId':窗,'revealIfOpened':False})

    def closeTab(自身,签):
        '关标签'
        if callable(自身.关标签):#经清理
            自身.关标签(签)#关
            return#止
        自身.动作['closeTab'](自身.会话标识,签)#关

    def duplicateTab(自身,签):
        '复制标签'
        自身.动作['duplicateTab'](自身.会话标识,签)#复制

    def floatTab(自身,签,矩=None):
        '浮出'
        自身.动作['floatTab'](自身.会话标识,签,矩)#浮

    def unfloatPane(自身,窗):
        '收回浮窗'
        自身.动作['unfloatPane'](自身.会话标识,窗)#收

    def placeTab(自身,签,到,下):
        '放到条带'
        自身.动作['placeTab'](自身.会话标识,签,到,下)#放

    def dropTab(自身,签,窗,区):
        '投到区位'
        自身.动作['dropTab'](自身.会话标识,签,窗,区)#投

    def moveFloat(自身,窗,横,纵):
        '移动浮窗'
        自身.动作['moveFloat'](自身.会话标识,窗,横,纵)#移

    def resizeFloat(自身,窗,矩):
        '缩放浮窗'
        自身.动作['resizeFloat'](自身.会话标识,窗,矩)#缩

    def resizeSplit(自身,分,份):
        '调整分割'
        自身.动作['resizeSplit'](自身.会话标识,分,份)#调


class 面板铬:#条带末端两个钮
    '父组件构造后调用 渲染，构造本身不画'

    def __init__(自身,席):
        '记下右栏席'
        自身.席=席#席

    def 渲染(自身):
        '全屏切换和收起'
        翻译=自身.席.属性['t']#文案
        全=自身.席._全屏()#全屏
        退文=翻译('chrome.exitFullscreen') if 全 else 翻译('chrome.toFullscreen')#模式文
        收文=翻译('chrome.collapse')#收起提示
        收名=翻译('chrome.collapseAria')#收起名
        模式=界面.button(on_click=自身.席.切模式).props('flat dense round aria-label="'+退文+'" title="'+退文+'"').classes('iconButton')#模式
        模式.props('data-sidebar-right-mode='+('push' if 全 else 'fullscreen'))#下一模式
        with 模式:#字形
            界面.html(退出全屏标记 if 全 else 全屏标记,sanitize=False)#图标
        收起=界面.button(on_click=自身.席.收起).props('flat dense round aria-label="'+收名+'" title="'+收文+'"').classes('iconButton')#收起
        收起.props('data-sidebar-right-toggle')#标记
        with 收起:#镜像面板
            界面.html(收起标记,sanitize=False).classes('collapseGlyph')#图标


class 签标题:#键控标题席
    '父组件调用 渲染 时才画；已登记的标题类在自己的构造里画出'

    def __init__(自身,席,签):
        '记下席与标签记录'
        自身.席=席#席
        自身.签=签#记录

    def 渲染(自身):
        '有登记则由标题组件画出；条带上的按钮本身带着打开时的标题'
        标记=object()#回退身份
        盒=界面.element('span').classes('tabTitle')#标题位
        盒.props('data-sidebar-right-tab="'+str(自身.签['id']).replace('"','')+'"')#标记
        with 盒:#内容
            自身.席._调度席(自身.签,席名右侧签标题,标记)#有登记的标题在构造里画出；条带按钮自带记录标题


class 签正文:#键控正文席
    '父组件调用 渲染 时才画'

    def __init__(自身,席,签):
        '记下席与标签记录'
        自身.席=席#席
        自身.签=签#记录

    def 渲染(自身):
        '有登记则由正文组件画出；否则说明这类内容还不能看'
        标记=object()#回退身份
        盒=界面.element('div').classes('tabBody')#正文位
        盒.props('data-sidebar-right-tab="'+str(自身.签['id']).replace('"','')+'"')#标记
        with 盒:#内容
            结果=自身.席._调度席(自身.签,席名右侧签正文,标记)#席
            if 自身.席._是回退(结果,标记):#没有登记
                界面.label(自身.席.属性['t']('tab.unavailable')).classes('unavailable')#说明


class 菜单附加:#标签菜单里的登记项
    '父组件在菜单列里调用 渲染，登记项在那时画出'

    def __init__(自身,席,签,关):
        '记下席、标签和关闭菜单'
        自身.席=席#席
        自身.签=签#记录
        自身.关=关#解散

    def 渲染(自身):
        '把菜单项席画进当前菜单'
        画=自身.席.属性['renderSlot'] if 'renderSlot' in 自身.席.属性 else None#子槽
        if not callable(画):#没装
            return#无附加
        try:#一项失败不拆掉关标签
            with 界面.element('div').style('display:contents'):#附加项跟关标签项排在一起
                画(席名右侧签菜单项,{'tab':自身.签,'dismiss':自身.关})#列表席
        except Exception as 错误:
            界面.label(异常原文(错误))


def _窗向导(布局,窗格标识):
    '窗内向导'
    return 查找窗格内容标签(布局,窗格标识,页面地址(向导种类),向导种类)#签


class 右栏席:#rightbar 席视图模型
    '物化表面、同步帧呈现、绑定服务面、产出面板结构'

    def __init__(自身,属性):
        '记下 props。槽位只调用构造，键齐了就画。'
        自身.属性=属性 if 属性 is not None else {}#props
        自身.房间={}#paneId → halvesFit
        自身._服务释放=None#绑定释放
        自身._已报呈现=None#上次呈现
        if 'sessionId' in 自身.属性 and 'useStore' in 自身.属性 and 'actions' in 自身.属性:#槽位份额齐了
            自身.更新(自身.属性)#物化表面
        if 'sessionId' in 自身.属性 and 'useStore' in 自身.属性 and 'actions' in 自身.属性 and 't' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新 props 并重绑'
        自身.属性=属性 if 属性 is not None else {}#最新
        自身._确保表面()#物化
        自身._同步可展示()#空间不足则收
        自身._同步呈现()#报帧
        自身._绑定服务()#服务

    def 卸载(自身):
        '还轨道、释绑定'
        同步=自身.属性['syncPresentation'] if 'syncPresentation' in 自身.属性 else None#同步
        if 同步 is not None:
            同步({'shown':False,'track':False,'fullscreen':False})#还
        if 自身._服务释放 is not None:
            自身._服务释放()#释
            自身._服务释放=None

    def _读表面表(自身):
        'bySession'
        用=自身.属性['useStore']#选择
        return 用(lambda 态:态['bySession'])#表

    def _读表面(自身):
        '本会话表面'
        表=自身._读表面表()#表
        会话=自身.属性['sessionId']#会话
        return 表[会话] if 会话 in 表 else None#表面

    def _确保表面(自身):
        '无表面则 open'
        if 自身._读表面() is None:#无
            自身.属性['actions']['open'](自身.属性['sessionId'])#物化

    def _自动全屏(自身):
        '视口派生'
        宽=自身.属性['viewportWidth'] if 'viewportWidth' in 自身.属性 else 1024#宽
        return 宽<窄视口全屏阈值#窄

    def _全屏(自身):
        '自动或手动全屏'
        表面=自身._读表面()#表面
        if 自身._自动全屏():#窄
            return True#全屏
        if 表面 is None:#无
            return False#否
        return 表面['layout']['mode']=='fullscreen'#模式

    def _已展示(自身):
        '面板是否画出'
        表面=自身._读表面()#表面
        return 表面 is not None and 表面['layout']['expanded'] is True#展

    def _同步可展示(自身):
        '普通呈现且不可展示则收起'
        可=自身.属性['canShow'] if 'canShow' in 自身.属性 else True#可
        if 自身._已展示() and not 自身._全屏() and not 可:#收
            自身.属性['actions']['setExpanded'](自身.属性['sessionId'],False)#收

    def _同步呈现(自身):
        '报告帧'
        同步=自身.属性['syncPresentation'] if 'syncPresentation' in 自身.属性 else None#同步
        if 同步 is None:#无
            return#止
        展=自身._已展示()#展
        全=自身._全屏()#全
        轨=展 and not 自身._自动全屏()#轨
        呈现={'shown':展,'track':轨,'fullscreen':全}#呈现
        if 自身._已报呈现==呈现:#未变
            return#止
        自身._已报呈现=呈现#记
        同步(呈现)#报

    def _绑定服务(自身):
        '发布绑定'
        绑函=自身.属性['bindService'] if 'bindService' in 自身.属性 else None#绑
        if 绑函 is None:#无
            return#止
        if 自身._服务释放 is not None:#先释旧
            自身._服务释放()#释
        房间=自身.房间#闭包

        def 可分(窗):
            '房间规则'
            读=房间[窗] if 窗 in 房间 else None#读
            if 读 is None:#未测
                return True#默认可
            return 读.get('row') is not False#行向可

        自身._服务释放=绑函({#绑定
            'sessionId':自身.属性['sessionId'],
            'actions':自身.属性['actions'],
            'surfaces':自身._读表面表(),
            'canSplitPane':可分,
        })#绑定结束

    def 报房间(自身,适合表):
        '停靠套件房间读数'
        自身.房间=dict(适合表) if 适合表 is not None else {}#写

    def 切模式(自身):
        '全屏⟷推挤；自动全屏下退出则收起'
        会话=自身.属性['sessionId']#会话
        动作=自身.属性['actions']#动作
        全=自身._全屏()#全
        次='push' if 全 else 'fullscreen'#次
        if 全 and 自身._自动全屏():#窄退出
            动作['setExpanded'](会话,False)#收
        动作['setMode'](会话,次)#模式

    def 收起(自身):
        '切换展开'
        自身.属性['actions']['toggleExpanded'](自身.属性['sessionId'])#切

    def 调度正文(自身,签):
        '键控正文；停靠面再调用 渲染'
        return 签正文(自身,签)#正文

    def 调度标题(自身,签):
        '键控标题；停靠面再调用 渲染'
        return 签标题(自身,签)#标题

    def 调度菜单(自身,签,关):
        '菜单附加项；菜单列里再调用 渲染'
        return 菜单附加(自身,签,关)#附加

    def _是回退(自身,结果,标记):
        '槽出口没有当选'
        if isinstance(结果,dict) and 结果.get('type')=='slot-outlet':#出口
            return 结果.get('content') is 标记#回退
        return 结果 is 标记#原样

    def _调度席(自身,签,席名,回退):
        '带钩上下文的席调度；失败时把回退交还给调用方去画'
        属性=自身.属性#props
        画=属性['renderSlot'] if 'renderSlot' in 属性 else None#子槽
        if not callable(画):#没装
            return 回退#回退
        try:#出现次或类型钩还没就绪
            出现=属性['occurrence'](签)#出现次
            用类型=属性['useTabTypes'] if 'useTabTypes' in 属性 else None#类型钩
            定义=None#定义
            if callable(用类型):
                定义=用类型(lambda 表:next((项 for 项 in 表 if 项['kind']==签['kind']),None))#定义
            用导航=属性['useTabNavigation'] if 'useTabNavigation' in 属性 else None#导航钩
            钩上下={#钩上下文
                'tabId':签['id'],
                'title':席名==席名右侧签标题,
                'fullscreen':自身._全屏(),
                'active':属性['active'] if 'active' in 属性 else True,
                'signal':出现['signal'],
                'actions':出现['tabActions'],
                'useStore':属性['useStore'],
                'useTabNavigation':用导航,
            }#上下文
            return 画(席名,{},{#选项
                'entryKey':定义['id'] if isinstance(定义,dict) and 'id' in 定义 else 签['kind'],
                'fallback':回退,
                'hookContext':钩上下,
            })#结果
        except Exception as 错误:
            界面.label(异常原文(错误))
            return 回退#回退

    def 渲染(自身):
        '画出停靠面板和浮窗；收起时面板仍在，只是滑出右缘'
        属性=自身.属性#props
        if 'sessionId' not in 属性 or 'useStore' not in 属性 or 'actions' not in 属性 or 't' not in 属性:#份额未齐
            return#不画
        try:#表面还读不到
            表面=自身._读表面()#表面
        except Exception as 错误:
            界面.label(异常原文(错误))
            return#不画
        if 表面 is None:#尚未物化
            return
        布局=表面['layout']#布局
        全=自身._全屏()#全屏
        展=布局['expanded'] is True#展开
        宽=属性['width'] if 'width' in 属性 and 属性['width'] is not None else 360#宽
        if 全:#铺满视口
            像素='100vw'#全屏
        elif isinstance(宽,(int,float)):#数字
            像素=str(宽)+'px'#像素
        else:#已是长度
            像素=str(宽)#原样
        会话=str(属性['sessionId']).replace('"','')#属性值
        面板=界面.element('div').classes('panel').style('width:'+像素+';--dsh-sidebar-width:'+像素)#面板
        面板.props('data-sidebar-right-session="'+会话+'" data-sidebar-right-panel="'+('fullscreen' if 全 else 'push')+'"')#模式
        if 展:#展开
            面板.props('data-sidebar-right-open')#滑入
        浮=布局['floats'] if 'floats' in 布局 and 布局['floats'] is not None else ()#浮窗
        if not 展 and len(浮)==0:#收起且无浮窗
            面板.props('aria-hidden=true')#不可达
        开=属性['openTab'] if 'openTab' in 属性 and callable(属性['openTab']) else (lambda *_参数:None)#开标签
        关=属性['closeTab'] if 'closeTab' in 属性 and callable(属性['closeTab']) else None#关标签
        分=属性['splitPane'] if 'splitPane' in 属性 and callable(属性['splitPane']) else None#分栏
        意图=意图面(属性['sessionId'],属性['actions'],开,关,分)#手势
        文案=停靠标签(属性['t'])#停靠文案
        with 面板:#面板内
            with 界面.element('div').classes('panelBody'):#停靠树
                停靠面(#表面
                    布局,
                    可分割(布局) and len(停靠窗格标识列表(布局))<2,
                    意图,
                    文案,
                    自身.调度正文,
                    渲标签标题=自身.调度标题,
                    渲菜单附加=自身.调度菜单,
                    铬=面板铬(自身),
                    可加标签=lambda 窗:_窗向导(布局,窗) is None,
                    投放模式='horizontal',
                    最小份额=0.2,
                    满员藏分割=True,
                    房间回调=自身.报房间,
                ).渲染()#画出停靠树
            if len(浮)>0:
                浮动层(布局,意图,文案,自身.调度正文,自身.调度标题).渲染()#画出浮窗
