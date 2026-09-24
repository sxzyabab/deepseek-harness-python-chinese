__all__=['账号头像']

class 账号头像:
    """装饰性头像；缺失或加载失败时用默认图标。"""
    def __init__(自身,属性=None):
        """记下网址。"""
        自身.属性={} if 属性 is None else 属性
        自身.失败网址=None

    def 更新(自身,属性):
        """刷新。"""
        自身.属性=属性

    def 标失败(自身):
        """当前网址加载失败后改走图标。"""
        自身.失败网址=自身.属性.get('url')

    def 渲染(自身):
        """图片或默认账号图标。"""
        网址=自身.属性.get('url')
        if 网址 and 网址!=自身.失败网址:
            return {
                'type':'account-avatar',
                'kind':'image',
                'src':网址,
                'onError':自身.标失败,
                'cssModule':'账号头像.module.css',
            }
        return {'type':'account-avatar','kind':'icon','size':16}

    def __call__(自身,属性=None):
        """对齐 React 调用。"""
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
