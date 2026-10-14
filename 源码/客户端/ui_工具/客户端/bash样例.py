from nicegui import ui as 界面
from .调用模型 import 派生工具行
from .终端卡模型 import 终端卡模型,终端已失败,终端块文案
from .文案 import 会话命名空间
from ...ui_基础界面组件.终端块 import 终端块

__all__=['bash行','bash工具视图样例','前导态','状态文案']

def 前导态(状态):
    '错误或中止换状态点，其余保留 api 图标'
    if 状态=='error':
        return 'error'
    if 状态=='stopped':
        return 'warning'
    return 'api'

def 状态文案(状态,翻译):
    'ok 为 None'
    if 状态=='running':
        return 翻译('bash.running') if callable(翻译) else 'bash.running'
    if 状态=='error':
        return 翻译('bash.failed') if callable(翻译) else 'bash.failed'
    if 状态=='stopped':
        return 翻译('bash.stopped') if callable(翻译) else 'bash.stopped'
    return None

class bash行:
    '图标加 Bash 描述。槽位只调用构造，键齐了就画'

    def __init__(自身,属性=None):
        '记下 props 与本地展开'
        自身.属性={} if 属性 is None else 属性
        自身.已展开=False
        if isinstance(自身.属性,dict) and ('block' in 自身.属性 or 'phase' in 自身.属性):
            自身.渲染()

    def 更新(自身,属性):
        '刷新 props'
        自身.属性=属性

    def 切换展开(自身):
        '可展开才翻转'
        if not 自身.可展开():
            return
        自身.已展开=not 自身.已展开

    def 会话工作目录(自身):
        'useSessions 选 byId[sessionId].cwd'
        属性=自身.属性
        会话标识=属性['sessionId'] if 'sessionId' in 属性 else None
        用会话=属性['useSessions'] if 'useSessions' in 属性 else None
        if not callable(用会话) or 会话标识 is None:
            return None
        def 取工作目录(表):
            'byId[sessionId].cwd'
            按标识=表['byId'] if 'byId' in 表 else None
            if 按标识 is None or 会话标识 not in 按标识:
                return None
            会话=按标识[会话标识]
            return 会话['cwd'] if 'cwd' in 会话 else None
        return 用会话(取工作目录)

    def 可展开(自身):
        '有终端卡或通用错误体'
        属性=自身.属性
        工具名=属性['toolName'] if 'toolName' in 属性 else None
        块=属性['block'] if 'block' in 属性 else None
        模型=派生工具行(工具名,块)
        终端=终端卡模型(块,自身.会话工作目录())
        态=模型['state']
        通用错=(终端 is None and 态=='error'
                and (模型['body'] is not None or 模型['output'] is not None))
        return 终端 is not None or 通用错

    def 渲染(自身):
        '画出 bash 行与展开后的终端或输入输出'
        属性=自身.属性
        工具名=属性['toolName'] if 'toolName' in 属性 else None
        块=属性['block'] if 'block' in 属性 else None
        翻译=属性['t'] if 't' in 属性 else None
        检查=属性['inspect'] if 'inspect' in 属性 else None
        模型=派生工具行(工具名,块)
        工作目录=自身.会话工作目录()
        终端=终端卡模型(块,工作目录)
        态=模型['state']
        if 态=='ok' and 终端 is not None and 终端已失败(终端):
            态='error'
        通用错=(终端 is None and 模型['state']=='error'
                and (模型['body'] is not None or 模型['output'] is not None))
        可展=终端 is not None or 通用错
        打开=自身.已展开 and 可展
        失败行=模型['errorSummary'] if 模型['state']=='error' else None
        终端描述=终端['description'] if 终端 is not None and 'description' in 终端 else None
        摘要=失败行 if 失败行 is not None else (终端描述 if 终端描述 is not None else 模型['summary'])
        前导='chevron' if 打开 else ('icon-chevron-hover' if 可展 else 前导态(态))
        with 界面.column().classes('bash-sample-row'):
            with 界面.row():
                if 态=='error':
                    界面.icon('error')
                elif 前导=='chevron' or 可展:
                    界面.icon('expand_more' if 打开 else 'chevron_right')
                if isinstance(模型['title'],str) and 模型['title']!='':
                    界面.label(模型['title'])
                if isinstance(摘要,str) and 摘要!='':
                    界面.label(摘要)
                状态文=状态文案(态,翻译)
                if isinstance(状态文,str) and 状态文!='':
                    界面.label(状态文)
                if 可展:
                    界面.button(on_click=自身.切换展开).props('icon=expand_more flat round')
                if 打开 and callable(检查):
                    界面.button(on_click=检查).props('icon=search flat round')
            if 打开 and 终端 is not None:
                卡=终端['card'] if 'card' in 终端 and isinstance(终端['card'],dict) else {}
                载荷=dict(卡)
                if callable(翻译):
                    载荷['labels']=终端块文案(翻译)
                终端块(载荷).渲染()
            elif 打开:
                with 界面.column().classes('进出卡'):
                    if isinstance(模型['body'],str) and 模型['body']!='':
                        with 界面.element('div').classes('进出节'):
                            界面.label('IN').classes('进出标')
                            界面.label(模型['body'])
                    if isinstance(模型['output'],str) and 模型['output']!='':
                        with 界面.element('div').classes('进出节'):
                            界面.label('OUT').classes('进出标')
                            界面.label(模型['output'])

    def __call__(自身,属性=None):
        '有新属性则刷新后渲染'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()

bash工具视图样例={
    'name':'bash-toolview-sample',
    'inject':['slots'],
    'key':'bash',
    'locale':会话命名空间,
    'component':bash行,
}
