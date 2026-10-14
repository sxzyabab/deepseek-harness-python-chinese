from nicegui import ui as 界面

__all__=['胶囊','样式表']#仅中文公开名

样式表='''
.胶囊{display:inline-flex;align-items:center;gap:4px;height:24px;padding:0 8px;border:none;border-radius:999px;font-size:12px;line-height:18px;color:var(--dsw-alias-label-secondary);background:var(--dsw-alias-bg-layer-2)}
button.q-btn.胶囊{min-height:24px;cursor:pointer}
button.q-btn.胶囊:hover{background:var(--dsw-alias-interactive-bg-hover) !important}
.胶囊.选中,button.q-btn.胶囊.选中{color:var(--dsw-alias-label-primary);background:var(--dsw-alias-button-ghost-active-fill) !important;box-shadow:inset 0 0 0 1px var(--dsw-alias-button-ghost-active-border)}
'''

样式已登记=False

def 登记样式():
    '同一段样式整个进程只登记一次'
    global 样式已登记
    if 样式已登记 is True:
        return
    界面.add_css(样式表)
    样式已登记=True

class 胶囊:#标签芯片
    '画出胶囊文案；有点击时做成按钮'
    def __init__(自身,属性=None,**关键字参数):#构造
        '合并 props'
        自身.属性=dict(属性 or {})#基础
        自身.属性.update(关键字参数)#覆盖

    def 更新(自身,属性):#props 变更
        '刷新'
        自身.属性=dict(属性)#最新

    def 渲染(自身):#画出胶囊
        '有点击画按钮，否则画标签'
        登记样式()
        点击=自身.属性.get('onClick')#点击
        可点=点击 is not None
        子=自身.属性.get('children')#子内容
        选中=bool(自身.属性.get('active'))#选中
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
        类名=自身.属性.get('className')#附加类
        类串='胶囊'+(' 选中' if 选中 else '')#基础类
        if isinstance(类名,str) and 类名!='':
            类串=类串+' '+类名#附
        文案=None#文字
        if isinstance(子,str):#字面
            文案=子#用
        elif isinstance(子,(list,tuple)) and all(isinstance(项,str) for 项 in 子):#全是字
            文案=''.join(子)#拼
        if 可点:#按钮
            def 点下():
                '调用点击'
                点击()#调用
            if isinstance(文案,str) or 子 is None:#文字或空胶囊
                界面.button('' if 文案 is None else 文案,on_click=点下).classes(类串)#按钮
                return
            行=界面.row().classes(类串)#组件子内容
            行.on('click',点下)#点击
            with 行:#内容
                画子(子)#子内容
            return
        if isinstance(文案,str) or 子 is None:#纯文字或空胶囊
            界面.label('' if 文案 is None else 文案).classes(类串)#标签
            return
        行=界面.row().classes(类串)#组件子内容
        with 行:#内容
            画子(子)#子内容

    def __call__(自身,属性=None,**关键字参数):#组件调用形
        '对齐 React 调用'
        if 属性 is not None or 关键字参数:
            合并=dict(属性 or {})#基础
            合并.update(关键字参数)#覆盖
            自身.更新(合并)#刷新
        return 自身.渲染()
