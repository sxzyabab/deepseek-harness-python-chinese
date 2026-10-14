'macOS 桌面折叠侧栏时对话 header 前置控件'

from nicegui import ui as 界面
from .文案 import 中文

__all__=['头部前置控件']#仅中文公开名

class 头部前置控件:#前置席位
    '侧栏打开与新建会话控件；非 Darwin 桌面返回空'

    def __init__(自身,属性):
        '记下切换侧栏与开新会话'
        自身.属性=属性#合成 props
        自身.渲染()#槽位只调用构造；非达尔文桌面不画

    def 是否达尔文桌面(自身):
        '对齐 isDarwinDesktop；宿主注入平台判定'
        return 自身.属性.get('darwinDesktop') is True#平台

    def 渲染(自身):
        '两枚图标按钮；非 Darwin 不画'
        if not 自身.是否达尔文桌面():#非桌面
            return
        切=自身.属性.get('toggleSidebar')
        开=自身.属性.get('startSession')
        def 点切换():
            '打开或收起侧栏'
            if 切 is not None:
                切()
        def 点新建():
            '开始新会话'
            if 开 is not None:
                开()
        with 界面.row().classes('header-leading'):
            界面.button(中文['toggle.open'], on_click=点切换).props('icon=menu')
            界面.button(中文['session.new'], on_click=点新建).props('icon=add')
