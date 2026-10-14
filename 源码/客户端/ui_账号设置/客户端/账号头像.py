from nicegui import ui as 界面

__all__=['账号头像']

头像样式='.账号头像{flex:none;display:flex;align-items:center;justify-content:center;width:32px;height:32px;border-radius:50%;color:var(--dsw-alias-label-tertiary);background:var(--dsw-alias-bg-skeleton);object-fit:cover}'
界面.add_css(头像样式,shared=True)

class 账号头像:
    '装饰性头像；缺失或加载失败时用默认图标'
    def __init__(自身,属性=None):
        '记下网址。父组件会调用，构造时不画'
        自身.属性={} if 属性 is None else 属性
        自身.失败网址=None

    def 更新(自身,属性):
        '刷新'
        自身.属性=属性

    def 标失败(自身):
        '当前网址加载失败后改走图标'
        自身.失败网址=自身.属性.get('url')

    def 渲染(自身):
        '图片或默认账号图标'
        网址=自身.属性.get('url')
        if not isinstance(网址,str) or 网址=='' or 网址==自身.失败网址:
            界面.icon('account_circle', size='32px').classes('账号头像')
            return
        图=界面.image(网址).classes('账号头像')
        def 失败():
            '加载失败后改走图标'
            自身.标失败()
            图.set_visibility(False)
            界面.icon('account_circle', size='32px').classes('账号头像')
        图.on('error',失败)

    def __call__(自身,属性=None):
        '对齐 React 调用'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
