from .文案 import 表单标签
from .子智能体卡片控制器 import 子智能体卡片外壳
from .子智能体限额字段 import 子智能体限额字段
from .子智能体模型选择字段 import 子智能体模型选择字段

__all__=['子智能体卡片']

class 子智能体卡片:
    """限额与模型授权收在一次保存里。"""
    def __init__(自身,属性):
        """记下 props。"""
        自身.属性=属性

    def 更新(自身,属性):
        """刷新。"""
        自身.属性=属性

    def 渲染(自身):
        """摘要或两节表单。"""
        翻译=自身.属性['t']
        def 全量(快照):
            """整份卡片快照。"""
            return 快照
        限额=自身.属性['useSubagentLimitsCard'](全量)
        模型=自身.属性['useSubagentModelSelectionCard'](全量)
        if 自身.属性['view']=='summary':
            return 翻译('subagentDescription')
        状态=子智能体卡片外壳(限额,模型)
        子=[]
        if 限额.get('available'):
            子.append({
                'type':'section',
                'title':翻译('subagentLimitsTitle'),
                'cssModule':'子智能体卡片.module.css',
                'children':子智能体限额字段({
                    't':翻译,
                    'state':{**限额,'saving':状态['saving']},
                    'edit':自身.属性['editLimit'],
                    'resetField':自身.属性['resetLimit'],
                })(),
            })
        if 模型.get('available'):
            子.append({
                'type':'section',
                'title':翻译('subagentModelSelectionTitle'),
                'cssModule':'子智能体卡片.module.css',
                'children':子智能体模型选择字段({
                    't':翻译,
                    'state':{**模型,'saving':状态['saving']},
                    'toggleEnabled':自身.属性['toggleEnabled'],
                    'toggleModel':自身.属性['toggleModel'],
                    'retryCatalog':自身.属性['retryCatalog'],
                })(),
            })
        return {
            'type':'settings-form',
            'labels':表单标签(翻译),
            'state':状态,
            'onSave':自身.属性['save'],
            'onDiscard':自身.属性['discard'],
            'children':子,
        }

    def __call__(自身,属性=None):
        """对齐 React 调用。"""
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
