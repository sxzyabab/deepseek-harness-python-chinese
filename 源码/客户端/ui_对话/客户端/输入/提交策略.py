'撰写器提交策略。忙碌回车偏好在这里，投递窗口仍归宿主和智能体'
from ....存储 import 创建快照存储
from ...提交设置 import 忙碌回车字段,默认忙碌回车行为

__all__=['解析提交方式','提交策略','默认忙碌回车行为']

def 解析提交方式(偏好,运行中,手势,可插话):
    '空闲或不能插话时一律排队。回车用手势偏好，加速键用另一行为'
    if (not 运行中) or (not 可插话):
        return 'queue'
    if 手势=='enter':
        return 偏好
    if 偏好=='queue':
        return 'steer'
    return 'queue'

class 提交策略:
    '设置行和撰写器栏共用的忙碌回车偏好'
    def __init__(自身,宿主=None):
        '有配置表就订阅并采用当前值'
        自身.忙碌回车=创建快照存储(默认忙碌回车行为)
        自身.宿主=宿主
        自身.退订=None
        if 宿主 is not None:
            自身.退订=宿主.subscribe(lambda: 自身.采用(宿主))
            自身.采用(宿主)

    def 释放(自身):
        '拆掉偏好订阅'
        if 自身.退订 is not None:
            自身.退订()
            自身.退订=None

    def 设置忙碌回车(自身,行为):
        '先发布活值，再写耐久设置'
        if 自身.忙碌回车.getSnapshot()==行为:
            return
        自身.忙碌回车.set(行为)
        if 自身.宿主 is not None:
            结果=自身.宿主.set(忙碌回车字段,行为)
            if hasattr(结果,'等待'):
                结果.等待()

    def 采用(自身,宿主):
        '采用作用域里已接受的耐久值，不写回'
        节=宿主.getSnapshot()['value']
        if 节 is None:
            return
        if 自身.忙碌回车.getSnapshot()==节['busyEnter']:
            return
        自身.忙碌回车.set(节['busyEnter'])

    @property
    def busyEnter(自身):
        '登记面仍用上游字段名'
        return 自身.忙碌回车

    def setBusyEnter(自身,行为):
        '登记面仍用上游方法名'
        自身.设置忙碌回车(行为)

    def dispose(自身):
        '登记面仍用上游方法名'
        自身.释放()
