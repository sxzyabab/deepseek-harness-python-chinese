from nicegui import ui as 界面
from ..主题设置 import 规范化字体族#提交前收成合法字体列表

__all__=['字体族行','样式表']

样式表='''
.字体族条{display:flex;align-items:center;gap:8px;width:100%;padding:12px 0;border-bottom:0.5px solid var(--dsw-alias-border-l2);flex-wrap:nowrap}
.字体族文{flex:1;min-width:0;display:flex;flex-direction:column;gap:4px;padding-right:24px}
.字体族标题{font-size:14px;font-weight:400;line-height:22px;color:var(--dsw-alias-label-primary)}
.字体族说明{font-size:12px;font-weight:400;line-height:18px;color:var(--dsw-alias-label-tertiary)}
.字体族框{flex:none;width:220px}
.字体族框 .q-field__control{height:36px;min-height:36px;padding:0 12px;border:0.5px solid var(--dsw-alias-border-l4);border-radius:var(--dsw-radius-md);background:var(--dsw-alias-bg-layer-3);box-shadow:none}
.字体族框 .q-field__control:before,.字体族框 .q-field__control:after{display:none}
'''

样式已登记=False

def 登记样式():
    '字体族行样式整个进程只登记一次'
    global 样式已登记
    if 样式已登记 is True:
        return
    界面.add_css(样式表)
    样式已登记=True

class 字体族行:
    '一种角色的字体列表。失焦或回车后规范化再写入，空串恢复内置栈。字体设置组调用渲染，构造不画'
    def __init__(自身,属性):
        '记下角色、写入与 store 钩'
        自身.属性=属性

    def 更新(自身,属性):
        '刷新合成 props'
        自身.属性=属性

    def 当前列表(自身):
        '从 useStore 读该角色已保存的字体列表'
        角色=自身.属性['role']
        def 选取(快照):
            'fontFamilies'
            表=快照.get('fontFamilies') if isinstance(快照,dict) else None
            if isinstance(表,dict) and 角色 in 表:
                return 表[角色]
            return ''
        return 自身.属性['useStore'](选取)

    def 渲染(自身):
        '标题、说明和一格字体名'
        登记样式()
        翻译=自身.属性['t']
        角色=自身.属性['role']
        标题=翻译('fontFamily.'+角色+'.title')
        框=None
        def 提交():
            '规范化后写回输入框和偏好'
            规范=规范化字体族('' if 框.value is None else 框.value)
            框.set_value(规范)
            自身.属性['setFontFamily'](规范)
        def 按键(事件):
            '回车等同失焦。组合输入中的回车不提交'
            if getattr(事件, 'key', None)=='Enter' or (isinstance(事件.args,dict) and 事件.args.get('key')=='Enter'):
                提交()
        with 界面.row().classes('字体族条'):
            with 界面.column().classes('字体族文'):
                界面.label(标题).classes('字体族标题')
                界面.label(翻译('fontFamily.'+角色+'.description')).classes('字体族说明')
            框=界面.input(value=自身.当前列表(), placeholder=翻译('fontFamily.placeholder')).classes('字体族框').props('borderless dense spellcheck=false autocomplete=off maxlength=200 aria-label="'+标题+'"')
            框.on('blur', lambda 事件: 提交())
            框.on('keydown', 按键)

    def __call__(自身,属性=None):
        '对齐组件调用'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
