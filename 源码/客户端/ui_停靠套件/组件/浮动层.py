from nicegui import ui as 界面
from ..引擎.约束 import 浮动最小尺寸#下限
from ..引擎.几何 import 平移矩形,缩放矩形#几何
from ..引擎.树 import 浮动矩形,取窗格,取标签,唯一标签标识#树
from .指针 import 手势会话#手势

__all__=['浮动层']#仅中文公开名


def _已抬顶(状态,窗格标识):
    '是否已聚焦且在 z 顶'
    return 状态['activePaneId']==窗格标识 and len(状态['floats'])>0 and 状态['floats'][-1]==窗格标识#抬


def _同矩形(甲,乙):
    '坐标是否全同'
    return 甲['x']==乙['x'] and 甲['y']==乙['y'] and 甲['width']==乙['width'] and 甲['height']==乙['height']#同


class 浮动层:
    '浮窗列表；拖移/缩放预览至落定上报意图'

    def __init__(自身,状态,意图,文案,渲标签,渲标签标题=None):
        '记下布局与出口'
        自身.状态=状态#布局
        自身.意图=意图#意图
        自身.文案=文案#文案
        自身.渲标签=渲标签#正文
        自身.渲标签标题=渲标签标题#标题
        自身._预览=None# {paneId, rect}
        自身._手势=手势会话(lambda:自身._清预览())#手势

    def 更新(自身,状态,意图,文案,渲标签,渲标签标题=None):
        'props 变更'
        自身.状态=状态#态
        自身.意图=意图#意图
        自身.文案=文案#文案
        自身.渲标签=渲标签
        自身.渲标签标题=渲标签标题#标题

    def _清预览(自身):
        '清空预览'
        自身._预览=None

    def 抬升(自身,窗格标识):
        '聚焦抬顶；已抬则无'
        if _已抬顶(自身.状态,窗格标识):#已
            return#无
        自身.意图.focusPane(窗格标识)#焦

    def 开始拖移(自身,窗格标识,原点横,原点纵):
        '标题栏按下：拖移；未动则抬升'
        起=浮动矩形(取窗格(自身.状态,窗格标识))#起矩
        def 移动(事件):
            '预览'
            自身._预览={'paneId':窗格标识,'rect':平移矩形(起,事件['clientX']-原点横,事件['clientY']-原点纵)}#预览
        def 抬起(事件):
            '落定'
            矩=平移矩形(起,事件['clientX']-原点横,事件['clientY']-原点纵)#终
            if _同矩形(矩,起):#未动
                自身.抬升(窗格标识)#点击抬
            else:#移动
                自身.意图.moveFloat(窗格标识,矩['x'],矩['y'])#报
        return 自身._手势.开始(移动,抬起)#喂入

    def 开始缩放(自身,窗格标识,原点横,原点纵):
        '角点按下：缩放；未动则抬升'
        起=浮动矩形(取窗格(自身.状态,窗格标识))#起
        def 移动(事件):
            '预览'
            自身._预览={'paneId':窗格标识,'rect':缩放矩形(起,事件['clientX']-原点横,事件['clientY']-原点纵,浮动最小尺寸)}#预览
        def 抬起(事件):
            '落定'
            矩=缩放矩形(起,事件['clientX']-原点横,事件['clientY']-原点纵,浮动最小尺寸)#终
            if _同矩形(矩,起):#未动
                自身.抬升(窗格标识)#点击
            else:#缩放
                自身.意图.resizeFloat(窗格标识,矩)#报
        return 自身._手势.开始(移动,抬起)#喂入

    def 渲染(自身):
        '画出浮窗'
        for 深,窗格标识 in enumerate(自身.状态['floats']):#底到顶
            窗格=取窗格(自身.状态,窗格标识)#窗
            标签=取标签(自身.状态,唯一标签标识(窗格))#签
            if 自身._预览 is not None and 自身._预览['paneId']==窗格标识:#预览中
                活矩=自身._预览['rect']#预览
                层=len(自身.状态['floats'])+1#顶
            else:#录制
                活矩=浮动矩形(窗格)#矩
                层=深+1#z
            标题=标签['title']#默认
            if 自身.渲标签标题 is not None:#自定义
                产出=自身.渲标签标题(标签)
                if isinstance(产出,str):
                    标题=产出
                elif hasattr(产出,'渲染'):
                    产出.渲染()
            样式='left:'+str(活矩['x'])+'px;top:'+str(活矩['y'])+'px;width:'+str(活矩['width'])+'px;height:'+str(活矩['height'])+'px;z-index:'+str(层)
            def 抬(窗=窗格标识):
                '抬到前面'
                自身.抬升(窗)
            def 收回(窗=窗格标识):
                '收回停靠'
                自身.意图.unfloatPane(窗)
            def 关闭(签=标签['id']):
                '关闭浮窗'
                自身.意图.closeTab(签)
            with 界面.card().classes('dockkit-float').style(样式):
                界面.button(str(标题), on_click=抬)
                正文=自身.渲标签(标签)
                if hasattr(正文,'渲染'):
                    正文.渲染()
                elif isinstance(正文,str) and 正文!='':
                    界面.label(正文)
                with 界面.row():
                    界面.button(自身.文案['dockFloat'], on_click=收回)
                    界面.button(自身.文案['closeFloat'], on_click=关闭)
