__all__=['官方品牌标志','官方品牌名称']#仅中文公开名

class 官方品牌标志:#侧栏标志占位
    """按宿主面请求的呈现渲染官方鲸鱼标志。"""
    def __init__(自身,属性=None):
        """记下 props。"""
        自身.属性={} if 属性 is None else 属性#合成

    def 更新(自身,属性):
        """刷新 props。"""
        自身.属性={} if 属性 is None else 属性#新

    def 渲染(自身):
        """官方鱼标。"""
        尺寸=自身.属性['size'] if 'size' in 自身.属性 else None#宿主请求尺寸
        return {'type':'fish-logo','size':尺寸}#官方鱼标

    def __call__(自身,属性=None):
        """对齐 React。"""
        if 属性 is not None:
            自身.更新(属性)#刷
        return 自身.渲染()#渲

class 官方品牌名称:#侧栏名称占位
    """渲染官方名称画作，不含其独立成槽的标志。"""
    def __init__(自身,属性=None):
        """记下 props。"""
        自身.属性={} if 属性 is None else 属性#合成

    def 更新(自身,属性):
        """刷新 props。"""
        自身.属性={} if 属性 is None else 属性#新

    def 渲染(自身):
        """官方名称字标。"""
        return {'type':'brand-wordmark','includeMark':False}#字标不含内嵌标志

    def __call__(自身,属性=None):
        """对齐 React。"""
        if 属性 is not None:
            自身.更新(属性)#刷
        return 自身.渲染()#渲
