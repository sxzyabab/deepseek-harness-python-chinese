from nicegui import ui as 界面
from .轨迹轮次 import 轮次头样式表#加载时已登记样式

__all__=['轨迹轮次头','列标签','轮次头样式表']

列标签=('Input','Output','Think','Time')

class 轨迹轮次头:
    'Turn N 与四列度量标签。父级调用渲染，构造时不画'
    def __init__(自身,属性=None):
        '记下 props'
        自身.属性=属性 if 属性 is not None else {}

    def 更新(自身,属性):
        '换成新的 props'
        自身.属性=属性 if 属性 is not None else {}

    def 渲染(自身):
        '画出粘性轮次栏'
        属性=自身.属性
        轮次=属性['turn'] if 'turn' in 属性 else None
        with 界面.row().classes('trajectory-turn-header'):
            界面.label('Turn '+str(轮次))
            for 列 in 列标签:
                界面.label(列)

    def __call__(自身,属性=None):
        '有新 props 先更新，再画出'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
