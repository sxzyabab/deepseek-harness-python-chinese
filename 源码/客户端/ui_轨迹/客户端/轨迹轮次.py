import importlib.resources as 包资源
from nicegui import ui as 界面

__all__=['轨迹轮次','轨迹轮次头','列标签','轮次样式表','轮次头样式表','轮次样式文件','轮次头样式文件']

轮次样式文件='轨迹轮次.module.css'
轮次头样式文件='轨迹轮次头.module.css'

def _读样式(文件名):
    '读当前包内样式。失败时异常文案只有样式读不到，不含路径'
    try:
        return 包资源.files(__package__).joinpath(文件名).read_text(encoding='utf-8')
    except Exception:
        raise OSError('样式读不到') from None

轮次样式表=_读样式(轮次样式文件)
轮次头样式表=_读样式(轮次头样式文件)
界面.add_css(轮次样式表+'\n'+轮次头样式表,shared=True)

列标签=('Input','Output','Think','Time')

class 轨迹轮次头:
    'Turn N 与 Input、Output、Think、Time。父级调用渲染，构造时不画'
    def __init__(自身,轮次=1):
        '记下 1 基轮次'
        自身.轮次=轮次

    def 渲染(自身):
        '画出轮次头'
        with 界面.row().classes('trajectory-turn-header'):
            界面.label('Turn '+str(自身.轮次))
            for 列 in 列标签:
                界面.label(列)

class 轨迹轮次:
    '粘性头与正文子节点。父级调用渲染，构造时不画'
    def __init__(自身,属性=None):
        '记下 props'
        自身.属性=属性 if 属性 is not None else {}

    def 更新(自身,属性):
        '换成新的 props'
        自身.属性=属性 if 属性 is not None else {}

    def 渲染(自身):
        '画出一轮。子节点自己有渲染才继续画'
        轮=自身.属性['turn'] if 'turn' in 自身.属性 else 1
        子=自身.属性['children'] if 'children' in 自身.属性 else None
        with 界面.column().classes('trajectory-turn'):
            轨迹轮次头(轮).渲染()
            if hasattr(子,'渲染'):
                子.渲染()
            elif isinstance(子,list):
                for 项 in 子:
                    if hasattr(项,'渲染'):
                        项.渲染()

    def __call__(自身,属性=None):
        '有新 props 先更新，再画出'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
