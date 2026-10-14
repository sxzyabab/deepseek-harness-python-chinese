from nicegui import ui as 界面
from ...ui_基础界面组件.状态点 import 状态点

__all__=['加载指示器','加载状态','样式表']

样式表='''
.loading{display:flex;flex-direction:column;gap:12px;align-items:center;justify-content:center;box-sizing:border-box;width:100%;height:100%;min-height:0;padding:24px;color:var(--dsw-alias-label-secondary);font-size:var(--dsh-content-font-size,14px);line-height:1.5;text-align:center;white-space:normal}
.inline{display:inline-flex;flex-direction:row;gap:8px;width:auto;height:auto;padding:0;vertical-align:middle}
'''
界面.add_css(样式表,shared=True)

def 加载指示器(标签,类名=None):
    '产出动画、可访问的加载状态结构'
    return {'kind':'loading','label':标签,'className':类名,'role':'status'}#结构


class 加载状态:
    '居中或行内的加载状态'

    def __init__(自身,标签,行内=False):
        '记下状态文案与是否行内'
        自身.标签=标签#文案
        自身.行内=行内 is True#行内

    def 渲染(自身):
        '状态点；非行内时带文案'
        类名='loading inline' if 自身.行内 else 'loading'
        with 界面.element('span').classes(类名).props('role=status aria-label="'+自身.标签+'"'):
            状态点({'state':'ongoing','size':14 if 自身.行内 else 28}).渲染()
            if 自身.行内 is not True:
                界面.label(自身.标签)
