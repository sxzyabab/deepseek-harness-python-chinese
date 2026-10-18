from ...ui_基础界面组件.表单模型 import 设置表单模型,设置数字字段

__all__=['子智能体限额卡片控制器']

def 限额字段(字段名,最小):
    '在数字字段上再卡安全整数和下限。负零不接受'
    数字=设置数字字段(字段名)
    原解析=数字['parse']
    def 解析(文本):
        '空草稿清除。非安全整数、低于下限、负零都不接受'
        写=原解析(文本)
        if not isinstance(写,dict) or 写.get('kind')!='set':
            return 写
        值=写['value']
        修剪=文本.strip()
        if type(值) is bool:
            return None
        if 修剪.startswith('-') and 值==0:
            return None
        if type(值) is int:
            安全=-9007199254740991<=值<=9007199254740991
        elif type(值) is float and 值==值 and 值!=float('inf') and 值!=float('-inf') and 值.is_integer():
            安全=-9007199254740991<=值<=9007199254740991
        else:
            return None
        if not 安全 or 值<最小:
            return None
        return 写
    return {**数字,'parse':解析}

class 子智能体限额卡片控制器:
    '把 Host 的 subagent 节接到暂存限额表单'
    def __init__(自身,作用域):
        '绑定深度与并行容量，各自可以单独复位'
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
        '槽位登记用的快照与暂存动作'
        return {'hooks':{'subagentLimitsCard':自身.存储},**自身.表单.动作()}

    def 拆除(自身):
        '释放已接受值订阅'
        自身.表单.拆除()
