from nicegui import ui as 界面
from ...ui_插件设置.字段 import 取值字段,画出设置表单,样式表 as 表单样式
from .文案 import 表单标签

__all__=['终端卡片']

界面.add_css(表单样式,shared=True)

class 终端卡片:
    '命令超时与单流输出上限页'
    def __init__(自身,属性):
        '记下 props。槽位只调用构造，键齐了就画。'
        自身.属性=属性
        if isinstance(属性,dict) and 't' in 属性 and 'view' in 属性 and 'useShellCard' in 属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新'
        自身.属性=属性

    def 渲染(自身):
        '摘要或表单'
        翻译=自身.属性['t']
        def 全量(快照):
            '整份卡片快照'
            return 快照
        状态=自身.属性['useShellCard'](全量)
        if 自身.属性['view']=='summary':
            界面.label(翻译('description'))
            return
        禁用=not 状态.get('writable')
        def 改超时(文):
            '草稿原样交给数字字段，斜杠不当成命令'
            自身.属性['edit']('timeoutMs',文)
        def 复超时():
            '恢复超时默认'
            自身.属性['resetField']('timeoutMs')
        def 改上限(文):
            '草稿原样交给数字字段，斜杠不当成命令'
            自身.属性['edit']('maxOutputBytes',文)
        def 复上限():
            '恢复输出上限默认'
            自身.属性['resetField']('maxOutputBytes')
        def 画控件():
            '超时与单流输出上限'
            取值字段({
                'id':'plugin-config-shell-timeout',
                'label':翻译('timeoutMs'),
                'hint':翻译('timeoutMsHint'),
                'overriddenLabel':翻译('overridden'),
                'resetLabel':翻译('reset'),
                'invalidLabel':翻译('invalidNumber'),
                'numeric':True,
                'disabled':禁用,
                **状态['timeoutMs'],
                'onEdit':改超时,
                'onReset':复超时,
            }).渲染()
            取值字段({
                'id':'plugin-config-shell-output',
                'label':翻译('maxOutputBytes'),
                'hint':翻译('maxOutputBytesHint'),
                'overriddenLabel':翻译('overridden'),
                'resetLabel':翻译('reset'),
                'invalidLabel':翻译('invalidNumber'),
                'numeric':True,
                'disabled':禁用,
                **状态['maxOutputBytes'],
                'onEdit':改上限,
                'onReset':复上限,
            }).渲染()
        画出设置表单(表单标签(翻译),状态,自身.属性.get('discard'),自身.属性['save'],画控件)

    def __call__(自身,属性=None):
        '对齐 React 调用'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
