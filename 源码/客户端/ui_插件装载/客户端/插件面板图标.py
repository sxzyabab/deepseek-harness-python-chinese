__all__=['插件面板图标','插件刷新提示']#仅中文公开名

from nicegui import ui as 界面
from ...ui_基础界面组件.icons import 图标Cordis插件14
from ..异常 import 页面失败文案
from .呈现 import 提示文案#提示句

class 插件面板图标:
    '侧栏插件入口图标。槽位只调用构造，没有必填键，空表也画。'
    def __init__(自身,属性=None):
        '记下尺寸'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.渲染()

    def 更新(自身,属性):
        '刷新'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '按钮、标签与选中态由侧栏拥有'
        尺寸=自身.属性['size'] if 'size' in 自身.属性 else 16#边长
        图标Cordis插件14({'size':尺寸})#风车标

    def __call__(自身,属性=None):
        '更新后渲染'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()

class 插件刷新提示:
    '离开插件页后仍显示刷新失败'
    def __init__(自身,属性):
        '记下 props。槽位只调用构造，键齐了就画。'
        自身.属性=属性 if isinstance(属性,dict) else {}
        if 't' in 自身.属性 and ('hooks' in 自身.属性 or 'usePluginManager' in 自身.属性):
            自身.渲染()

    def 更新(自身,属性):
        '刷新'
        自身.属性=属性

    def 渲染(自身):
        '仅 refresh-failed 画一句，关掉即 dismiss'
        钩=自身.属性['hooks'] if 'hooks' in 自身.属性 and 自身.属性['hooks'] is not None else {}
        存储=钩['pluginManager'] if 'pluginManager' in 钩 else None
        用=自身.属性['usePluginManager'] if 'usePluginManager' in 自身.属性 else None
        if 存储 is not None:
            状态=存储.getSnapshot()
        elif 用 is not None:
            状态=用(lambda 快照:快照)
        else:
            return
        提示=状态['notice'] if 'notice' in 状态 else None
        旧=getattr(自身,'根',None)
        if 提示 is None or 提示.get('kind')!='refresh-failed':
            if 旧 is not None:
                try:
                    旧.clear()
                    旧.set_visibility(False)
                except Exception as 错误:
                    自身.根=None
                    界面.label(页面失败文案(错误))
            return
        画面失败=None
        if 旧 is not None:
            try:
                旧.clear()
                旧.set_visibility(True)
            except Exception as 错误:
                自身.根=None
                画面失败=页面失败文案(错误)
        if getattr(自身,'根',None) is None:
            自身.根=界面.row().classes('plugin-refresh-toast')
        翻译=自身.属性['t']
        with 自身.根:
            if isinstance(画面失败,str) and 画面失败!='':
                界面.label(画面失败)
            界面.icon('warning')
            界面.label(提示文案(提示,翻译))
            def 点关():
                '关掉这条提示'
                自身.属性['dismissNotice']()
                自身.渲染()
            界面.button(on_click=点关).props('icon=close flat round')

    def __call__(自身,属性=None):
        '对齐 React 调用'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
