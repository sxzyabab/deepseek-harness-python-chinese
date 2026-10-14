import importlib.resources as 包资源
from nicegui import ui as 界面
from .轨迹记录 import 格式化已用秒数

__all__=['轨迹格','种类标签','样式表','样式文件']

样式文件='轨迹格.module.css'

def _读样式(文件名):
    '读当前包内样式。失败时异常文案只有样式读不到，不含路径'
    try:
        return 包资源.files(__package__).joinpath(文件名).read_text(encoding='utf-8')
    except Exception:
        raise OSError('样式读不到') from None

样式表=_读样式(样式文件)
界面.add_css(样式表,shared=True)

种类标签={
    'system':'System','user':'User','context':'Context','compacted':'Compacted',
    'message':'Message','tool':'Tool','subtool':'Sub',
}

标签类={
    'system':'tagSystem','user':'tagUser','context':'tagContext','compacted':'tagSystem',
    'message':'tagMessage','tool':'tagTool','subtool':'tagSubtool',
}

class 轨迹格:
    '一步轨迹格。父级调用渲染，构造时不画'
    def __init__(自身,属性=None):
        '记下 props'
        自身.属性=属性 if 属性 is not None else {}

    def 更新(自身,属性):
        '换成新的 props'
        自身.属性=属性 if 属性 is not None else {}

    def 渲染(自身):
        '画出一步格。消息种类才显示输入、输出和思考'
        p=自身.属性
        种类=p['kind'] if 'kind' in p else 'message'
        选中=bool(p['selected']) if 'selected' in p else False
        显示指标=种类=='message'
        标签=种类标签[种类] if 种类 in 种类标签 else 种类
        类名=标签类[种类] if 种类 in 标签类 else None
        文本=p['text'] if 'text' in p else ''
        with 界面.row().classes('trajectory-cell selected' if 选中 else 'trajectory-cell'):
            界面.label(标签).classes(类名 if 类名 is not None else '')
            if 文本!='':
                界面.label(文本)
            if 显示指标:
                界面.label(str(p['input'] if 'input' in p else ''))
                界面.label(str(p['output'] if 'output' in p else ''))
                界面.label(str(p['think'] if 'think' in p else ''))
            界面.label(格式化已用秒数(p['timeSeconds'] if 'timeSeconds' in p else None))

    def __call__(自身,属性=None):
        '有新 props 先更新，再画出'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
