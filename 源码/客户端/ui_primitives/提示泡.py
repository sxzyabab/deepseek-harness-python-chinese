"""悬停/焦点提示泡。

对齐上游 `ui-primitives/src/Tooltip.tsx`。公开面仅中文名。
锚点为子元素本身；气泡 fixed 定位。
"""

__all__=['提示泡','侧表']#仅中文公开名

侧表=('right','bottom','top')#放置侧

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class 提示泡:#锚点提示
    """hover/focus 显气泡；disabled 不改锚布局。"""

    def __init__(自身,属性=None,**关键字参数):#构造
        """合并 props。"""
        自身.属性=dict(属性 or {})#基础
        自身.属性.update(关键字参数)#覆盖
        自身.可见=False#显
        自身.放置=取字段(自身.属性,'side','right')#侧

    def 更新(自身,属性):#刷新
        """刷新。"""
        自身.属性=dict(属性)#最新
        if 取字段(属性,'disabled'):#禁用中
            自身.可见=False#隐

    def 解析标签(自身):#解析文案
        """字符串或惰性函数。"""
        标签=取字段(自身.属性,'label','')#标签
        if callable(标签):#惰性
            return 标签() if 自身.可见 else None#仅可见时算
        return 标签 if 自身.可见 else None#文案

    def 渲染(自身):#结构树
        """锚+条件气泡。"""
        属性=自身.属性#props
        侧=取字段(属性,'side','right')#请求侧
        if 侧 not in 侧表:#非法
            侧='right'#回退
        禁用=bool(取字段(属性,'disabled',False))#禁
        return {#提示
            'type':'tooltip',#类型
            'visible':自身.可见 and not 禁用,#显
            'label':自身.解析标签(),#文案
            'side':自身.放置 if 自身.可见 else 侧,#实际侧
            'requestedSide':侧,#请求
            'delayMs':取字段(属性,'delayMs',0),#延迟
            'disabled':禁用,#禁
            'maxWidth':取字段(属性,'maxWidth'),#宽帽
            'children':取字段(属性,'children'),#锚
            'onShow':lambda:自身.__setattr__('可见',True) if not 禁用 else None,#显
            'onHide':lambda:自身.__setattr__('可见',False),#隐
            'cssModule':'提示泡.module.css',#样式
        }#视图结束

    def __call__(自身,属性=None,**关键字参数):#调用形
        """对齐 React。"""
        if 属性 is not None or 关键字参数:#有
            合并=dict(属性 or {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()#渲
