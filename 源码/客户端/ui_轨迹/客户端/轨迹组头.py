import importlib.resources as 包资源
from nicegui import ui as 界面

__all__=['轨迹组头','样式表','样式文件']

样式文件='轨迹组头.module.css'

def _读样式(文件名):
    '读当前包内样式。失败时异常文案只有样式读不到，不含路径'
    try:
        return 包资源.files(__package__).joinpath(文件名).read_text(encoding='utf-8')
    except Exception:
        raise OSError('样式读不到') from None

样式表=_读样式(样式文件)
界面.add_css(样式表,shared=True)

class 轨迹组头:
    '标题与可选次要描述。父级调用渲染，构造时不画'
    def __init__(自身,属性=None):
        '记下 props'
        自身.属性=属性 if 属性 is not None else {}

    def 更新(自身,属性):
        '换成新的 props'
        自身.属性=属性 if 属性 is not None else {}

    def 渲染(自身):
        '画出组头'
        属性=自身.属性
        描述=属性['description'] if 'description' in 属性 else None
        标题=属性['title'] if 'title' in 属性 else None
        with 界面.column().classes('trajectory-group-header'):
            if isinstance(标题,str) and 标题!='':
                界面.label(标题)
            if 描述 is not None and 描述!='':
                界面.label(描述)

    def __call__(自身,属性=None):
        '有新 props 先更新，再画出'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
