from nicegui import ui as 界面

__all__=['提示泡','侧表','样式表']#仅中文公开名

样式表='''
.q-tooltip{max-width:50vw;padding:3px 7px;border-radius:var(--dsw-radius-sm);background:var(--dsw-alias-tooltip-bg);color:var(--dsw-static-neutral-bluish-00);font-size:13px;line-height:20px;white-space:pre-line;overflow-wrap:break-word}
'''

侧表=('right','bottom','top')#放置侧

样式已登记=False

def 登记样式():
    '同一段样式整个进程只登记一次'
    global 样式已登记
    if 样式已登记 is True:
        return
    界面.add_css(样式表)
    样式已登记=True

class 提示泡:#锚点提示
    'hover/focus 显气泡；disabled 不改锚布局'
    def __init__(自身,属性=None,**关键字参数):
        '合并 props'
        自身.属性=dict(属性 if 属性 is not None else {})#基础
        自身.属性.update(关键字参数)#覆盖
        自身.可见=False#显
        自身.放置=自身.属性['side'] if 'side' in 自身.属性 else 'right'#侧

    def 更新(自身,属性):
        '刷新'
        自身.属性=dict(属性)#最新
        禁用=属性['disabled'] is True if 'disabled' in 属性 else False#禁用
        if 禁用 is True:#禁用中
            自身.可见=False#隐

    def 显示(自身):
        '显气泡'
        禁用=自身.属性['disabled'] is True if 'disabled' in 自身.属性 else False#禁
        if 禁用 is False:#可显
            自身.可见=True#显

    def 隐藏(自身):
        '隐气泡'
        自身.可见=False#隐

    def 解析标签(自身):
        '字符串或惰性函数'
        标签=自身.属性['label'] if 'label' in 自身.属性 else ''#标签
        if 自身.可见 is False:#隐
            return None#不画
        if isinstance(标签,str):#字面量
            return 标签#文案
        return 标签()#惰性

    def 渲染(自身):
        '画出锚，悬停时显示提示'
        登记样式()
        属性=自身.属性#props
        侧=属性['side'] if 'side' in 属性 else 'right'#请求侧
        if 侧 not in 侧表:#非法
            侧='right'#回退
        禁用=属性['disabled'] is True if 'disabled' in 属性 else False#禁
        子=属性['children'] if 'children' in 属性 else None#锚
        标签=属性['label'] if 'label' in 属性 else ''#标签
        if isinstance(标签,str):#字面
            文=标签#文案
        elif 标签 is not None:#惰性
            文=标签()#取文
        else:#无
            文=''#空
        if isinstance(文,str) is False and 文 is not None:#非串
            文=str(文)#转
        if 文 is None:#无
            文=''#空
        def 画子(内容):
            '字符串做标签，组件自己画'
            if 内容 is None:#无
                return
            if isinstance(内容,str):#文案
                界面.label(内容)#标签
                return
            if isinstance(内容,(list,tuple)):#多项
                for 项 in 内容:#逐项
                    画子(项)#递归
                return
            if hasattr(内容,'渲染'):#组件
                内容.渲染()#自画
        锚=界面.row().classes('提示泡')#锚
        with 锚:#内容
            画子(子)#锚内容
        if 禁用 is False and 文!='':#可提示
            放置={'right':'anchor=center right self=center left','bottom':'anchor=bottom middle self=top middle','top':'anchor=top middle self=bottom middle'}#侧
            泡=锚.tooltip(文)#气泡
            泡.props(放置[侧])#侧
            宽=属性['maxWidth'] if 'maxWidth' in 属性 else None#宽帽
            if 宽 is not None:
                泡.style('max-width:'+str(宽)+('px' if isinstance(宽,(int,float)) else ''))#宽
        def 进入():
            '显示'
            自身.显示()#显
        def 离开():
            '隐藏'
            自身.隐藏()#隐
        if 禁用 is False:#可悬停
            锚.on('mouseenter',进入)#入
            锚.on('mouseleave',离开)#出

    def __call__(自身,属性=None,**关键字参数):
        '对齐 React'
        if 属性 is not None or len(关键字参数)>0:#有；判 length
            合并=dict(属性 if 属性 is not None else {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()
