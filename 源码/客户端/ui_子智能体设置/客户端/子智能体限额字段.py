import json
import importlib.resources as 包资源
from nicegui import ui as 界面
from ...ui_插件设置.字段 import 取值字段

__all__=['子智能体限额字段']

def _读样式():
    '读同目录样式并给类名加前缀。失败时异常文案只有样式读不到，不含路径'
    try:
        原文=包资源.files(__package__).joinpath('子智能体限额字段.module.css').read_text(encoding='utf-8')
    except OSError:
        raise OSError('样式读不到') from None
    for 名 in ('depthTable','limits','limit'):
        原文=原文.replace('.'+名,'.subagent-'+名)
    return 原文

界面.add_css(_读样式(),shared=True)

class 子智能体限额字段:
    '深度与容量两个可复位字段'
    def __init__(自身,属性):
        '记下 props。父卡片会调用，构造时不画'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 更新(自身,属性):
        '刷新'
        自身.属性=属性

    def 渲染(自身):
        '两列限额'
        翻译=自身.属性['t']
        状态=自身.属性['state']
        禁用=not 状态['writable'] or 状态['saving']
        def 改深度(文):
            '改深度草稿'
            自身.属性['edit']('maxDepth',文)
        def 复深度():
            '恢复深度默认'
            自身.属性['resetField']('maxDepth')
        def 改容量(文):
            '改容量草稿'
            自身.属性['edit']('maxActiveSubagents',文)
        def 复容量():
            '恢复容量默认'
            自身.属性['resetField']('maxActiveSubagents')
        with 界面.column().classes('subagent-limits'):
            with 界面.column().classes('subagent-limit'):
                取值字段({
                    'id':'plugin-config-subagent-depth',
                    'label':翻译('subagentMaxDepth'),
                    'overriddenLabel':翻译('overridden'),
                    'resetLabel':翻译('reset'),
                    'invalidLabel':翻译('subagentDepthInvalid'),
                    'numeric':True,
                    'disabled':禁用,
                    **状态['maxDepth'],
                    'onEdit':改深度,
                    'onReset':复深度,
                }).渲染()
                界面.label(翻译('subagentDepthHelp'))
                深度表=界面.element('table').classes('subagent-depthTable')
                深度表.props('aria-label='+json.dumps(翻译('subagentDepthHelpLabel'),ensure_ascii=False))
                with 深度表:
                    with 界面.element('tbody'):
                        for 数字,键 in ((0,'subagentDepthZero'),(1,'subagentDepthOne')):
                            with 界面.element('tr'):
                                with 界面.element('th').props('scope=row'):
                                    界面.label(str(数字))
                                with 界面.element('td'):
                                    界面.label(翻译(键))
                界面.label(翻译('subagentDepthOverride'))
            with 界面.column().classes('subagent-limit'):
                取值字段({
                    'id':'plugin-config-subagent-capacity',
                    'label':翻译('subagentMaxActive'),
                    'overriddenLabel':翻译('overridden'),
                    'resetLabel':翻译('reset'),
                    'invalidLabel':翻译('subagentCapacityInvalid'),
                    'numeric':True,
                    'disabled':禁用,
                    **状态['maxActiveSubagents'],
                    'onEdit':改容量,
                    'onReset':复容量,
                }).渲染()
                界面.label(翻译('subagentCapacityHelp'))

    def __call__(自身,属性=None):
        '对齐 React 调用'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
