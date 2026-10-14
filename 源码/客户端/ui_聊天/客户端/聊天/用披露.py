__all__=['用披露','绑定披露','披露席位']

class 披露席位:
    '一份初始折叠的独立披露，无外部订阅'
    def __init__(自身,世代=0):
        '记下重置世代'
        自身.世代=世代
        自身.展开世代=None

    def 是否展开(自身):
        '当前世代是否展开'
        return 自身.展开世代==自身.世代

    def 设展开(自身,打开):
        '显式开合'
        自身.展开世代=自身.世代 if 打开 else None

    def 切换(自身):
        '在开合之间切换'
        自身.展开世代=None if 自身.展开世代==自身.世代 else 自身.世代

def 用披露(世代=0):
    '铸造披露席位'
    return 披露席位(世代)

def 读重置世代(重置源):
    '对象走 getSnapshot；外部字典源走同名键'
    if 重置源 is None:
        return 0
    取=getattr(重置源,'getSnapshot',None)
    if callable(取):
        世代=取()
        return 0 if 世代 is None else 世代
    if isinstance(重置源,dict):
        函数=重置源.get('getSnapshot')
        if callable(函数):
            世代=函数()
            return 0 if 世代 is None else 世代
    return 0

def 绑定披露(重置源):
    '到组件调用前不订阅；每次调用读当前重置世代'
    def 用已绑披露():
        '按重置源世代铸造席位'
        return 用披露(读重置世代(重置源))
    return 用已绑披露
