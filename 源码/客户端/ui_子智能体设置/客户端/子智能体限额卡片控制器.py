from ...ui_基础界面组件.表单模型 import 设置表单模型,设置数字字段

__all__=['子智能体限额卡片控制器']

安全整数上限=9007199254740991

def 是安全整数(值):
    '与 Number.isSafeInteger 同范围，并排除负零'
    if type(值) is bool:
        return False
    if type(值) is int:
        return -安全整数上限<=值<=安全整数上限
    if type(值) is not float:
        return False
    if 值!=值 or 值==float('inf') or 值==float('-inf'):
        return False
    if 值==0.0 and repr(值).startswith('-'):
        return False
    if not 值.is_integer():
        return False
    return -安全整数上限<=值<=安全整数上限

def 限额字段(字段名,最小):
    '只接受不低于下限的安全整数'
    数字=设置数字字段(字段名)
    原解析=数字['parse']
    def 解析(文本):
        '先走数字解析，再卡整数下限'
        写=原解析(文本)
        if 写 is None or 写.get('kind')!='set':
            return 写
        值=写['value']
        if not 是安全整数(值) or 值<最小:
            return None
        if type(值) is float:
            return {'kind':'set','value':int(值)}
        return 写
    return {**数字,'parse':解析}

class 子智能体限额卡片控制器:
    '把 Host 的 subagent 节接到暂存限额表单'
    def __init__(自身,作用域):
        '绑定深度与并行容量'
        自身.表单=设置表单模型(作用域,[限额字段('maxDepth',0),限额字段('maxActiveSubagents',1)])
        自身.存储=自身.表单.绑定(自身.投影)

    def 投影(自身):
        '外壳叠两个限额字段'
        return {
            **自身.表单.外壳(),
            'maxDepth':自身.表单.字段('maxDepth'),
            'maxActiveSubagents':自身.表单.字段('maxActiveSubagents'),
        }

    def 注入(自身):
        '槽位登记用的快照与动作'
        return {'hooks':{'subagentLimitsCard':自身.存储},**自身.表单.动作()}

    def 拆除(自身):
        '释放已接受值订阅'
        自身.表单.拆除()
