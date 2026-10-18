from ..文案 import 中文
from .偏好行 import 偏好行

__all__=['性能用量行']


def 原样(值):
    '整份快照'
    return 值


class 性能用量行:
    '性能与用量的详细程度'
    def __init__(自身,属性):
        '记下设置槽属性并画出这一行'
        自身.属性=属性
        自身.行=None
        自身.根=None
        自身.已订=False
        自身.退订表=[]
        自身.渲染()

    def 选中(自身,值):
        '改详细程度'
        自身.属性['setPerformanceUsage'](值)

    def 渲染(自身):
        '标签用中文表原文'
        属性=自身.属性
        窗口=属性['window']
        模式=属性['usePerformanceUsage'](原样)
        选中键='settings.performance.detailed' if 模式=='detailed' else 'settings.performance.compact'
        行属性={
            'window':窗口,
            'title':中文['settings.performance.title'],
            'description':中文['settings.performance.description'],
            'value':模式,
            'selectedLabel':中文[选中键],
            'options':[
                {'id':'compact','label':中文['settings.performance.compact']},
                {'id':'detailed','label':中文['settings.performance.detailed']},
            ],
            'onSelect':自身.选中,
        }
        if 自身.行 is None:
            if 'parent' in 属性:
                行属性['parent']=属性['parent']
            自身.行=偏好行(行属性)
            自身.根=自身.行.根
        else:
            自身.行.属性=行属性
            自身.行.渲染()
        if not 自身.已订:
            订=getattr(属性['usePerformanceUsage'],'_subscribe',None)
            if callable(订):
                自身.退订表.append(订(自身.渲染))
            自身.已订=True
        return 自身.根
