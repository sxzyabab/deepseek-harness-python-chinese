import math
from nicegui import ui as 界面
from .类型 import 适应宽度,最小固定缩放,最大固定缩放,缩放步长,缩放选项
from .文案 import 中文 as 缩放中文

__all__=['缩放控件','步进缩放']


def 步进缩放(倍率,方向):
    '按四分之一档夹紧固定倍率。方向为 -1 或 1'
    if 方向==-1:
        步=math.ceil(倍率/缩放步长)-1
    else:
        步=math.floor(倍率/缩放步长)+1
    下一=步*缩放步长
    if 下一<最小固定缩放:
        return 最小固定缩放
    if 下一>最大固定缩放:
        return 最大固定缩放
    return 下一


class 缩放控件:
    '适应宽度、预设比例与加减'

    def __init__(自身,属性):
        '记下偏好、文案与回调'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.菜单开=False

    def 渲染(自身):
        '画出缩放工具条'
        属性=自身.属性
        偏好=属性['preference'] if 'preference' in 属性 and 属性['preference'] is not None else 适应宽度
        翻译=属性['t'] if 't' in 属性 else None
        变更=属性['onPreference'] if 'onPreference' in 属性 else None
        def 文(键):
            '优先席位文案，缺键用缩放词典'
            if 翻译 is not None:
                值=翻译(键)
                if isinstance(值,str) and 值!='' and 值!=键:
                    return 值
            return 缩放中文[键]
        适应=not isinstance(偏好,dict) or 偏好.get('kind')=='fit-width'
        倍率=1 if 适应 or 'scale' not in 偏好 else 偏好['scale']
        def 写(下一):
            '交给偏好回调'
            if 变更 is not None:
                变更(下一)
        def 缩小():
            '降一档并离开适应宽度'
            写({'kind':'fixed','scale':步进缩放(1 if 适应 else 倍率,-1)})
        def 放大():
            '升一档并离开适应宽度'
            写({'kind':'fixed','scale':步进缩放(1 if 适应 else 倍率,1)})
        def 适应宽():
            '回到适应宽度'
            自身.菜单开=False
            写(适应宽度)
        def 固定(值):
            '选一个预设倍率'
            def 点():
                自身.菜单开=False
                写({'kind':'fixed','scale':值})
            return 点
        def 开关菜单():
            '展开或收起比例菜单'
            自身.菜单开=not 自身.菜单开
        百分=文('zoomValue').replace('{percent}',str(int(round((1 if 适应 else 倍率)*100))))
        with 界面.row().classes('zoom-controls').props('role=toolbar aria-label="'+文('zoomControls')+'"'):
            减=界面.button('−', on_click=缩小).props('flat dense aria-label="'+文('zoomOut')+'"')
            if (1 if 适应 else 倍率)<=最小固定缩放:
                减.disable()
            界面.button(文('zoomFitWidth') if 适应 else 百分, on_click=开关菜单).props('flat dense no-caps aria-label="'+文('zoomMenu')+'"')
            加=界面.button('+', on_click=放大).props('flat dense aria-label="'+文('zoomIn')+'"')
            if (1 if 适应 else 倍率)>=最大固定缩放 and 适应 is not True:
                加.disable()
            if 自身.菜单开:
                with 界面.column().classes('zoom-menu'):
                    界面.button(文('zoomFitWidth'), on_click=适应宽).props('flat no-caps align=left')
                    for 值 in 缩放选项:
                        界面.button(文('zoomValue').replace('{percent}',str(int(值*100))), on_click=固定(值)).props('flat no-caps align=left')
