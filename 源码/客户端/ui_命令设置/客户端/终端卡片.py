from ...ui_插件设置.字段 import 取值字段
from .文案 import 表单标签

__all__=['终端卡片']

class 终端卡片:
    """命令超时与单流输出上限页。"""
    def __init__(自身,属性):
        """记下 props。"""
        自身.属性=属性

    def 更新(自身,属性):
        """刷新。"""
        自身.属性=属性

    def 渲染(自身):
        """摘要或表单。"""
        翻译=自身.属性['t']
        def 全量(快照):
            """整份卡片快照。"""
            return 快照
        状态=自身.属性['useShellCard'](全量)
        if 自身.属性['view']=='summary':
            return 翻译('description')
        禁用=not 状态['writable']
        def 改超时(文):
            """改超时草稿。"""
            自身.属性['edit']('timeoutMs',文)
        def 复超时():
            """恢复超时默认。"""
            自身.属性['resetField']('timeoutMs')
        def 改上限(文):
            """改输出上限草稿。"""
            自身.属性['edit']('maxOutputBytes',文)
        def 复上限():
            """恢复输出上限默认。"""
            自身.属性['resetField']('maxOutputBytes')
        控件=[
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
            })(),
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
            })(),
        ]
        return {
            'type':'settings-form',
            'labels':表单标签(翻译),
            'state':状态,
            'onSave':自身.属性['save'],
            'onDiscard':自身.属性['discard'],
            'children':控件,
        }

    def __call__(自身,属性=None):
        """对齐 React 调用。"""
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
