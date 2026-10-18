from .终端体 import 终端体

__all__=['惰性终端体']

_实例={}

class 惰性终端体:
    '正文挂上之后才把份额交给终端体'
    def __init__(自身,属性=None):
        '记下份额。同一页签复用已经挂上的终端体'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.体=None
        自身.根=None
        自身.渲染()

    def 更新(自身,属性):
        '换上一份份额'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '按页签取出终端体并画出'
        属性=自身.属性
        标签=属性['useTabInfo']()['tab']
        标识=标签['id']
        已有=_实例.get(标识)
        if 已有 is not None and 已有.模型 is None and 已有.根 is None:
            已有=None
        if 已有 is None:
            已有=终端体(属性)
            _实例[标识]=已有
        else:
            已有.更新(属性)
            已有.渲染()
        自身.体=已有
        自身.根=已有.根
        return 自身

    def __call__(自身,属性=None):
        '有新属性先更新，再画出'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
