__all__=['向导标题','罗盘标记','立方标记','画字形']#仅中文公开名

from nicegui import ui as 界面
from ....异常 import 异常原文

样式表='.titleIcon{flex:none;display:inline-flex;align-items:center;color:var(--dsw-alias-label-tertiary)}'
界面.add_css(样式表,shared=True)

罗盘标记='<svg width="{尺寸}" height="{尺寸}" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M8 14C11.3137 14 14 11.3137 14 8C14 4.68629 11.3137 2 8 2C4.68629 2 2 4.68629 2 8C2 11.3137 4.68629 14 8 14Z" stroke="currentColor" stroke-width="1"/><path d="M10.6101 5.39014L8.99014 8.99014L5.39014 10.6101L7.01014 7.01014L10.6101 5.39014Z" fill="currentColor"/></svg>'#罗盘
立方标记='<svg width="{尺寸}" height="{尺寸}" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M7.99998 2.5L12.9 5.2V10.8L7.99998 13.5L3.09998 10.8V5.2L7.99998 2.5Z" stroke="currentColor" stroke-linejoin="round" stroke-width="1"/><path d="M3.09998 5.19995L7.99998 7.89995M7.99998 7.89995L12.9 5.19995M7.99998 7.89995V13.5" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1"/></svg>'#立方


def 画字形(标记,尺寸,类名=None):
    '把字形画成内联 svg'
    节点=界面.html(标记.format(尺寸=尺寸),sanitize=False)#字形
    if 类名:
        节点.classes(类名)#类
    return 节点#节点


class 向导标题:#芯片标题
    '芯片与浮动面板头部：罗盘加向导签标题'

    def __init__(自身,用标签信息):
        '槽位传入 props 字典；直接调用时仍可以是钩子'
        if isinstance(用标签信息,dict):#槽位 props
            钩=用标签信息['useTabInfo'] if 'useTabInfo' in 用标签信息 else None#钩
            自身.用标签信息=钩 if callable(钩) else None#可读才留
        else:#旧调用
            自身.用标签信息=用标签信息 if callable(用标签信息) else None#钩子
        if callable(自身.用标签信息):
            自身.渲染()

    def 渲染(自身):
        '罗盘图标和标题文本。父组件不调用本方法，构造在键齐时自己画。'
        if not callable(自身.用标签信息):
            return
        try:
            信息=自身.用标签信息()#标签信息
            签=信息['tab'] if isinstance(信息,dict) else 信息.tab#标签记录
            标题=签['title'] if isinstance(签,dict) else 签.title#标题文本
            with 界面.row().style('align-items:center;gap:6px;flex-wrap:nowrap;min-width:0'):#芯片行
                画字形(罗盘标记,16,'titleIcon')#罗盘
                界面.label(str(标题))#标题
        except Exception as 错误:
            界面.label(异常原文(错误))
