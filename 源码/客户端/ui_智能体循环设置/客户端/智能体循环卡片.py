from ...ui_插件设置.字段 import 取值字段
from .文案 import 表单标签

__all__=['智能体循环卡片']

class 智能体循环卡片:
    """并行工具调用上限页。"""
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
        状态=自身.属性['useAgentLoopCard'](全量)
        if 自身.属性['view']=='summary':
            return 翻译('description')
        字段=状态['maxParallelToolCalls']
        def 点编辑(文):
            """改并行上限草稿。"""
            自身.属性['edit']('maxParallelToolCalls',文)
        def 点复位():
            """恢复默认。"""
            自身.属性['resetField']('maxParallelToolCalls')
        控件=取值字段({
            'id':'plugin-config-agent-loop-parallel',
            'label':翻译('maxParallel'),
            'hint':翻译('maxParallelHint'),
            'overriddenLabel':翻译('overridden'),
            'resetLabel':翻译('reset'),
            'invalidLabel':翻译('invalidNumber'),
            'numeric':True,
            'disabled':not 状态['writable'],
            **字段,
            'onEdit':点编辑,
            'onReset':点复位,
        })()
        return {
            'type':'settings-form',
            'labels':表单标签(翻译),
            'state':状态,
            'onSave':自身.属性['save'],
            'onDiscard':自身.属性['discard'],
            'children':[控件],
        }

    def __call__(自身,属性=None):
        """对齐 React 调用。"""
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
