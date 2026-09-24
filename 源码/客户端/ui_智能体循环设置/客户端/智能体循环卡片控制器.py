from ...ui_基础界面组件.表单模型 import 设置表单模型,设置数字字段

__all__=['智能体循环命名空间','智能体循环卡片控制器']

智能体循环命名空间='agent-loop'

class 智能体循环卡片控制器:
    """把 agent-loop 作用域接到本页暂存表单。"""
    def __init__(自身,作用域):
        """绑定并行上限字段。"""
        自身.表单=设置表单模型(作用域,[设置数字字段('maxParallelToolCalls')])
        自身.存储=自身.表单.绑定(自身.投影)

    def 投影(自身):
        """外壳叠并行上限字段。"""
        return {**自身.表单.外壳(),'maxParallelToolCalls':自身.表单.字段('maxParallelToolCalls')}

    def 注入(自身):
        """槽位登记用的快照与动作。"""
        return {'hooks':{'agentLoopCard':自身.存储},**自身.表单.动作()}

    def 拆除(自身):
        """释放已接受值订阅。"""
        自身.表单.拆除()
