from ...ui_插件设置.字段 import 取值字段

__all__=['子智能体限额字段']

class 子智能体限额字段:
    """深度与容量两个可复位字段。"""
    def __init__(自身,属性):
        """记下 props。"""
        自身.属性=属性

    def 更新(自身,属性):
        """刷新。"""
        自身.属性=属性

    def 渲染(自身):
        """两列限额。"""
        翻译=自身.属性['t']
        状态=自身.属性['state']
        禁用=not 状态['writable'] or 状态['saving']
        def 改深度(文):
            """改深度草稿。"""
            自身.属性['edit']('maxDepth',文)
        def 复深度():
            """恢复深度默认。"""
            自身.属性['resetField']('maxDepth')
        def 改容量(文):
            """改容量草稿。"""
            自身.属性['edit']('maxActiveSubagents',文)
        def 复容量():
            """恢复容量默认。"""
            自身.属性['resetField']('maxActiveSubagents')
        return {
            'type':'subagent-limits-fields',
            'cssModule':'子智能体限额字段.module.css',
            'children':[
                取值字段({
                    'id':'plugin-config-subagent-depth',
                    'label':翻译('subagentMaxDepth'),
                    'help':{
                        'label':翻译('subagentDepthHelpLabel'),
                        'content':[
                            翻译('subagentDepthHelp'),
                            {'0':翻译('subagentDepthZero'),'1':翻译('subagentDepthOne')},
                            翻译('subagentDepthOverride'),
                        ],
                    },
                    'overriddenLabel':翻译('overridden'),
                    'resetLabel':翻译('reset'),
                    'invalidLabel':翻译('subagentDepthInvalid'),
                    'numeric':True,
                    'disabled':禁用,
                    **状态['maxDepth'],
                    'onEdit':改深度,
                    'onReset':复深度,
                })(),
                取值字段({
                    'id':'plugin-config-subagent-capacity',
                    'label':翻译('subagentMaxActive'),
                    'help':{
                        'label':翻译('subagentCapacityHelpLabel'),
                        'content':翻译('subagentCapacityHelp'),
                    },
                    'overriddenLabel':翻译('overridden'),
                    'resetLabel':翻译('reset'),
                    'invalidLabel':翻译('subagentCapacityInvalid'),
                    'numeric':True,
                    'disabled':禁用,
                    **状态['maxActiveSubagents'],
                    'onEdit':改容量,
                    'onReset':复容量,
                })(),
            ],
        }

    def __call__(自身,属性=None):
        """对齐 React 调用。"""
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
