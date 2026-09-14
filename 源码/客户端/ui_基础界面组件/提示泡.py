__all__=['提示泡','侧表']#仅中文公开名

侧表=('right','bottom','top')#放置侧

class 提示泡:#锚点提示
    """hover/focus 显气泡；disabled 不改锚布局。"""
    def __init__(自身,属性=None,**关键字参数):
        """合并 props。"""
        自身.属性=dict(属性 if 属性 is not None else {})#基础
        自身.属性.update(关键字参数)#覆盖
        自身.可见=False#显
        自身.放置=自身.属性['side'] if 'side' in 自身.属性 else 'right'#侧

    def 更新(自身,属性):
        """刷新。"""
        自身.属性=dict(属性)#最新
        禁用=属性['disabled'] is True if 'disabled' in 属性 else False#禁用
        if 禁用 is True:#禁用中
            自身.可见=False#隐

    def 显示(自身):
        """显气泡。"""
        禁用=自身.属性['disabled'] is True if 'disabled' in 自身.属性 else False#禁
        if 禁用 is False:#可显
            自身.可见=True#显

    def 隐藏(自身):
        """隐气泡。"""
        自身.可见=False#隐

    def 解析标签(自身):
        """字符串或惰性函数。"""
        标签=自身.属性['label'] if 'label' in 自身.属性 else ''#标签
        if 自身.可见 is False:#隐
            return None#不画
        if isinstance(标签,str):#字面量
            return 标签#文案
        return 标签()#惰性

    def 渲染(自身):
        """锚+条件气泡。"""
        属性=自身.属性#props
        侧=属性['side'] if 'side' in 属性 else 'right'#请求侧
        if 侧 not in 侧表:#非法
            侧='right'#回退
        禁用=属性['disabled'] is True if 'disabled' in 属性 else False#禁
        return {#提示
            'type':'tooltip',#类型
            'visible':自身.可见 is True and 禁用 is False,#显
            'label':自身.解析标签(),#文案
            'side':自身.放置 if 自身.可见 is True else 侧,#实际侧
            'requestedSide':侧,#请求
            'delayMs':属性['delayMs'] if 'delayMs' in 属性 else 0,#延迟
            'disabled':禁用,#禁
            'maxWidth':属性['maxWidth'] if 'maxWidth' in 属性 else None,#宽帽
            'children':属性['children'] if 'children' in 属性 else None,#锚
            'onShow':自身.显示,#显
            'onHide':自身.隐藏,#隐
            'cssModule':'提示泡.module.css',#样式
        }#视图结束

    def __call__(自身,属性=None,**关键字参数):
        """对齐 React。"""
        if 属性 is not None or len(关键字参数)>0:#有；判 length
            合并=dict(属性 if 属性 is not None else {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()#渲
