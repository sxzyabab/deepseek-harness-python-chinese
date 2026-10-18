'一份已接受的偏好驱动全部开发者工具消费方。'

class 已启用源:
    '已接受的 enabled。渲染器按 getSnapshot 和 subscribe 绑定'
    def __init__(自身,取值,订表单):
        '记下读值和表单订阅'
        自身.取值=取值
        自身.订表单=订表单

    def getSnapshot(自身):
        '当前是否启用。还没有接受过的值时为关'
        return 自身.取值()

    def subscribe(自身,监听):
        '值变了才转发'
        先前=[自身.getSnapshot()]

        def 转发():
            '相同则不通知'
            下一=自身.getSnapshot()
            if 下一==先前[0]:
                return
            先前[0]=下一
            监听()

        return 自身.订表单(转发)

class 开发者工具偏好:
    '宿主接受之前，依赖这份偏好的功能保持关闭'
    def __init__(自身,作用域):
        '跟这份命名空间里已接受的 enabled'
        自身.作用域=作用域

        def 取值():
            '已接受节的 enabled。缺席为关'
            值=作用域.getSnapshot().get('value')
            if not isinstance(值,dict) or 'enabled' not in 值:
                return False
            开=值.get('enabled')
            if 开 is None:
                return False
            return 开

        自身.enabled=已启用源(取值,作用域.subscribe)

    def setEnabled(自身,启用):
        '按顺序写到宿主。宿主拒绝则按上游原文抛出'
        if 自身.作用域.set('enabled',启用) is not True:
            raise Exception('Developer tools preference was not saved')
