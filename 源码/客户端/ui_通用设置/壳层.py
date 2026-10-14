__all__=['触发器内容','页眉内容','关闭标签','样式表']#仅中文公开名

from nicegui import ui as 界面

样式表='''#对齐 chrome.module.css
.triggerLabel{overflow:hidden;white-space:nowrap}
'''#样式表结束

class 触发器内容:#触发行内容
    '图标；宽轨才显示标签'
    def __init__(自身,属性):#构造
        '记下 props'
        自身.属性=属性#合成 props
        if 't' in 自身.属性 and 'wide' in 自身.属性:#槽位份额齐了才画
            自身.渲染()#槽位只调用构造

    def 更新(自身,属性):#props 变更
        '刷新'
        自身.属性=属性#最新

    def 渲染(自身):#结构化视图
        '画出设置触发器'
        界面.add_css(样式表)
        翻译=自身.属性['t']#文案
        宽=自身.属性['wide']#宽轨；主人份额键名
        with 界面.row().classes('trigger'):
            界面.icon('settings', size='16px' if 宽 else '18px')
            if 宽:
                界面.label(翻译('trigger')).classes('triggerLabel')

    def __call__(自身,属性=None):#组件调用形
        '对齐 React 调用'
        if 属性 is not None:
            自身.更新(属性)#刷新
        return 自身.渲染()

class 页眉内容:#面板标题文本
    '渲染面板标题'
    def __init__(自身,属性):#构造
        '记下 props'
        自身.属性=属性#合成 props
        if 't' in 自身.属性:#有文案才画
            自身.渲染()#槽位只调用构造

    def 更新(自身,属性):#props 变更
        '刷新'
        自身.属性=属性#最新

    def 渲染(自身):#结构化视图
        '画出面板标题'
        界面.add_css(样式表)
        翻译=自身.属性['t']#文案
        界面.label(翻译('title')).classes('设置标题')

    def __call__(自身,属性=None):#组件调用形
        '对齐 React 调用'
        if 属性 is not None:
            自身.更新(属性)#刷新
        return 自身.渲染()

class 关闭标签:#关闭按钮视觉隐藏标签
    '关闭按钮可访问名'
    def __init__(自身,属性):#构造
        '记下 props'
        自身.属性=属性#合成 props
        if 't' in 自身.属性:#有文案才画
            自身.渲染()#槽位只调用构造

    def 更新(自身,属性):#props 变更
        '刷新'
        自身.属性=属性#最新

    def 渲染(自身):#结构化视图
        '画出关闭文案'
        界面.add_css(样式表)
        翻译=自身.属性['t']#文案
        界面.label(翻译('close'))

    def __call__(自身,属性=None):#组件调用形
        '对齐 React 调用'
        if 属性 is not None:
            自身.更新(属性)#刷新
        return 自身.渲染()
