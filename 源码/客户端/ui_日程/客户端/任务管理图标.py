'侧栏任务入口的时钟'
from .日历图标 import 日历图标

__all__=['任务管理图标']

class 任务管理图标:
    '槽位只调用构造。侧栏自己提供无障碍名'
    def __init__(自身,属性=None):
        '记下尺寸。槽位只调用构造，没有必填键，空表也画。'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.渲染()

    def 更新(自身,属性):
        '刷新'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '按侧栏要的边长画时钟'
        尺寸=自身.属性['size'] if 'size' in 自身.属性 else 16
        日历图标({'size':尺寸}).渲染()

    def __call__(自身,属性=None):
        '更新后渲染'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
