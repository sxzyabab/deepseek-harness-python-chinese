from nicegui import ui as 界面
from .回退工具卡 import 回退工具卡

__all__=['工具调用树','工具调用枝','工具调用','调用名']

def 调用名(节点):
    '从生命周期任一侧解析工具名'
    if 'kind' in 节点:
        调用=节点['call'] if 'call' in 节点 else None
        名=调用['name'] if 调用 is not None and 'name' in 调用 else None
        return 名 if 名 else ''
    名=节点['name'] if 'name' in 节点 else None
    return 名 if 名 else ''

class 工具调用:
    '单次调用。父组件调用渲染，构造本身不画'

    def __init__(自身,属性=None):
        '记下 props'
        自身.属性={} if 属性 is None else 属性

    def 更新(自身,属性):
        '刷新 props'
        自身.属性=属性

    def 渲染(自身):
        '派发槽；无登记则画回退卡'
        属性=自身.属性
        调用标识=属性['callId'] if 'callId' in 属性 else None
        工具名=属性['toolName'] if 'toolName' in 属性 else None
        块=属性['block'] if 'block' in 属性 else None
        开文件=属性['openFile'] if 'openFile' in 属性 else None
        工作目录=属性['cwd'] if 'cwd' in 属性 else None
        检查调用=属性['inspectCall'] if 'inspectCall' in 属性 else None
        翻译=属性['t'] if 't' in 属性 else None
        渲槽=属性['renderSlot'] if 'renderSlot' in 属性 else None
        选中=bool(属性['selected']) if 'selected' in 属性 else False
        子列表=属性['children'] if 'children' in 属性 else None
        def 检查本调用():
            '转调 inspectCall(callId)'
            return 检查调用(调用标识)
        所有者={
            'callId':调用标识,
            'toolName':工具名,
            'block':块,
            'openFile':开文件,
            'cwd':工作目录,
            'inspect':检查本调用 if callable(检查调用) else None,
        }
        with 界面.column().classes('tool-call-row selected' if 选中 else 'tool-call-row'):
            if callable(渲槽):
                渲槽('tool.call.toolview',所有者,{'entryKey':工具名})
            else:
                卡=回退工具卡()
                载荷=dict(所有者)
                载荷['t']=翻译
                卡.更新(载荷)
                卡.渲染()
            if isinstance(子列表,list):
                for 子 in 子列表:
                    if hasattr(子,'渲染'):
                        子.渲染()

    def __call__(自身,属性=None):
        '有新属性则刷新后渲染'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()

class 工具调用枝:
    '一块调用及其子调用。父组件调用渲染，构造本身不画'

    def __init__(自身,属性=None):
        '记下 props'
        自身.属性={} if 属性 is None else 属性

    def 更新(自身,属性):
        '刷新 props'
        自身.属性=属性

    def 渲染(自身):
        '先画本行，再逐个子调用'
        属性=自身.属性
        块=属性['block']
        选中标识=属性['selectedCallId'] if 'selectedCallId' in 属性 else None
        渲槽=属性['renderSlot'] if 'renderSlot' in 属性 else None
        工作目录=属性['cwd'] if 'cwd' in 属性 else None
        开文件=属性['openFile'] if 'openFile' in 属性 else None
        检查调用=属性['inspectCall'] if 'inspectCall' in 属性 else None
        翻译=属性['t'] if 't' in 属性 else None
        调用标识=块['callId'] if 'callId' in 块 else None
        子调用=块['subCalls'] if 'subCalls' in 块 and 块['subCalls'] is not None else []
        with 界面.column().classes('tool-call-branch'):
            行=工具调用()
            行.更新({
                'renderSlot':渲槽,
                'callId':调用标识,
                'toolName':调用名(块),
                'block':块,
                'openFile':开文件,
                'selected':调用标识==选中标识,
                'cwd':工作目录,
                'inspectCall':检查调用,
                't':翻译,
            })
            行.渲染()
            for 子 in 子调用:
                枝=工具调用枝()
                枝.更新({
                    'renderSlot':渲槽,
                    'block':子,
                    'selectedCallId':选中标识,
                    'cwd':工作目录,
                    'openFile':开文件,
                    'inspectCall':检查调用,
                    't':翻译,
                })
                枝.渲染()

    def __call__(自身,属性=None):
        '有新属性则刷新后渲染'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()

class 工具调用树:
    '槽位只调用构造，键齐了就画'

    def __init__(自身,属性=None):
        '记下 props'
        自身.属性={} if 属性 is None else 属性
        if isinstance(自身.属性,dict) and 'node' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新 props'
        自身.属性=属性

    def 渲染(自身):
        '取 node.data.root 交给调用枝'
        属性=自身.属性
        节点=属性['node'] if 'node' in 属性 else None
        if not isinstance(节点,dict):
            return
        数据=节点['data'] if 'data' in 节点 else None
        根=数据['root'] if 数据 is not None and 'root' in 数据 else None
        if 根 is None:
            return
        枝=工具调用枝()
        with 界面.column().classes('tool-call-tree'):
            枝.更新({
                'renderSlot':属性['renderSlot'] if 'renderSlot' in 属性 else None,
                'block':根,
                'selectedCallId':属性['selectedCallId'] if 'selectedCallId' in 属性 else None,
                'cwd':属性['cwd'] if 'cwd' in 属性 else None,
                'openFile':属性['openFile'] if 'openFile' in 属性 else None,
                'inspectCall':属性['inspectCall'] if 'inspectCall' in 属性 else None,
                't':属性['t'] if 't' in 属性 else None,
            })
            枝.渲染()

    def __call__(自身,属性=None):
        '有新属性则刷新后渲染'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
