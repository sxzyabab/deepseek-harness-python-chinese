"""一窗格：标签条、分割控件与正文的视图模型。

对齐上游 `ui-dockkit/src/components/TabPanel.tsx`。公开面仅中文名。
手势经面板回调离开；正文由 renderTab 供给。
"""
from ..引擎.树 import 取标签#树
from .面板回调 import 分割阻断预算,分割阻断宽度#阻断
from .标签菜单 import 标签菜单#菜单

__all__=['标签面板','芯片导航目标','是否选定键']#仅中文公开名


def 芯片导航目标(键,标签表,标签标识):
    """方向键/Home/End 下一芯片；非导航键返回 None。"""
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
    """是否选定当前芯片。"""
    return 键=='Enter' or 键==' '#选定


def _分割标题(文案,阻断):
    """分割控件提示文。"""
    if 阻断 is None:#可分
        return 文案['splitPane']#可
    if 阻断==分割阻断预算:#满
        return 文案['splitPaneDisabled']#满
    if 阻断==分割阻断宽度:#窄
        return 文案['splitPaneNarrow']#窄
    return 文案['splitPane']#回退


class 标签面板:
    """窗格条带与正文；持菜单打开态。"""

    def __init__(自身,状态,窗格,回调):
        """记下布局、窗格节点与面板回调。"""
        自身.状态=状态#布局
        自身.窗格=窗格#窗格 dict
        自身.回调=回调#回调
        自身._菜单标签=None#打开中的标签

    def 更新(自身,状态,窗格,回调):
        """props 变更。"""
        自身.状态=状态#态
        自身.窗格=窗格#窗
        自身.回调=回调#回调

    def 激活标签(自身,标签标识):
        """点击或键选定；已是活动则无操作。"""
        if 自身.状态['activePaneId']==自身.窗格['id'] and 自身.窗格['activeTabId']==标签标识:#已活
            return#无
        自身.回调['onFocusTab'](标签标识)#焦

    def 聚焦窗格体(自身):
        """点空白聚焦窗格；已活动则无。"""
        if 自身.状态['activePaneId']==自身.窗格['id']:#已
            return#无
        自身.回调['onFocusPane'](自身.窗格['id'])#焦

    def 切换菜单(自身,标签标识):
        """二次按切换菜单。"""
        if 自身._菜单标签==标签标识:#同则关
            自身._菜单标签=None#关
        else:#开
            自身._菜单标签=标签标识#开

    def 关菜单(自身):
        """解散菜单。"""
        自身._菜单标签=None#关

    def 渲染(自身):
        """结构树。"""
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
        芯片=[]#条带子
        for 序号,标签标识 in enumerate(窗格['tabs']):#逐签
            if 条带下标==序号:#插入符
                芯片.append({'type':'caret','data':'dockkit-caret','index':序号})#符
            标签=取标签(状态,标签标识)#记录
            选中=标签标识==活动标识#选
            标题=标签['title']#默认
            if 回调['renderTabTitle'] is not None:#自定义标题
                标题=回调['renderTabTitle'](标签)#渲
            菜单树=None#菜单
            if 自身._菜单标签==标签标识:#打开
                def _关此(签=标签标识):
                    """关菜单并关签。"""
                    自身.关菜单()#关菜
                    回调['onCloseTab'](签)#关签
                def _解散():
                    """仅解散。"""
                    自身.关菜单()#关
                附加=None#附加
                if 回调['renderTabMenuItems'] is not None:#有
                    附加=回调['renderTabMenuItems'](标签,_解散)#附加
                菜单树=标签菜单(回调['labels'],_关此,_解散,附加).渲染()#树
            芯片.append({#芯片
                'type':'tab',
                'data':'dockkit-tab',
                'tabId':标签标识,
                'selected':选中,
                'dragging':回调['draggingTabId']==标签标识,
                'title':标题,
                'menu':菜单树,
                'onPress':lambda 签=标签标识,事=None:回调['onTabPressed'](签,事),
                'onClick':lambda 签=标签标识:自身.激活标签(签),
                'onClose':lambda 签=标签标识:回调['onCloseTab'](签),
                'onContext':lambda 签=标签标识:自身.切换菜单(签),
                'onKey':lambda 键,签=标签标识:(
                    (lambda 下一:自身.激活标签(下一) if 下一 is not None else (
                        自身.激活标签(签) if 是否选定键(键) else None
                    ))(芯片导航目标(键,窗格['tabs'],签))
                ),
            })#片
        if 条带下标==len(窗格['tabs']):#末符
            芯片.append({'type':'caret','data':'dockkit-caret','index':条带下标})#符
        端=[]#条带末端控件
        if 回调['canAddTab'](窗格['id']):#可加
            端.append({#加
                'type':'addTab',
                'data':'dockkit-add-tab',
                'paneId':窗格['id'],
                'label':回调['labels']['addTab'],
                'onClick':lambda:回调['onAddTab'](窗格['id']),
            })#加
        端.append({'type':'stripFill','data':'dockkit-strip-fill'})#填充
        if not (回调['hideSplitAtCapacity'] and 阻断==分割阻断预算):#显示分割
            端.append({#分割钮
                'type':'splitButton',
                'data':'dockkit-split-button',
                'paneId':窗格['id'],
                'blocked':阻断,
                'title':_分割标题(回调['labels'],阻断),
                'disabled':阻断 is not None,
                'onClick':lambda:回调['onSplitPane'](窗格['id']),
            })#钮
        if 窗格['id']==回调['chromePaneId'] and 回调['chrome'] is not None:#铬
            端.append({'type':'chrome','data':'dockkit-strip-chrome','children':回调['chrome']})#铬
        正文=回调['labels']['emptyPane'] if 活动 is None else 回调['renderTab'](活动)#体
        提示=[]#投放提示
        if 区 is not None:#有区
            if 回调['horizontalDrops'] and 区!='center':#水平双提示
                提示=[#左右
                    {'type':'dockHint','zone':'left','active':区=='left'},
                    {'type':'dockHint','zone':'right','active':区=='right'},
                ]#提示
            else:#单区
                提示=[{'type':'dockHint','zone':区}]#一
        return {#树
            'type':'pane',
            'data':'dockkit-pane',
            'paneId':窗格['id'],
            'active':状态['activePaneId']==窗格['id'],
            'onFocusPane':自身.聚焦窗格体,
            'strip':{
                'type':'tabStrip',
                'data':'dockkit-strip',
                'paneId':窗格['id'],
                'tabs':芯片,
                'end':端,
            },
            'body':{'type':'paneBody','content':正文,'hints':提示},
        }#结束
