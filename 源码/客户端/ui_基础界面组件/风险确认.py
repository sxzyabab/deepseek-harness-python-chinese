from nicegui import ui as 界面
from .模态 import 模态#模态外壳
from .按钮 import 按钮#动作按钮

__all__=['风险确认']#仅中文公开名

样式已登记=False

def 登记样式():
    '同一段样式整个进程只登记一次'
    global 样式已登记
    if 样式已登记 is True:
        return
    界面.add_css('''
.风险确认{width:min(440px,100%);max-height:calc(100dvh - 48px);overflow:hidden}
.风险警告{display:flex;align-items:flex-start;gap:10px;color:var(--dsw-alias-label-secondary);font-size:14px;line-height:22px}
.风险警告 .q-icon{flex:none;margin-top:2px;color:var(--dsw-alias-state-error-primary)}
.风险勾{display:flex;align-items:flex-start;gap:10px;margin-top:20px;color:var(--dsw-alias-label-primary);font-size:14px;line-height:22px}
''')
    样式已登记=True

class 风险确认:#勾选门控确认
    '属主控制 acknowledged；组合模态页脚'
    def __init__(自身,属性=None,**关键字参数):
        '合并 props'
        自身.属性=dict(属性 if 属性 is not None else {})#基础
        自身.属性.update(关键字参数)#覆盖

    def 更新(自身,属性):
        '刷新'
        自身.属性=dict(属性)#最新

    def 渲染(自身):
        '打开时画出说明、勾选和取消确认'
        属性=自身.属性#props
        已认=属性['acknowledged'] is True if 'acknowledged' in 属性 else False#已勾选
        禁用=属性['disabled'] is True if 'disabled' in 属性 else False#禁用
        说明=属性['description'] if 'description' in 属性 else None#说明
        勾文=属性['acknowledgeLabel'] if 'acknowledgeLabel' in 属性 else None#勾选文案
        变更=属性['onAcknowledgedChange'] if 'onAcknowledgedChange' in 属性 else None#变更
        class 确认体:#说明和勾选
            '模态正文'
            def 渲染(自身):
                '画出警告说明和勾选'
                登记样式()
                with 界面.column().classes('风险确认'):#体
                    with 界面.row().classes('风险警告'):#警告行
                        界面.icon('warning')#警告
                        if isinstance(说明,str) and 说明!='':#说明
                            界面.label(说明)#说明
                        elif 说明 is not None and hasattr(说明,'渲染'):#组件
                            说明.渲染()#自画
                    文=勾文 if isinstance(勾文,str) else ''#文案
                    框=界面.checkbox(文,value=已认).classes('风险勾')#勾选
                    if 禁用:#禁用
                        框.props('disable')#禁
                    if 变更 is not None:
                        def 改了():
                            '把勾选结果交给回调'
                            变更(框.value)#调用
                        框.on_value_change(改了)#监听
        取消钮=按钮({#取消
            'variant':'outline','className':'modalAction',
            'onClick':属性['onCancel'] if 'onCancel' in 属性 else None,'children':属性['cancelLabel'] if 'cancelLabel' in 属性 else None,
        })#取消结束
        确认钮=按钮({#确认
            'variant':'primary','className':'confirmAction',
            'disabled':禁用 is True or 已认 is False,
            'onClick':属性['onConfirm'] if 'onConfirm' in 属性 else None,'children':属性['confirmLabel'] if 'confirmLabel' in 属性 else None,
        })#确认结束
        壳=模态({#模态
            'open':属性['open'] if 'open' in 属性 else None,#开
            'onClose':属性['onCancel'] if 'onCancel' in 属性 else None,#关=取消
            'title':属性['title'] if 'title' in 属性 else None,#标题
            'className':'confirmation',#卡类
            'contentClassName':'confirmationContent',#内容类
            'footer':(取消钮,确认钮),#脚
            'children':确认体(),#体
        })#壳结束
        壳.渲染()#模态自己画

    def __call__(自身,属性=None,**关键字参数):
        '对齐 React'
        if 属性 is not None or len(关键字参数)>0:#有；判 length
            合并=dict(属性 if 属性 is not None else {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()
