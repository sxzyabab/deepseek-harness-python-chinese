from nicegui import ui as 界面

__all__=['输入','样式表']#仅中文公开名

样式表='''
.输入{display:inline-flex;align-items:center;gap:6px;height:32px;padding:0 8px;border:0.5px solid var(--dsw-alias-border-l4);border-radius:var(--dsw-radius-md);background:var(--dsw-alias-bg-layer-1)}
.输入:focus-within{border-color:var(--dsw-alias-state-business-primary)}
.输入 .q-icon{width:16px;height:16px;color:var(--dsw-alias-label-tertiary)}
.输入 .q-field{flex:1;min-width:0}
.输入 .q-field__control,.输入 .q-field__native,.输入 .q-field__marginal{min-height:22px;height:22px;background:transparent}
.输入 .q-field__native{font-size:14px;line-height:22px;color:var(--dsw-alias-label-primary)}
.输入 .q-field__native::placeholder{color:var(--dsw-alias-label-dimmed)}
'''

样式已登记=False

def 登记样式():
    '同一段样式整个进程只登记一次'
    global 样式已登记
    if 样式已登记 is True:
        return
    界面.add_css(样式表)
    样式已登记=True

class 输入:#文本输入
    '可选前导图标的单行输入'
    def __init__(自身,属性=None,**关键字参数):
        '合并 props'
        自身.属性=dict(属性 if 属性 is not None else {})#基础
        自身.属性.update(关键字参数)#覆盖

    def 更新(自身,属性):
        '刷新'
        自身.属性=dict(属性)#最新

    def 渲染(自身):
        '画出前导图标和单行输入'
        登记样式()
        属性=自身.属性#props
        图标=属性['icon'] if 'icon' in 属性 else None#图标
        值=属性['value'] if 'value' in 属性 and 属性['value'] is not None else ''#值
        占位=属性['placeholder'] if 'placeholder' in 属性 and 属性['placeholder'] is not None else ''#占位
        种类=属性['type'] if 'type' in 属性 and 属性['type'] is not None else 'text'#类型
        禁用=属性['disabled'] is True if 'disabled' in 属性 else False#禁用
        只读=属性['readOnly'] is True if 'readOnly' in 属性 else False#只读
        变更=属性['onChange'] if 'onChange' in 属性 else None#变更
        if 变更 is None and 'onInput' in 属性:#输入回调
            变更=属性['onInput']#改用
        类名=属性['className'] if 'className' in 属性 else None#类
        行=界面.row().classes('输入')#包装
        if isinstance(类名,str) and 类名!='':
            行.classes(类名)#附
        with 行:#内容
            if isinstance(图标,str) and 图标!='':
                尾=图标.rsplit('-',1)[-1]#尺寸后缀
                图标名=图标.rsplit('-',1)[0] if 尾.isdigit() else 图标#去掉尺寸后缀
                界面.icon(图标名)#图
            框=界面.input(value=str(值),placeholder=占位 if 占位!='' else None)#输入
            if 种类=='password':#密码
                框.props('type=password')#密码
            if 禁用 or 只读:#不可改
                框.props('disable' if 禁用 else 'readonly')#禁或只读
            if 变更 is not None:
                def 改了():
                    '把当前文字交给变更回调'
                    变更(框.value)#调用
                框.on_value_change(改了)#监听

    def __call__(自身,属性=None,**关键字参数):
        '对齐 React'
        if 属性 is not None or len(关键字参数)>0:#有；判 length
            合并=dict(属性 if 属性 is not None else {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()
