import importlib.resources as 包资源
from nicegui import ui as 界面
from ...ui_插件设置.字段 import 画出设置表单,样式表 as 表单样式
from .文案 import 表单标签
from .子智能体卡片控制器 import 子智能体卡片外壳
from .子智能体限额字段 import 子智能体限额字段
from .子智能体模型选择字段 import 子智能体模型选择字段

__all__=['子智能体卡片']

def _读样式():
    '读同目录样式并给类名加前缀。失败时异常文案只有样式读不到，不含路径'
    try:
        原文=包资源.files(__package__).joinpath('子智能体卡片.module.css').read_text(encoding='utf-8')
    except OSError:
        raise OSError('样式读不到') from None
    for 名 in ('section','heading'):
        原文=原文.replace('.'+名,'.subagent-card-'+名)
    return 原文

界面.add_css(表单样式,shared=True)
界面.add_css(_读样式(),shared=True)

class 子智能体卡片:
    '限额与模型授权收在一次保存里'
    def __init__(自身,属性):
        '记下 props。槽位只调用构造，键齐了就画。'
        自身.属性=属性
        if isinstance(属性,dict) and 't' in 属性 and 'view' in 属性 and 'useSubagentLimitsCard' in 属性 and 'useSubagentModelSelectionCard' in 属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新'
        自身.属性=属性

    def 渲染(自身):
        '摘要或两节表单'
        翻译=自身.属性['t']
        def 全量(快照):
            '整份卡片快照'
            return 快照
        限额=自身.属性['useSubagentLimitsCard'](全量)
        模型=自身.属性['useSubagentModelSelectionCard'](全量)
        if 自身.属性['view']=='summary':
            界面.label(翻译('subagentDescription'))
            return
        状态=子智能体卡片外壳(限额,模型)
        def 画控件():
            '限额节与模型授权节'
            if 限额.get('available'):
                with 界面.column().classes('subagent-card-section'):
                    界面.label(翻译('subagentLimitsTitle')).classes('subagent-card-heading')
                    子智能体限额字段({
                        't':翻译,
                        'state':{**限额,'saving':状态['saving']},
                        'edit':自身.属性['editLimit'],
                        'resetField':自身.属性['resetLimit'],
                    }).渲染()
            if 模型.get('available'):
                with 界面.column().classes('subagent-card-section'):
                    界面.label(翻译('subagentModelSelectionTitle')).classes('subagent-card-heading')
                    子智能体模型选择字段({
                        't':翻译,
                        'state':{**模型,'saving':状态['saving']},
                        'toggleEnabled':自身.属性['toggleEnabled'],
                        'toggleModel':自身.属性['toggleModel'],
                        'retryCatalog':自身.属性['retryCatalog'],
                    }).渲染()
        画出设置表单(表单标签(翻译),状态,自身.属性.get('discard'),自身.属性['save'],画控件)

    def __call__(自身,属性=None):
        '对齐 React 调用'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
