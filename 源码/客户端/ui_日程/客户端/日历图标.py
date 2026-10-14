'任务入口用的时钟图形'
from nicegui import ui as 界面

__all__=['日历图标']

class 日历图标:
    '父组件调用渲染。尺寸来自 props.size'
    def __init__(自身,属性=None):
        '只记尺寸'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 更新(自身,属性):
        '刷新'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '画出时钟'
        尺寸=自身.属性['size'] if 'size' in 自身.属性 else 16
        if isinstance(尺寸,bool) or not isinstance(尺寸,(int,float)):
            尺寸=16
        界面.icon('schedule', size=str(int(尺寸))+'px').props('aria-hidden=true')

    def __call__(自身,属性=None):
        '更新后渲染'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
