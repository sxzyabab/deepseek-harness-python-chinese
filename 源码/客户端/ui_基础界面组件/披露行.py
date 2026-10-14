from nicegui import ui as 界面

__all__=['披露行','样式表']#仅中文公开名

样式表='''
.披露行{display:flex;flex-direction:column;width:100%;min-width:0}
button.q-btn.披露头{width:100%;height:calc(24px + var(--dsh-content-font-delta,0px));min-height:0;padding:0;justify-content:flex-start;border-radius:var(--dsw-radius-sm);background:transparent !important;box-shadow:none !important;color:var(--dsw-alias-label-tertiary) !important;font-size:var(--dsh-content-font-size-secondary,13px);font-weight:400;line-height:calc(24px + var(--dsh-content-font-delta,0px))}
button.q-btn.披露头 .q-btn__content{justify-content:flex-start;flex-wrap:nowrap}
button.q-btn.披露头:hover{color:var(--dsw-alias-label-secondary) !important;background:transparent !important}
'''

样式已登记=False

def 登记样式():
    '同一段样式整个进程只登记一次'
    global 样式已登记
    if 样式已登记 is True:
        return
    界面.add_css(样式表)
    样式已登记=True

class 披露行:#披露头+受控展开体
    '结构化视图；宿主渲染真实 DOM'
    def __init__(自身,属性=None,**关键字参数):
        '合并 props'
        自身.属性=dict(属性 if 属性 is not None else {})#基础
        自身.属性.update(关键字参数)#覆盖

    def 更新(自身,属性):
        '刷新'
        自身.属性=dict(属性)#最新

    def 渲染(自身):
        '画出标题，打开时画出子内容'
        登记样式()
        属性=自身.属性#props
        可展=属性['expandable'] is True if 'expandable' in 属性 else False#可展
        打开=属性['open'] is True if 'open' in 属性 else False#开
        保持=属性['keepContentWhenOpen'] is True if 'keepContentWhenOpen' in 属性 else False#开时仍画折叠内容
        标题=属性['title'] if 'title' in 属性 else ''#标题
        if 标题 is None:#缺
            标题=''#空
        图标=属性['icon'] if 'icon' in 属性 else None#图标
        折叠=属性['collapsedContent'] if 'collapsedContent' in 属性 else None#折叠侧
        子=属性['children'] if 'children' in 属性 else None#展开子
        切换=属性['onToggle'] if 'onToggle' in 属性 else None#切换
        根=界面.column().classes('披露行')#根
        类名=属性['className'] if 'className' in 属性 else None#根类
        if isinstance(类名,str) and 类名!='':
            根.classes(类名)#附
        态={'开':打开}#本地开合
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
        def 重画():
            '按开合重画'
            根.clear()
            with 根:#内容
                前='▾ ' if 态['开'] else '▸ '#箭头
                行类=属性['rowClassName'] if 'rowClassName' in 属性 else None#行类
                if 可展:#可展
                    def 点切换():
                        '翻转并通知'
                        态['开']=not 态['开']#翻
                        if 切换 is not None:
                            切换()#调用
                        重画()#重画
                    钮=界面.button(前+标题,on_click=点切换).props('flat no-caps align=left').classes('披露头')#标题
                    if isinstance(行类,str) and 行类!='':#行类
                        钮.classes(行类)#附
                elif 标题!='':#仅标题
                    界面.label(标题)#标题
                if isinstance(图标,str) and 图标!='':#图标
                    尾=图标.rsplit('-',1)[-1]#尺寸后缀
                    图标名=图标.rsplit('-',1)[0] if 尾.isdigit() else 图标#去掉尺寸后缀
                    界面.icon(图标名)#图
                if 态['开'] is False or 保持 is True:#折叠侧
                    画子(折叠)#折叠内容
                if 态['开'] is True:#展开
                    画子(子)#子内容
        重画()#首画

    def __call__(自身,属性=None,**关键字参数):
        '对齐 React'
        if 属性 is not None or len(关键字参数)>0:#有；判 length
            合并=dict(属性 if 属性 is not None else {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()
