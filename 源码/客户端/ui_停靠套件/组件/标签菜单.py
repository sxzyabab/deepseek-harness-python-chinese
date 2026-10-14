
from nicegui import ui as 界面

__all__=['标签菜单','菜单间隙']#仅中文公开名

菜单间隙=4#控件与菜单间距及视口边距


class 标签菜单:
    '关标签项 + 宿主附加项；打开时相对锚点定位'

    def __init__(自身,文案,关标签,解散,附加=None,锚点矩形=None,菜单宽=96):
        '文案含 closeTab；附加为结构树列表或 None'
        自身.文案=文案#文案 dict
        自身.关标签=关标签#回调
        自身.解散=解散#回调
        自身.附加=附加#额外项
        自身.锚点矩形=锚点矩形#宿主量得
        自身.菜单宽=菜单宽#估计宽
        自身.视口宽=None#可选，供翻转

    def 设锚点(自身,矩形,视口宽=None):
        '更新锚点矩形'
        自身.锚点矩形=矩形#锚
        自身.视口宽=视口宽#视口

    def 算位置(自身):
        '相对锚点的 top/left；无锚点则 None'
        if 自身.锚点矩形 is None:#无
            return None#未置
        矩=自身.锚点矩形#锚
        左=矩['x']#默认左齐
        if 自身.视口宽 is not None and 矩['x']+自身.菜单宽+菜单间隙>自身.视口宽:#越右
            左=max(菜单间隙,矩['x']+矩['width']-自身.菜单宽)#右齐
        return {'top':矩['y']+矩['height']+菜单间隙,'left':左}#位

    def 渲染(自身):
        '画出关标签菜单'
        with 界面.column().classes('dockkit-tab-menu'):
            界面.button(自身.文案['closeTab'], on_click=自身.关标签)
            附加=自身.附加
            if hasattr(附加,'渲染'):
                附加.渲染()
            elif isinstance(附加,list):
                for 项 in 附加:
                    if hasattr(项,'渲染'):
                        项.渲染()
                    elif isinstance(项,dict) and 'label' in 项:
                        def 点附加(回调=项.get('onClick')):
                            '附加项'
                            if 回调 is not None:
                                回调()
                        界面.button(项['label'], on_click=点附加)
            elif isinstance(附加,dict) and 'label' in 附加:
                def 点一项(回调=附加.get('onClick')):
                    '附加项'
                    if 回调 is not None:
                        回调()
                界面.button(附加['label'], on_click=点一项)
