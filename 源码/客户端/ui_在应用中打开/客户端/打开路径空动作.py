'不能预览的文档空态上，用更大的带字按钮打开文件。'
from .打开路径动作 import 文件打开目标

__all__=['打开路径空动作']


class 打开路径空动作:
    '空态上的文件打开菜单，主钮更大并带文字'
    def __init__(自身,属性=None):
        '强制 empty，其余交给文件打开目标'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.目标=None
        自身.根=None
        if 'window' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '换上新的 props，并保持 empty'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 面(自身):
        '带上 empty 的 props'
        面=dict(自身.属性)
        面['empty']=True
        return 面

    def 渲染(自身):
        '画出更大的文件打开按钮'
        面=自身.面()
        if 自身.目标 is None:
            自身.目标=文件打开目标(面)
        else:
            自身.目标.更新(面)
            自身.目标.渲染()
        自身.根=自身.目标.根
        return 自身.根

    def __call__(自身,属性=None):
        '再次交给槽位时刷新'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
