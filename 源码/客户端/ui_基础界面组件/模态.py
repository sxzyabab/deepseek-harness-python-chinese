from nicegui import ui as 界面

__all__=['模态','保持毫秒','样式表']#仅中文公开名

样式表='''
.q-card.模态{box-sizing:border-box;display:flex;flex-direction:column;gap:0;width:min(380px,100%);padding:0 0 24px;overflow:hidden;border-radius:var(--dsw-radius-panel);background:var(--dsw-alias-bg-layer-2);box-shadow:var(--dsw-elevation-prominent);color:var(--dsw-alias-label-primary)}
.模态头{width:100%;align-items:center;justify-content:space-between;flex-wrap:nowrap;gap:8px;padding:22px 14px 12px 24px;box-sizing:border-box}
.模态题{margin:0;font-size:16px;line-height:24px;font-weight:500;color:var(--dsw-alias-label-primary)}
button.q-btn.模态关{width:28px;height:28px;min-width:28px;min-height:28px;padding:0;border-radius:var(--dsw-radius-sm);background:transparent !important;box-shadow:none !important;color:var(--dsw-alias-label-secondary) !important}
button.q-btn.模态关:hover{background:var(--dsw-alias-interactive-bg-hover) !important}
.模态述{margin:0;padding:0 24px;font-size:14px;line-height:22px;color:var(--dsw-alias-label-primary)}
.模态体{width:100%;min-width:0;margin-top:20px;padding:0 24px;box-sizing:border-box}
.模态脚{width:100%;align-items:center;justify-content:flex-end;flex-wrap:nowrap;gap:8px;padding:0 24px;box-sizing:border-box}
'''

保持毫秒=0#无自动关闭

样式已登记=False

def 登记样式():
    '同一段样式整个进程只登记一次'
    global 样式已登记
    if 样式已登记 is True:
        return
    界面.add_css(样式表)
    样式已登记=True

class 模态:#全视口对话框
    '受控打开；关则返回 None'
    def __init__(自身,属性=None,**关键字参数):
        '合并 props'
        自身.属性=dict(属性 if 属性 is not None else {})#基础
        自身.属性.update(关键字参数)#覆盖

    def 更新(自身,属性):
        '刷新'
        自身.属性=dict(属性)#最新

    def 渲染(自身):
        '打开时画出标题、正文和页脚'
        登记样式()
        属性=自身.属性#props
        打开=属性['open'] is True if 'open' in 属性 else False#开
        if 打开 is False:#关
            return None#不画
        无头=属性['headless'] is True if 'headless' in 属性 else False#无铬
        标题=属性['title'] if 'title' in 属性 else ''#标题
        if 标题 is None:#缺
            标题=''#空
        关文=属性['closeLabel'] if 'closeLabel' in 属性 else 'Close'#关按钮
        if 关文 is None or 关文=='':#缺
            关文='Close'#默认
        说明=属性['description'] if 'description' in 属性 else None#说明
        子=属性['children'] if 'children' in 属性 else None#体
        脚=属性['footer'] if 'footer' in 属性 else None#脚
        关闭=属性['onClose'] if 'onClose' in 属性 else None#关闭
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
        with 界面.dialog() as 对话框:#遮罩
            卡=界面.card().classes('模态')#卡
            类名=属性['className'] if 'className' in 属性 else None#卡类
            if isinstance(类名,str) and 类名!='':
                卡.classes(类名)#附
            with 卡:#内容
                内容类=属性['contentClassName'] if 'contentClassName' in 属性 else None#内容类
                体=界面.column()#体
                if isinstance(内容类,str) and 内容类!='':
                    体.classes(内容类)#附
                with 体:#正文区
                    if 无头 is False:
                        with 界面.row().classes('模态头'):#头
                            if isinstance(标题,str) and 标题!='':#标题
                                界面.label(标题).classes('模态题')#标题
                            elif hasattr(标题,'渲染'):#组件标题
                                标题.渲染()#自画
                            def 点关():
                                '调用关闭'
                                if 关闭 is not None:
                                    关闭()#调用
                            界面.button(关文,on_click=点关).props('flat dense no-caps').classes('模态关')#关闭
                        if isinstance(说明,str) and 说明!='':#说明
                            界面.label(说明).classes('模态述')#说明
                        elif 说明 is not None and hasattr(说明,'渲染'):#组件说明
                            说明.渲染()#自画
                    with 界面.column().classes('模态体'):#正文
                        画子(子)#正文
                    if 脚 is not None:
                        with 界面.row().classes('模态脚'):#脚
                            画子(脚)#页脚
        对话框.props('persistent')#只走关闭按钮
        对话框.open()#打开

    def __call__(自身,属性=None,**关键字参数):
        '对齐 React'
        if 属性 is not None or len(关键字参数)>0:#有；判 length
            合并=dict(属性 if 属性 is not None else {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()
