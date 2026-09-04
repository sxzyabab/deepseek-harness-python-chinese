"""通用浏览器品牌槽位的官方 DeepSeek Harness 占位。

对齐上游 `ui-brand-official/src/client/Brand.tsx`。公开面仅中文名。
无真 React：返回结构树字典。
"""
__all__=['官方品牌标志','官方品牌名称']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class 官方品牌标志:#侧栏标志占位
    """按宿主面请求的呈现渲染官方鲸鱼标志。"""

    def __init__(自身,属性=None):#构造
        """记下 props。"""
        自身.属性=属性 or {}#合成

    def 更新(自身,属性):#刷新
        """刷新 props。"""
        自身.属性=属性 or {}#新

    def 渲染(自身):#结构树
        """官方鱼标。"""
        尺寸=取字段(自身.属性,'size')#宿主请求尺寸
        return {'type':'fish-logo','size':尺寸}#官方鱼标

    def __call__(自身,属性=None):#调用形
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲

class 官方品牌名称:#侧栏名称占位
    """渲染官方名称画作，不含其独立成槽的标志。"""

    def __init__(自身,属性=None):#构造
        """记下 props。"""
        自身.属性=属性 or {}#合成

    def 更新(自身,属性):#刷新
        """刷新 props。"""
        自身.属性=属性 or {}#新

    def 渲染(自身):#结构树
        """官方名称字标。"""
        return {'type':'brand-wordmark','includeMark':False}#字标不含内嵌标志

    def __call__(自身,属性=None):#调用形
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
