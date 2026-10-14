'日期和时钟选择器的弹出层'
from nicegui import ui as 界面

__all__=['选择器弹出']

class 选择器弹出:
    '父组件调用渲染。open 不是 True 时不画'
    def __init__(自身,属性=None):
        '只记 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 更新(自身,属性):
        '刷新'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '标题加子内容'
        属性=自身.属性
        if 'open' not in 属性 or 属性['open'] is not True:
            return
        标签=属性['label'] if 'label' in 属性 and isinstance(属性['label'],str) else ''
        with 界面.column().classes('schedule-picker'):
            if 标签!='':
                界面.label(标签)
            子=属性['children'] if 'children' in 属性 else None
            if hasattr(子,'渲染'):
                子.渲染()
            elif callable(子):
                子()
            关闭=属性['onClose'] if 'onClose' in 属性 and callable(属性['onClose']) else None
            if 关闭 is not None:
                界面.button(on_click=关闭).props('icon=close flat round')

    def __call__(自身,属性=None):
        '更新后渲染'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
