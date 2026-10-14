from ...ui_基础界面组件.鱼标 import 鱼标
from ...ui_基础界面组件.品牌字标 import 品牌字标

__all__=['官方品牌标志','官方品牌名称']#仅中文公开名

class 官方品牌标志:#侧栏标志占位
    '按宿主面请求的呈现渲染官方鲸鱼标志'
    def __init__(自身,属性=None):
        '记下 props。槽位只调用构造，没有必填键，空表也画。'
        自身.属性=属性 if isinstance(属性,dict) else {}#合成
        自身.渲染()

    def 更新(自身,属性):
        '刷新 props'
        自身.属性=属性 if isinstance(属性,dict) else {}#新

    def 渲染(自身):
        '官方鱼标'
        尺寸=自身.属性['size'] if 'size' in 自身.属性 else None#宿主请求尺寸
        鱼标({} if 尺寸 is None else {'size':尺寸}).渲染()#鱼标构造不画，由这里调用渲染

    def __call__(自身,属性=None):
        '对齐 React'
        if 属性 is not None:
            自身.更新(属性)#刷
        return 自身.渲染()

class 官方品牌名称:#侧栏名称占位
    '渲染官方名称画作，不含其独立成槽的标志'
    def __init__(自身,属性=None):
        '记下 props。槽位只调用构造，没有必填键，空表也画。'
        自身.属性=属性 if isinstance(属性,dict) else {}#合成
        自身.渲染()

    def 更新(自身,属性):
        '刷新 props'
        自身.属性=属性 if isinstance(属性,dict) else {}#新

    def 渲染(自身):
        '官方名称字标，不含重复的鱼'
        品牌字标({'includeMark':False}).渲染()#字标构造不画，由这里调用渲染

    def __call__(自身,属性=None):
        '对齐 React'
        if 属性 is not None:
            自身.更新(属性)#刷
        return 自身.渲染()