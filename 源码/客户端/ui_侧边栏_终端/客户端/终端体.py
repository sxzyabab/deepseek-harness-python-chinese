import importlib.resources as 包资源
from nicegui import ui as 界面
from ..异常 import 去掉敏感,页面失败文案
from .终端图标 import 终端引导图标

__all__=['终端体','终端屏幕','适配屏幕']

def _读样式():
    '读同目录画面样式。打不开时只报样式读不到，不含路径'
    try:
        return 包资源.files(__package__).joinpath('终端体.module.css').read_text(encoding='utf-8')
    except OSError:
        raise OSError('样式读不到') from None

样式表=_读样式()
界面.add_css(样式表,shared=True)

def _引号(文本):
    '放进属性时转掉引号和尖括号'
    return str(文本).replace('&','&amp;').replace('"','&quot;').replace('<','&lt;')

def _键齐(属性):
    '页签、终端、模型、文案、主题都在才画'
    return isinstance(属性,dict) and 'useTabInfo' in 属性 and 'useTerminal' in 属性 and 'view' in 属性 and 't' in 属性 and 'useTheme' in 属性

def 适配屏幕(仿真,适配,状态,模型):
    '按视口与环境上限调整列行'
    尺寸=适配.proposeDimensions()
    环境=状态['environment'] if isinstance(状态,dict) and 'environment' in 状态 else None
    if 尺寸 is None or 环境 is None:
        return
    列=min(尺寸['cols'],环境['maxCols'])
    行=min(尺寸['rows'],环境['maxRows'])
    if 列<2 or 行<1:
        return
    仿真.resize(列,行)
    模型.resize(列,行)

def _帧文本(状态):
    '从当前帧取出画面字符串'
    渲染帧=状态['render'] if isinstance(状态,dict) and 'render' in 状态 and isinstance(状态['render'],dict) else None
    帧=渲染帧['frame'] if isinstance(渲染帧,dict) and 'frame' in 渲染帧 and isinstance(渲染帧['frame'],dict) else None
    if not isinstance(帧,dict):
        return ''
    if isinstance(帧.get('screen'),str):
        return 帧['screen']
    if isinstance(帧.get('data'),str):
        return 帧['data']
    return ''

def _写入器(模型):
    '模型上的 write，没有则空'
    if 模型 is not None and hasattr(模型,'write') and callable(模型.write):
        return 模型.write
    if isinstance(模型,dict) and 'write' in 模型 and callable(模型['write']):
        return 模型['write']
    return None

class 终端屏幕:
    '挂载仿真器并跟随主题与画面修订'
    def __init__(自身,属性):
        '记下 state、model、visible、label、theme。父组件调用渲染，构造时不画'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 更新(自身,属性):
        '刷新合成 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '画出画面容器、已有帧文本和可写输入'
        属性=自身.属性
        状态=属性['state'] if 'state' in 属性 and isinstance(属性['state'],dict) else {}
        模型=属性['model'] if 'model' in 属性 else None
        标签=属性['label'] if 'label' in 属性 and isinstance(属性['label'],str) else ''
        文本=_帧文本(状态)
        屏=界面.column().classes('dsh-term-screen')
        if 标签!='':
            屏.props('aria-label="'+_引号(标签)+'"')
        写=_写入器(模型)
        with 屏:
            if 文本!='':
                界面.label(文本).style('white-space:pre;font-family:monospace')
            if 状态.get('writable') is True and 写 is not None:
                框=界面.input().props('aria-label="'+_引号(标签)+'"')
                def 发送(写入=写,输入框=框):
                    '把输入写进终端'
                    值=输入框.value if isinstance(输入框.value,str) else ''
                    if 值=='':
                        return
                    写入(值)
                    输入框.set_value('')
                框.on('keydown.enter', lambda _: 发送())

    def __call__(自身,属性=None):
        '有新属性先更新。父组件负责调用渲染，这里不画'
        if 属性 is not None:
            自身.更新(属性)
        return 自身

class 终端体:
    '保留终端加主题与状态条'
    def __init__(自身,属性):
        '记下 props。槽位只调用构造，键齐了就挂上模型并画'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        if _键齐(自身.属性):
            自身._挂上()
            自身.渲染()

    def 更新(自身,属性):
        '刷新合成 props，并重新挂上模型'
        自身.属性=属性 if isinstance(属性,dict) else {}
        if _键齐(自身.属性):
            自身._挂上()

    def _挂上(自身):
        '按当前页签挂上终端模型'
        标签=自身.属性['useTabInfo']()['tab']
        自身.属性['view'](标签['id']).mount()

    def _腾出(自身):
        '清空仍挂着的根。父级已拆掉时丢掉根，并返回要显示的失败句'
        旧=自身.根
        if 旧 is None:
            return None
        try:
            旧.clear()
        except Exception as 错:
            自身.根=None
            return 页面失败文案(错)
        return None

    def 视图(自身):
        '状态条、屏幕与错误的结构。不画子组件。错误说明去掉绝对路径'
        if not _键齐(自身.属性):
            return None
        翻译=自身.属性['t']
        标签=自身.属性['useTabInfo']()['tab']
        模型=自身.属性['view'](标签['id'])
        状态=自身.属性['useTerminal'](标签['id'])
        if 状态 is None:
            return None
        阶段=状态['phase'] if 'phase' in 状态 else None
        信息=状态['info'] if 'info' in 状态 and isinstance(状态['info'],dict) else None
        错误=_错误句(状态,翻译)
        状态文案=_状态文案(状态,翻译)
        结束=_已结束(状态)
        可重试=结束 is not True and (阶段=='failed' or 阶段=='disconnected')
        只读=阶段=='connected' and 信息 is not None and 信息.get('state')=='running' and 状态.get('writable') is not True
        子=[]
        if 状态文案 is not None or 可重试 or 只读 or 结束:
            子.append({'tag':'div','className':'dsh-term-status','role':'status','text':状态文案})
        if 信息 is not None:
            子.append({'tag':'div','className':'dsh-term-screen'})
        if 错误 is not None:
            子.append({'tag':'p','className':'dsh-term-error','role':'alert','text':翻译('failed',{'message':错误})})
        return {
            'tag':'section',
            'className':'dsh-term-root',
            'data-sidebar-terminal':True,
            'model':模型,
            'children':子,
        }

    def 渲染(自身):
        '缺终端空态、状态条、画面文本和可写输入'
        if not _键齐(自身.属性):
            return
        清除失败=自身._腾出()
        if 自身.根 is None:
            自身.根=界面.element('section').classes('dsh-term-root')
            自身.根.props('data-sidebar-terminal')
        属性=自身.属性
        翻译=属性['t']
        标签=属性['useTabInfo']()['tab']
        状态=属性['useTerminal'](标签['id'])
        with 自身.根:
            if isinstance(清除失败,str) and 清除失败!='':
                界面.label(清除失败).classes('dsh-term-error')
            if 状态 is None:
                return
            if 状态.get('issue')=='missingTerminal':
                _画空态(翻译,标签)
                return
            _画状态条(状态,翻译,标签,属性['view'](标签['id']))
            信息=状态['info'] if 'info' in 状态 and isinstance(状态['info'],dict) else None
            if 信息 is not None:
                主题=属性['useTheme'](lambda 值:值)
                可见=标签['visible'] if isinstance(标签,dict) and 'visible' in 标签 else False
                终端屏幕({
                    'state':状态,
                    'model':属性['view'](标签['id']),
                    'visible':可见,
                    'label':翻译('title'),
                    'theme':主题,
                }).渲染()
            错误=_错误句(状态,翻译)
            if 错误 is not None and 错误!='':
                界面.label(翻译('failed',{'message':错误})).classes('dsh-term-error')

    def __call__(自身,属性=None):
        '有新属性先更新，再画出'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()

def _已结束(状态):
    '进程退出或页签已关'
    信息=状态['info'] if isinstance(状态,dict) and isinstance(状态.get('info'),dict) else None
    阶段=状态.get('phase') if isinstance(状态,dict) else None
    if 信息 is not None and 信息.get('state')=='exited':
        return True
    return 阶段=='closed'

def _状态文案(状态,翻译):
    '连接阶段对应的一句状态'
    阶段=状态.get('phase') if isinstance(状态,dict) else None
    信息=状态['info'] if isinstance(状态,dict) and isinstance(状态.get('info'),dict) else None
    if 阶段=='idle' or 阶段=='loading':
        return 翻译('loading')
    if 阶段=='creating' or 阶段=='connecting' or 阶段=='disconnected':
        return 翻译(阶段)
    if 信息 is not None and 信息.get('state')=='exited':
        码=信息['exitCode'] if 'exitCode' in 信息 and 信息['exitCode'] is not None else '—'
        return 翻译('exited',{'code':str(码)})
    if 信息 is not None and 信息.get('state')=='failed':
        return 翻译('unavailable')
    if 阶段=='closed':
        return 翻译('closed')
    return None

def _错误句(状态,翻译):
    '断开时不报错。issue 走文案键，原始错误去掉绝对路径'
    if not isinstance(状态,dict):
        return None
    if 状态.get('phase')=='disconnected':
        return None
    if 'issue' not in 状态 or 状态.get('issue') is None:
        原始=状态['error'] if 'error' in 状态 and 状态['error'] is not None else None
        信息=状态['info'] if isinstance(状态.get('info'),dict) else None
        if 原始 is None and 信息 is not None and 'error' in 信息 and 信息['error'] is not None:
            原始=信息['error']
        if 原始 is None:
            return None
        说明=去掉敏感(原始)
        if 说明=='':
            return None
        return 说明
    return 翻译(状态['issue'])

def _画空态(翻译,标签):
    '终端已不存在时给出说明和新建'
    def 新建():
        '用新终端替换当前页签'
        标签['actions'].openTab('terminal',{'replaceTab':True})
    with 界面.column().classes('dsh-term-empty'):
        终端引导图标({'size':36}).渲染()
        界面.label(翻译('missingTerminal')).classes('dsh-term-empty-msg')
        界面.button(翻译('new'), on_click=新建)

def _画状态条(状态,翻译,标签,模型):
    '状态句、只读接管、重连和结束后的新建'
    阶段=状态.get('phase')
    信息=状态['info'] if isinstance(状态.get('info'),dict) else None
    状态文案=_状态文案(状态,翻译)
    结束=_已结束(状态)
    可重试=结束 is not True and (阶段=='failed' or 阶段=='disconnected')
    只读=阶段=='connected' and 信息 is not None and 信息.get('state')=='running' and 状态.get('writable') is not True
    if 状态文案 is None and 可重试 is not True and 只读 is not True and 结束 is not True:
        return
    def 新建():
        '用新终端替换当前页签'
        标签['actions'].openTab('terminal',{'replaceTab':True})
    with 界面.row().classes('dsh-term-status'):
        if isinstance(状态文案,str) and 状态文案!='':
            界面.label(状态文案)
        if 只读:
            界面.label(翻译('readonly'))
            界面.button(翻译('control'), on_click=lambda: 模型.connect()).props('flat no-caps')
        if 可重试:
            if 信息 is None:
                文案=翻译('reconnect') if 阶段=='disconnected' else 翻译('retry')
                界面.button(文案, on_click=lambda: 模型.refresh()).props('flat no-caps')
            else:
                界面.button(翻译('reconnect'), on_click=lambda: 模型.connect()).props('flat no-caps')
        if 结束:
            界面.button(翻译('new'), on_click=新建).props('flat no-caps')
