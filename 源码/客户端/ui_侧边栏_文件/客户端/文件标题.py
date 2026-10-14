from nicegui import ui as 界面
from ...ui_基础界面组件.文件类型图标 import 文件类型图标

__all__=['文件标题']

def _键齐(用标签信息):
    '有标签钩子才画芯片'
    if isinstance(用标签信息,dict):
        return callable(用标签信息.get('useTabInfo'))
    return callable(用标签信息)

class 文件标题:
    '芯片与浮动面板头部：文件夹图标加标签标题'

    def __init__(自身,用标签信息):
        '槽位传入 props 字典；直接调用时仍可以是钩子。槽位只调用构造，键齐了才画'
        if isinstance(用标签信息,dict):
            自身.属性=用标签信息
            钩=用标签信息['useTabInfo'] if 'useTabInfo' in 用标签信息 else None
            自身.用标签信息=钩 if callable(钩) else None
        else:
            自身.属性={}
            自身.用标签信息=用标签信息 if callable(用标签信息) else None
        if _键齐(用标签信息):
            自身.渲染()

    def 渲染(自身):
        '文件夹图标加标签标题。标签记录跨边界时是 dict，包内铸造时是对象'
        if not callable(自身.用标签信息):
            return
        信息=自身.用标签信息()
        签=信息['tab'] if isinstance(信息,dict) else 信息.tab
        标题=签['title'] if isinstance(签,dict) else 签.title
        with 界面.row().classes('file-title'):
            文件类型图标({'kind':'folder','size':16,'className':'titleIcon'}).渲染()
            if isinstance(标题,str):
                界面.label(标题)
