"""壳层 chrome 内容：触发器/页眉/关闭标签。

对齐上游 `ui-settings-general/src/client/chrome.tsx`。公开面仅中文名。
"""

__all__=['触发器内容','页眉内容','关闭标签','样式表']#仅中文公开名

样式表='''#对齐 chrome.module.css
.triggerLabel{overflow:hidden;white-space:nowrap}
'''#样式表结束

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class 触发器内容:#触发行内容
    """图标；宽轨才显示标签。"""
    def __init__(自身,属性):#构造
        """记下 props。"""
        自身.属性=属性#合成 props

    def 更新(自身,属性):#props 变更
        """刷新。"""
        自身.属性=属性#最新

    def 渲染(自身):#结构化视图
        """产出触发器内容。"""
        翻译=取字段(自身.属性,'t',lambda 键,_=None:键)#文案
        宽=bool(取字段(自身.属性,'wide'))#宽轨
        return {#视图
            'type':'settings-trigger',#类型
            'wide':宽,#宽轨
            'iconSize':16 if 宽 else 18,#图标尺寸
            'label':翻译('trigger') if 宽 else None,#宽轨标签
            'css':样式表,#样式
        }#视图结束

    def __call__(自身,属性=None):#组件调用形
        """对齐 React 调用。"""
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染

class 页眉内容:#面板标题文本
    """渲染面板标题。"""
    def __init__(自身,属性):#构造
        """记下 props。"""
        自身.属性=属性#合成 props

    def 更新(自身,属性):#props 变更
        """刷新。"""
        自身.属性=属性#最新

    def 渲染(自身):#结构化视图
        """产出标题文本。"""
        翻译=取字段(自身.属性,'t',lambda 键,_=None:键)#文案
        return {'type':'settings-header','text':翻译('title')}#标题

    def __call__(自身,属性=None):#组件调用形
        """对齐 React 调用。"""
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染

class 关闭标签:#关闭按钮视觉隐藏标签
    """关闭按钮可访问名。"""
    def __init__(自身,属性):#构造
        """记下 props。"""
        自身.属性=属性#合成 props

    def 更新(自身,属性):#props 变更
        """刷新。"""
        自身.属性=属性#最新

    def 渲染(自身):#结构化视图
        """产出关闭文案。"""
        翻译=取字段(自身.属性,'t',lambda 键,_=None:键)#文案
        return {'type':'settings-close-label','text':翻译('close')}#关闭

    def __call__(自身,属性=None):#组件调用形
        """对齐 React 调用。"""
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染
