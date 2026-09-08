"""右栏席：帧右列面板与浮层意图面。

对齐上游 `ui-sidebar-right/src/client/shell/SidebarRight.tsx`。公开面仅中文名。
无 React：视图模型持呈现同步、服务绑定与停靠意图；正文经键控席调度。
停靠表面组件（DockSurface/FloatLayer）由宿主在有套件时挂载；本模块产出意图与结构树。
"""
from ....ui_停靠套件.引擎 import 查找窗格内容标签,可分割,停靠窗格标识列表#树
from ..约定.种子 import 向导种类,页面地址#向导
from ..停靠文案 import 停靠标签#文案投影

__all__=['右栏席','意图面','样式表','窄视口全屏阈值']#仅中文公开名

窄视口全屏阈值=768#低于此宽派生全屏

样式表='''#对齐 SidebarRight.module.css
.panel{position:absolute;top:0;right:0;bottom:0;z-index:10;display:flex;flex-direction:column;min-width:0;background:var(--dsw-alias-bg-base);border-left:0.5px solid var(--dsw-alias-border-l1);transform:translateX(100%);visibility:hidden;transition:transform var(--ds-transition-duration-slow) var(--ds-ease-in-out),visibility 0s linear var(--ds-transition-duration-slow)}
.panel[data-sidebar-right-open]{transform:none;visibility:visible;transition:transform var(--ds-transition-duration-slow) var(--ds-ease-in-out)}
.panel[data-sidebar-right-panel='fullscreen']{position:fixed;inset:0;z-index:40;border:none}
@media (prefers-reduced-motion:reduce){.panel,.panel[data-sidebar-right-open]{transition:none}}
.iconButton{display:flex;flex:none;align-items:center;justify-content:center;width:24px;height:24px;padding:0;color:var(--dsw-alias-label-secondary);font-size:14px;line-height:1;background:transparent;border:none;border-radius:4px;cursor:pointer}
.iconButton:hover{color:var(--dsw-alias-label-primary);background:var(--dsw-alias-interactive-bg-hover)}
.panelBody{display:flex;flex:1 1 auto;min-height:0}
.unavailable{margin:0;color:var(--dsw-alias-label-tertiary);font-size:var(--dsh-content-font-size-secondary, 13px)}
.floatHost{position:fixed;inset:0;z-index:60;pointer-events:none}
'''#样式表结束


def 意图面(会话标识,动作,开标签):
    """停靠手势 → 存储动作。"""
    return {#意图
        'focusTab':lambda 签:动作['focusTab'](会话标识,签),
        'focusPane':lambda 窗:动作['focusPane'](会话标识,窗),
        'splitPane':lambda 窗:动作['splitPane'](会话标识,窗),
        'addTab':lambda 窗:开标签(向导种类,{'paneId':窗,'revealIfOpened':False}),
        'closeTab':lambda 签:动作['closeTab'](会话标识,签),
        'duplicateTab':lambda 签:动作['duplicateTab'](会话标识,签),
        'floatTab':lambda 签,矩=None:动作['floatTab'](会话标识,签,矩),
        'unfloatPane':lambda 窗:动作['unfloatPane'](会话标识,窗),
        'placeTab':lambda 签,到,下:动作['placeTab'](会话标识,签,到,下),
        'dropTab':lambda 签,窗,区:动作['dropTab'](会话标识,签,窗,区),
        'moveFloat':lambda 窗,横,纵:动作['moveFloat'](会话标识,窗,横,纵),
        'resizeFloat':lambda 窗,矩:动作['resizeFloat'](会话标识,窗,矩),
        'resizeSplit':lambda 分,份:动作['resizeSplit'](会话标识,分,份),
    }#意图结束


def _窗向导(布局,窗格标识):
    """窗内向导。"""
    return 查找窗格内容标签(布局,窗格标识,页面地址(向导种类),向导种类)#签


class 右栏席:#rightbar 席视图模型
    """物化表面、同步帧呈现、绑定服务面、产出面板结构。"""

    def __init__(自身,属性):
        """记下 props 与房间读数。"""
        自身.属性=属性 if 属性 is not None else {}#props
        自身.房间={}#paneId → halvesFit
        自身._服务释放=None#绑定释放
        自身._已报呈现=None#上次呈现

    def 更新(自身,属性):
        """刷新 props 并重绑。"""
        自身.属性=属性 if 属性 is not None else {}#最新
        自身._确保表面()#物化
        自身._同步可展示()#空间不足则收
        自身._同步呈现()#报帧
        自身._绑定服务()#服务

    def 卸载(自身):
        """还轨道、释绑定。"""
        同步=自身.属性['syncPresentation'] if 'syncPresentation' in 自身.属性 else None#同步
        if 同步 is not None:#有
            同步({'shown':False,'track':False,'fullscreen':False})#还
        if 自身._服务释放 is not None:#有绑
            自身._服务释放()#释
            自身._服务释放=None#清

    def _读表面表(自身):
        """bySession。"""
        用=自身.属性['useStore']#选择
        return 用(lambda 态:态['bySession'])#表

    def _读表面(自身):
        """本会话表面。"""
        表=自身._读表面表()#表
        会话=自身.属性['sessionId']#会话
        return 表[会话] if 会话 in 表 else None#表面

    def _确保表面(自身):
        """无表面则 open。"""
        if 自身._读表面() is None:#无
            自身.属性['actions']['open'](自身.属性['sessionId'])#物化

    def _自动全屏(自身):
        """视口派生。"""
        宽=自身.属性['viewportWidth'] if 'viewportWidth' in 自身.属性 else 1024#宽
        return 宽<窄视口全屏阈值#窄

    def _全屏(自身):
        """自动或手动全屏。"""
        表面=自身._读表面()#表面
        if 自身._自动全屏():#窄
            return True#全屏
        if 表面 is None:#无
            return False#否
        return 表面['layout']['mode']=='fullscreen'#模式

    def _已展示(自身):
        """面板是否画出。"""
        表面=自身._读表面()#表面
        return 表面 is not None and 表面['layout']['expanded'] is True#展

    def _同步可展示(自身):
        """普通呈现且不可展示则收起。"""
        可=自身.属性['canShow'] if 'canShow' in 自身.属性 else True#可
        if 自身._已展示() and not 自身._全屏() and not 可:#收
            自身.属性['actions']['setExpanded'](自身.属性['sessionId'],False)#收

    def _同步呈现(自身):
        """报告帧。"""
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
        """发布绑定。"""
        绑函=自身.属性['bindService'] if 'bindService' in 自身.属性 else None#绑
        if 绑函 is None:#无
            return#止
        if 自身._服务释放 is not None:#先释旧
            自身._服务释放()#释
        房间=自身.房间#闭包

        def 可分(窗):
            """房间规则。"""
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
        """停靠套件房间读数。"""
        自身.房间=dict(适合表) if 适合表 is not None else {}#写

    def 切模式(自身):
        """全屏⟷推挤；自动全屏下退出则收起。"""
        会话=自身.属性['sessionId']#会话
        动作=自身.属性['actions']#动作
        全=自身._全屏()#全
        次='push' if 全 else 'fullscreen'#次
        if 全 and 自身._自动全屏():#窄退出
            动作['setExpanded'](会话,False)#收
        动作['setMode'](会话,次)#模式

    def 收起(自身):
        """切换展开。"""
        自身.属性['actions']['toggleExpanded'](自身.属性['sessionId'])#切

    def 调度正文(自身,签):
        """键控正文席。"""
        return 自身._调度席(签,'sidebar.right.pane.tab',{#回退
            'type':'p',
            'className':'unavailable',
            'props':{'data-sidebar-right-unavailable':True},
            'text':自身.属性['t']('tab.unavailable'),
        })#调度

    def 调度标题(自身,签):
        """键控标题席。"""
        return 自身._调度席(签,'sidebar.right.pane.tab.title',签['title'])#调度

    def _调度席(自身,签,席名,回退):
        """带钩上下文的席调度。"""
        属性=自身.属性#props
        出现=属性['occurrence'](签)#出现次
        用类型=属性['useTabTypes']#类型钩
        定义=用类型(lambda 表:next((项 for 项 in 表 if 项['kind']==签['kind']),None))#定义
        钩上下={#钩上下文
            'tabId':签['id'],
            'title':席名=='sidebar.right.pane.tab.title',
            'fullscreen':自身._全屏(),
            'signal':出现['signal'],
            'actions':出现['tabActions'],
            'useStore':属性['useStore'],
            'useTabNavigation':属性['useTabNavigation'],
        }#上下文
        return 属性['renderSlot'](席名,{},{#选项
            'entryKey':定义['id'] if 定义 is not None else 签['kind'],
            'fallback':回退,
            'hookContext':钩上下,
        })#结果

    def 面板铬(自身):
        """顶右条带两端控件。"""
        翻译=自身.属性['t']#文案
        全=自身._全屏()#全
        退文=翻译('chrome.exitFullscreen') if 全 else 翻译('chrome.toFullscreen')#模式文
        收文=翻译('chrome.collapse')#收
        return [#两钮
            {'type':'button','className':'iconButton','props':{'aria-label':退文,'title':退文,'data-sidebar-right-mode':('push' if 全 else 'fullscreen')},'onClick':自身.切模式},
            {'type':'button','className':'iconButton','props':{'aria-label':收文,'title':收文,'data-sidebar-right-toggle':True},'onClick':自身.收起},
        ]#铬

    def 停靠属性(自身):
        """交给停靠表面的属性包。"""
        表面=自身._读表面()#表面
        if 表面 is None:#无
            return None#无
        会话=自身.属性['sessionId']#会话
        动作=自身.属性['actions']#动作
        开=自身.属性['openTab']#开标签
        布局=表面['layout']#布局
        return {#停靠属性
            'state':布局,
            'canSplit':可分割(布局) and len(停靠窗格标识列表(布局))<2,
            'hideSplitAtCapacity':True,
            'dropZones':'horizontal',
            'minPaneFraction':0.2,
            'canAddTab':lambda 窗:_窗向导(布局,窗) is None,
            'intents':意图面(会话,动作,开),
            'labels':停靠标签(自身.属性['t']),
            'renderTab':自身.调度正文,
            'renderTabTitle':自身.调度标题,
            'renderTabMenuItems':lambda 签,关:自身.属性['renderSlot']('sidebar.right.tab.menu.item',{'tab':签,'dismiss':关}),
            'chrome':自身.面板铬(),
            'onRoom':自身.报房间,
        }#属性结束

    def 渲染(自身):
        """面板+浮层宿主结构树。"""
        表面=自身._读表面()#表面
        if 表面 is None:#尚未
            return None#空
        宽=自身.属性['width'] if 'width' in 自身.属性 else 0#宽
        全=自身._全屏()#全
        展=表面['layout']['expanded']#展
        停靠=自身.停靠属性()#停靠
        面板={#面板
            'type':'div',
            'className':'panel',
            'props':{#属性
                'style':{'width':'100%' if 全 else 宽},
                'data-sidebar-right-panel':'fullscreen' if 全 else 'push',
                'data-sidebar-right-open':True if 展 else None,
                'aria-hidden':None if 展 else True,
            },
            'children':[{'type':'div','className':'panelBody','props':{'dock':停靠}}],
        }#面板结束
        子=[面板]#子
        if len(表面['layout']['floats'])>0:#有浮
            子.append({#浮宿主
                'type':'div',
                'className':'floatHost',
                'props':{'data-sidebar-right-float-host':True,'dockFloat':停靠},
            })#浮
        return {'type':'fragment','children':子}#片断
