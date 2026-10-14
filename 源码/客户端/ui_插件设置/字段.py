from nicegui import ui as 界面

__all__=['取值字段','密钥字段','样式表','画出设置表单']

样式表='''
.settings-form{display:flex;flex-direction:column;width:100%}
.settings-readonly,.settings-unavailable{margin:0 0 12px;font-size:12px;line-height:1.5;color:var(--dsw-alias-label-tertiary)}
.settings-footer{display:flex;align-items:center;gap:8px;width:100%;padding-top:16px;flex-wrap:nowrap}
.settings-failed{flex:1;min-width:0;margin:0;font-size:12px;line-height:1.5;color:var(--dsw-alias-label-error)}
button.q-btn.保存钮{margin-left:auto;height:auto;min-height:0;padding:5px 14px;border-radius:var(--dsw-radius-md);background:var(--dsw-alias-label-primary) !important;color:var(--dsw-alias-bg-layer-3) !important;box-shadow:none !important;font-size:13px;line-height:1.5}
button.q-btn.保存钮:disabled{opacity:0.4}
.字段{display:flex;flex-direction:column;gap:6px;width:100%;padding:12px 0}
.字段+.字段{border-top:0.5px solid var(--dsw-alias-border-l2)}
.字段头{display:flex;align-items:center;gap:8px;width:100%;flex-wrap:nowrap}
.字段签{flex:1;min-width:0;font-size:13px;font-weight:500;line-height:1.5;color:var(--dsw-alias-label-primary)}
.字段徽{font-size:12px;line-height:1.5;color:var(--dsw-alias-label-secondary)}
button.q-btn.字段复位{height:auto;min-height:0;padding:0;background:none !important;box-shadow:none !important;color:var(--dsw-alias-label-secondary) !important;font-size:12px;line-height:1.5}
button.q-btn.字段复位:hover{color:var(--dsw-alias-label-primary) !important}
.字段框{width:100%}
.字段框 .q-field__control{height:34px;min-height:34px;padding:0 12px;border:0.5px solid var(--dsw-alias-border-l4);border-radius:var(--dsw-radius-md);background:var(--dsw-alias-bg-layer-3);box-shadow:none}
.字段框 .q-field__control:before,.字段框 .q-field__control:after{display:none}
.字段非法{margin:0;font-size:12px;line-height:1.5;color:var(--dsw-alias-state-error-primary)}
.字段提示{margin:0;font-size:12px;line-height:1.5;color:var(--dsw-alias-label-tertiary)}
'''
界面.add_css(样式表,shared=True)

class 取值字段:#暂存值字段
    'numeric 仅提示键盘；是否合法由规格判定，控件不改写键入'
    def __init__(自身,属性):#构造
        '记下 props'
        自身.属性=属性#合成 props

    def 更新(自身,属性):#props 变更
        '刷新'
        自身.属性=属性#最新

    def 渲染(自身):#结构化视图
        '标签、覆盖徽章、输入与提示'
        属性=自身.属性#props
        非法=bool(属性['invalid']) if 'invalid' in 属性 else False#非法
        覆盖=bool(属性['overridden']) if 'overridden' in 属性 else False#覆盖
        文本=属性['text'] if 'text' in 属性 else ''#草稿文本
        占位=属性['placeholder'] if 'placeholder' in 属性 else ''#占位
        禁用=bool(属性['disabled']) if 'disabled' in 属性 else False#禁用
        with 界面.column().classes('字段'):
            with 界面.row().classes('字段头'):
                标签=属性['label'] if 'label' in 属性 else None#标签
                if 标签 is not None:
                    界面.label(标签).classes('字段签')
                if 覆盖 and 'overriddenLabel' in 属性 and 属性['overriddenLabel'] is not None:
                    界面.label(属性['overriddenLabel']).classes('字段徽')
                if 覆盖 and 'onReset' in 属性 and 属性['onReset'] is not None and 'resetLabel' in 属性:
                    def 点复位():
                        '复位该字段'
                        属性['onReset']()
                    复位钮=界面.button(属性['resetLabel'], on_click=点复位).props('flat no-caps').classes('字段复位')
                    if 禁用:
                        复位钮.disable()
            def 改文(事件):
                '把键入交给编辑'
                编辑=属性['onEdit'] if 'onEdit' in 属性 else None
                if 编辑 is not None:
                    编辑(事件.value)
            属性串='borderless dense'
            if 属性.get('numeric') is True:
                属性串+=' inputmode=numeric'
            标识=属性.get('id')
            if isinstance(标识,str) and len(标识)>0:
                属性串+=' id='+标识
            if 非法:
                属性串+=' aria-invalid=true'
            框=界面.input(value=文本, placeholder=占位, on_change=改文).classes('字段框').props(属性串)
            if 禁用:
                框.disable()
            if 非法 and 'invalidLabel' in 属性:
                界面.label(属性['invalidLabel']).classes('字段非法')
            elif 'hint' in 属性 and 属性['hint'] is not None:
                界面.label(属性['hint']).classes('字段提示')

    def __call__(自身,属性=None):#组件调用形
        '对齐 React 调用'
        if 属性 is not None:
            自身.更新(属性)#刷新
        return 自身.渲染()

class 密钥字段:#只写凭证控件
    '响应从不带回值；空白草稿不写，保留已存密钥'
    def __init__(自身,属性):#构造
        '记下 props'
        自身.属性=属性#合成 props

    def 更新(自身,属性):#props 变更
        '刷新'
        自身.属性=属性#最新

    def 渲染(自身):#结构化视图
        '标签、已配徽章、密码输入与提示'
        属性=自身.属性#props
        已配=bool(属性['configured']) if 'configured' in 属性 else False#已配置
        文本=属性['text'] if 'text' in 属性 else ''#草稿
        禁用=bool(属性['disabled']) if 'disabled' in 属性 else False#禁用
        with 界面.column().classes('字段'):
            with 界面.row().classes('字段头'):
                标签=属性['label'] if 'label' in 属性 else None
                if 标签 is not None:
                    界面.label(标签).classes('字段签')
                if 'stateLabel' in 属性 and 属性['stateLabel'] is not None:
                    界面.label(属性['stateLabel']).classes('字段徽')
            def 改文(事件):
                '草稿含空白都交给编辑；是否写入由保存时决定'
                编辑=属性['onEdit'] if 'onEdit' in 属性 else None
                if 编辑 is not None:
                    编辑('' if 事件.value is None else 事件.value)
            属性串='borderless dense autocomplete=new-password'
            标识=属性.get('id')
            if isinstance(标识,str) and len(标识)>0:
                属性串+=' id='+标识
            框=界面.input(value=文本, password=True, on_change=改文).classes('字段框').props(属性串)
            if 禁用:
                框.disable()
            if 'hint' in 属性 and 属性['hint'] is not None:
                界面.label(属性['hint']).classes('字段提示')

    def __call__(自身,属性=None):#组件调用形
        '对齐 React 调用'
        if 属性 is not None:
            自身.更新(属性)#刷新
        return 自身.渲染()

def 挂离开丢弃(容器,丢弃):
    '元素删除时丢掉暂存，只调用一次'
    if 丢弃 is None:
        return
    容器._丢弃=丢弃
    原删除=容器._handle_delete
    def 删除():
        回调=容器._丢弃
        容器._丢弃=None
        if 回调 is not None:
            回调()
        原删除()
    容器._handle_delete=删除

def 画出设置表单(标签,状态,丢弃,保存,画控件):
    '未服务时只留说明；只读提示在控件前；离开页面丢掉暂存'
    壳=界面.column().classes('settings-form')
    挂离开丢弃(壳,丢弃)
    with 壳:
        if 'available' in 状态 and 状态['available'] is not True:
            界面.label(标签['unavailable']).classes('settings-unavailable')
            return
        if 'writable' in 状态 and 状态['writable'] is not True:
            界面.label(标签['readOnly']).classes('settings-readonly')
        画控件()
        保存中=bool(状态.get('saving'))
        def 点保存():
            '写入全部暂存'
            保存()
        with 界面.row().classes('settings-footer'):
            if 'failed' in 状态 and 状态['failed'] is True:
                界面.label(标签['saveFailed']).classes('settings-failed')
            存钮=界面.button(标签['saving'] if 保存中 else 标签['save'], on_click=点保存).props('flat no-caps').classes('保存钮')
            未改='dirty' not in 状态 or 状态['dirty'] is not True#缺键与显式未改都不能存
            非法='invalid' in 状态 and 状态['invalid'] is True#显式非法
            if 保存中 or 未改 or 非法:
                存钮.disable()
