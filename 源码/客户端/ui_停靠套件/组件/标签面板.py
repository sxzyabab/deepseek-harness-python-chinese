from nicegui import ui as 界面
from ..引擎.树 import 取标签#树
from .面板回调 import 分割阻断预算,分割阻断宽度#阻断
from .标签菜单 import 标签菜单#菜单

__all__=['标签面板','芯片导航目标','是否选定键']#仅中文公开名


def 芯片导航目标(键,标签表,标签标识):
    '方向键/Home/End 下一芯片；非导航键返回 None'
    数=len(标签表)#长
    if 数==0:#空
        return None#无
    下标=标签表.index(标签标识)#位
    if 键=='ArrowLeft':#左
        return 标签表[(下标-1+数)%数]#环
    if 键=='ArrowRight':#右
        return 标签表[(下标+1)%数]#环
    if 键=='Home':#首
        return 标签表[0]#首
    if 键=='End':#末
        return 标签表[-1]#末
    return None#非导航


def 是否选定键(键):
    '是否选定当前芯片'
    return 键=='Enter' or 键==' '#选定


def _分割标题(文案,阻断):
    '分割控件提示文'
    if 阻断 is None:#可分
        return 文案['splitPane']#可
    if 阻断==分割阻断预算:#满
        return 文案['splitPaneDisabled']#满
    if 阻断==分割阻断宽度:#窄
        return 文案['splitPaneNarrow']#窄
    return 文案['splitPane']#回退


class 标签面板:
    '窗格条带与正文；持菜单打开态'

    def __init__(自身,状态,窗格,回调):
        '记下布局、窗格节点与面板回调'
        自身.状态=状态#布局
        自身.窗格=窗格#窗格 dict
        自身.回调=回调#回调
        自身._菜单标签=None#打开中的标签

    def 更新(自身,状态,窗格,回调):
        'props 变更'
        自身.状态=状态#态
        自身.窗格=窗格#窗
        自身.回调=回调#回调

    def 激活标签(自身,标签标识):
        '点击或键选定；已是活动则无操作'
        if 自身.状态['activePaneId']==自身.窗格['id'] and 自身.窗格['activeTabId']==标签标识:#已活
            return#无
        自身.回调['onFocusTab'](标签标识)#焦

    def 聚焦窗格体(自身):
        '点空白聚焦窗格；已活动则无'
        if 自身.状态['activePaneId']==自身.窗格['id']:#已
            return#无
        自身.回调['onFocusPane'](自身.窗格['id'])#焦

    def 切换菜单(自身,标签标识):
        '二次按切换菜单'
        if 自身._菜单标签==标签标识:#同则关
            自身._菜单标签=None#关
        else:#开
            自身._菜单标签=标签标识#开

    def 关菜单(自身):
        '解散菜单'
        自身._菜单标签=None#关

    def 渲染(自身):
        '画出标签条与窗格体'
        回调=自身.回调#回调
        窗格=自身.窗格#窗
        状态=自身.状态#态
        活动标识=窗格['activeTabId']#活动
        活动=None if 活动标识 is None else 取标签(状态,活动标识)#记录
        阻断=回调['splitBlock'](窗格['id'])#阻断
        目标=回调['dropTarget']#投放预览
        条带下标=None#插入预览
        区=None#区位预览
        if 目标 is not None and 目标['kind']=='strip' and 目标['paneId']==窗格['id']:#条带
            条带下标=目标['index']#槽
        if 目标 is not None and 目标['kind']=='zone' and 目标['paneId']==窗格['id']:#区位
            区=目标['zone']#区
        with 界面.column().classes('dockkit-pane'):
            with 界面.row().classes('dockkit-strip'):
                for 序号,标签标识 in enumerate(窗格['tabs']):#逐签
                    if 条带下标==序号:#插入符
                        界面.element('span').classes('dockkit-caret')
                    标签=取标签(状态,标签标识)#记录
                    标题=标签['title']#默认
                    if 回调['renderTabTitle'] is not None:#自定义标题
                        产出=回调['renderTabTitle'](标签)
                        if isinstance(产出,str):
                            标题=产出
                        elif hasattr(产出,'渲染'):
                            产出.渲染()
                    def 点标签(签=标签标识):
                        '激活该签'
                        自身.激活标签(签)
                    def 关此签(签=标签标识):
                        '关闭该签'
                        回调['onCloseTab'](签)
                    def 开菜单(签=标签标识):
                        '打开或关闭菜单'
                        自身.切换菜单(签)
                    钮=界面.button(str(标题), on_click=点标签).classes('dockkit-tab')
                    if 标签标识==活动标识:
                        钮.classes(add='selected')
                    界面.button(回调['labels']['closeTab'], on_click=关此签)
                    界面.button(on_click=开菜单).props('icon=more_vert flat round')
                    if 自身._菜单标签==标签标识:#打开
                        def 关此(签=标签标识):
                            '关菜单并关签'
                            自身.关菜单()
                            回调['onCloseTab'](签)
                        def 解散():
                            '仅解散'
                            自身.关菜单()
                        附加=None
                        if 回调['renderTabMenuItems'] is not None:
                            附加=回调['renderTabMenuItems'](标签,解散)
                        标签菜单(回调['labels'],关此,解散,附加).渲染()
                if 条带下标==len(窗格['tabs']):
                    界面.element('span').classes('dockkit-caret')
                if 回调['canAddTab'](窗格['id']):
                    def 加签(窗=窗格['id']):
                        '加标签'
                        回调['onAddTab'](窗)
                    界面.button(回调['labels']['addTab'], on_click=加签)
                if not (回调['hideSplitAtCapacity'] and 阻断==分割阻断预算):
                    def 分割(窗=窗格['id']):
                        '分割窗格'
                        回调['onSplitPane'](窗)
                    分钮=界面.button(_分割标题(回调['labels'],阻断), on_click=分割)
                    if 阻断 is not None:
                        分钮.disable()
                铬=回调['chrome']
                if 窗格['id']==回调['chromePaneId'] and 铬 is not None:
                    if hasattr(铬,'渲染'):
                        铬.渲染()
            if 活动 is None:
                界面.label(回调['labels']['emptyPane'])
            else:
                正文=回调['renderTab'](活动)
                if hasattr(正文,'渲染'):
                    正文.渲染()
                elif isinstance(正文,str) and 正文!='':
                    界面.label(正文)
            if 区 is not None:
                区文=回调['labels']['dropZone']
                if 回调['horizontalDrops'] and 区!='center':
                    界面.label(区文['left']).classes('dock-hint' if 区!='left' else 'dock-hint active')
                    界面.label(区文['right']).classes('dock-hint' if 区!='right' else 'dock-hint active')
                elif 区 in 区文:
                    界面.label(区文[区]).classes('dock-hint active')
