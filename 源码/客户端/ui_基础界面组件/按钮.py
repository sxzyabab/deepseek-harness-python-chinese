from nicegui import ui as 界面

__all__=['按钮','变体表','尺寸表','样式表']#仅中文公开名

样式表='''
button.q-btn.按钮{box-sizing:border-box;display:inline-flex;align-items:center;justify-content:center;gap:4px;height:36px;min-height:36px;padding:0 14px;border:none;border-radius:var(--dsw-radius-md);background:transparent !important;box-shadow:none !important;color:var(--dsw-alias-label-primary) !important;font-size:14px;line-height:22px}
button.q-btn.按钮.sm{height:28px;min-height:28px;font-size:12px;line-height:18px;padding:0 10px;border-radius:var(--dsw-radius-sm)}
button.q-btn.按钮.primary{background:var(--dsw-alias-button-primary-fill) !important;color:var(--dsw-alias-label-primary-foreground) !important}
button.q-btn.按钮.primary:hover{background:var(--dsw-alias-button-primary-hover) !important}
button.q-btn.按钮.ghost:hover{background:var(--dsw-alias-interactive-bg-hover) !important}
button.q-btn.按钮.outline{border:0.5px solid var(--dsw-alias-border-l3) !important}
button.q-btn.按钮.outline:hover{background:var(--dsw-alias-interactive-bg-hover) !important}
button.q-btn.按钮.toolbar{background:var(--dsw-alias-button-tool-bar-fill) !important}
button.q-btn.按钮.toolbar:hover{background:var(--dsw-alias-button-tool-bar-hover) !important}
button.q-btn.按钮:disabled{opacity:0.4}
.按钮.行钮{display:inline-flex;align-items:center;justify-content:center;gap:4px;height:36px;padding:0 14px;border-radius:var(--dsw-radius-md);cursor:pointer}
'''

变体表=('primary','ghost','outline','toolbar')#视觉变体
尺寸表=('md','sm')#尺寸

样式已登记=False

def 登记样式():
    '同一段样式整个进程只登记一次'
    global 样式已登记
    if 样式已登记 is True:
        return
    界面.add_css(样式表)
    样式已登记=True

class 按钮:#按钮原子
    '画出按钮、图标和子内容'
    def __init__(自身,属性=None,**关键字参数):#构造
        '合并 props'
        自身.属性=dict(属性 or {})#基础
        自身.属性.update(关键字参数)#覆盖

    def 更新(自身,属性):#props 变更
        '刷新'
        自身.属性=dict(属性)#最新

    def 渲染(自身):#画出按钮
        '按变体和尺寸画出按钮、图标和子内容'
        登记样式()
        变体=自身.属性.get('variant','ghost')#变体
        尺寸=自身.属性.get('size','md')#尺寸
        if 变体 not in 变体表:#非法
            变体='ghost'#退回
        if 尺寸 not in 尺寸表:#非法
            尺寸='md'#退回
        子=自身.属性.get('children')#子内容
        点击=自身.属性.get('onClick')#点击
        禁用=bool(自身.属性.get('disabled'))#禁用
        图标=自身.属性.get('icon')#图标
        图标名=None#材料图标名
        if isinstance(图标,str) and 图标!='':
            尾=图标.rsplit('-',1)[-1]#尺寸后缀
            图标名=图标.rsplit('-',1)[0] if 尾.isdigit() else 图标#去掉尺寸后缀
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
        def 点下():
            '有点击回调就调用'
            if 点击 is not None:
                点击()#调用
        文案=None#按钮文字
        if isinstance(子,str):#字面
            文案=子#用
        elif isinstance(子,(list,tuple)) and all(isinstance(项,str) for 项 in 子):#全是字
            文案=''.join(子)#拼
        类名=自身.属性.get('className')#附加类
        类串='按钮 '+变体+' '+尺寸#基础类
        if isinstance(类名,str) and 类名!='':
            类串=类串+' '+类名#附
        if isinstance(文案,str) or 子 is None:#文字或空按钮
            钮=界面.button('' if 文案 is None else 文案,on_click=点下 if 点击 is not None else None,icon=图标名)#按钮
            钮.classes(类串)#类
            if 禁用:#禁用
                钮.props('disable')#禁
            return
        行=界面.row().classes(类串)#组件子内容
        if 点击 is not None and 禁用 is False:#可点
            行.on('click',点下)#点击
        with 行:#内容
            if 图标名 is not None:#图标
                界面.icon(图标名)#图
            画子(子)#子内容

    def __call__(自身,属性=None,**关键字参数):#组件调用形
        '对齐 React 调用'
        if 属性 is not None or 关键字参数:
            合并=dict(属性 or {})#基础
            合并.update(关键字参数)#覆盖
            自身.更新(合并)#刷新
        return 自身.渲染()
