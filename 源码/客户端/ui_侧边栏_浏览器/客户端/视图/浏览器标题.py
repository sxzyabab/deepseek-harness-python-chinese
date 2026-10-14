from nicegui import ui as 界面
from ..浏览器.导航 import 浏览器导航
from .浏览器体 import 样式表 as _浏览器样式

__all__=['浏览器标题']

if not isinstance(_浏览器样式,str) or _浏览器样式=='':
    raise OSError('样式读不到')

def _键齐(属性):
    '页签和存储都在才画芯片'
    return isinstance(属性,dict) and 'useTabInfo' in 属性 and 'useStore' in 属性

class 浏览器标题:
    '芯片标题：地球图标与当前主机名或页签标题'

    def __init__(自身,属性=None):
        '记下标题席 props。槽位只调用构造，键齐了才画'
        自身.属性=属性 if isinstance(属性,dict) else {}
        if _键齐(自身.属性):
            自身.渲染()

    def 更新(自身,属性):
        '刷新合成 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '画出图标和标题'
        属性=自身.属性
        if not _键齐(属性):
            return
        标签=属性['useTabInfo']()['tab']
        def 选当前(状态):
            '取当前历史条目'
            桶=状态['byTab'][标签['id']] if isinstance(状态,dict) and 标签['id'] in 状态['byTab'] else None
            return 浏览器导航.当前(桶)
        条目=属性['useStore'](选当前)
        标题=条目['title'] if isinstance(条目,dict) and 'title' in 条目 and 条目['title'] is not None else 标签['title']
        with 界面.row().classes('browser-title'):
            界面.icon('public').classes('titleIcon')
            if isinstance(标题,str):
                界面.label(标题)

    def __call__(自身,属性=None):
        '有新属性先更新，再画出'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
