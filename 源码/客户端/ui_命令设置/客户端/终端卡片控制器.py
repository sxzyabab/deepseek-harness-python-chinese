from ...ui_基础界面组件.表单模型 import 设置表单模型,设置数字字段

__all__=['bash命名空间','pwsh命名空间','终端卡片控制器']

bash命名空间='bash-sandbox'
pwsh命名空间='pwsh-sandbox'

class 终端卡片控制器:
    """把一条已组装的终端执行器表单接到本页。"""
    def __init__(自身,作用域):
        """绑定超时与单流上限。"""
        自身.表单=设置表单模型(作用域,[设置数字字段('timeoutMs'),设置数字字段('maxOutputBytes')])
        自身.存储=自身.表单.绑定(自身.投影)

    def 投影(自身):
        """外壳叠两个数字字段。"""
        return {
            **自身.表单.外壳(),
            'timeoutMs':自身.表单.字段('timeoutMs'),
            'maxOutputBytes':自身.表单.字段('maxOutputBytes'),
        }

    def 注入(自身):
        """槽位登记用的快照与动作。"""
        return {'hooks':{'shellCard':自身.存储},**自身.表单.动作()}

    def 拆除(自身):
        """释放表单订阅。"""
        自身.表单.拆除()
