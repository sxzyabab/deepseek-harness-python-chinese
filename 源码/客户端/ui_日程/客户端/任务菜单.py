'任务操作菜单：分隔、标题、可点项'
from nicegui import ui as 界面

__all__=['任务菜单']

class 任务菜单:
    '父组件调用渲染。open 不是 True 时不画'
    def __init__(自身,属性=None):
        '只记 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 更新(自身,属性):
        '刷新'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '按条目画按钮'
        属性=自身.属性
        if 'open' not in 属性 or 属性['open'] is not True:
            return
        条目=属性['items'] if 'items' in 属性 and isinstance(属性['items'],list) else []
        选择=属性['onSelect'] if 'onSelect' in 属性 and callable(属性['onSelect']) else (lambda _标识:None)
        关闭=属性['onClose'] if 'onClose' in 属性 and callable(属性['onClose']) else (lambda:None)
        with 界面.column().classes('schedule-task-menu'):
            for 项 in 条目:
                if not isinstance(项,dict):
                    continue
                if 项.get('separator') is True:
                    界面.separator()
                    continue
                if 项.get('labelOnly') is True:
                    界面.label(项['label'] if 'label' in 项 else '')
                    continue
                标识=项['id'] if 'id' in 项 else ''
                文=项['label'] if 'label' in 项 and isinstance(项['label'],str) else str(标识)
                def 点(当前=标识):
                    '选中并请父组件关闭'
                    选择(当前)
                    关闭()
                钮=界面.button(文, on_click=点).props('flat no-caps align=left')
                if 项.get('disabled') is True:
                    钮.disable()
            界面.button(on_click=关闭).props('icon=close flat round')

    def __call__(自身,属性=None):
        '更新后渲染'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
