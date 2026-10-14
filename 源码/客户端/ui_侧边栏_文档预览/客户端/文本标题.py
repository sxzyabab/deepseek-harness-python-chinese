from nicegui import ui as 界面
from ...ui_基础界面组件.文件类型图标 import 文件类型图标

__all__=['文本标题']


class 文本标题:
    '芯片与浮动面板标题：文件类型图标加标签标题'

    def __init__(自身,属性=None):
        '属性为合成 props；单独传入标签钩子时也接受'
        if callable(属性):
            自身.属性={'useTabInfo':属性}
        else:
            自身.属性=属性 if isinstance(属性,dict) else {}
        if 'useTabInfo' in 自身.属性 and callable(自身.属性['useTabInfo']):
            自身.渲染()

    def 更新(自身,属性):
        '刷新合成 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '十六像素类型图标后接标题'
        取=自身.属性['useTabInfo'] if 'useTabInfo' in 自身.属性 and callable(自身.属性['useTabInfo']) else None
        if 取 is None:
            return
        信息=取()
        签=信息['tab'] if isinstance(信息,dict) else 信息.tab
        标题=签['title'] if isinstance(签,dict) else 签.title
        with 界面.row().classes('text-title'):
            文件类型图标({'path':标题 if isinstance(标题,str) else '','size':16,'className':'titleIcon'}).渲染()
            if isinstance(标题,str):
                界面.label(标题)

    def __call__(自身,属性=None):
        '对齐组件调用'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
