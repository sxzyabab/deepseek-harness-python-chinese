'提示上方的模组条带：当前绘制，按钮点击发回宿主'
from nicegui import ui as 界面

颜色表=frozenset(('yellow','red','green','cyan','blue','magenta','gray','grey','white','black'))

样式表='''
.模组条带{display:flex;flex-direction:column;gap:2px;padding:6px 10px;border-radius:8px;background:var(--dsw-alias-bg-layer-1,transparent);color:var(--dsw-alias-label-primary);font-family:var(--dsw-font-mono,ui-monospace,monospace);font-size:12px;line-height:18px;white-space:pre-wrap}
.模组盒{display:flex;min-width:0}
.模组钮{font:inherit}
.模组热键{opacity:0.7}
.模组提示{font-size:12px}
'''
界面.add_css(样式表,shared=True)

def 失败说明(错误):
    '失败句去掉绝对路径，其余原文保留'
    if isinstance(错误,BaseException) and len(错误.args)>0:
        原文=str(错误.args[0])
    else:
        原文=str(错误)
    留下=[]
    for 词 in 原文.split():
        去引=词.strip('\'"()[]{}<>')
        统一=去引.replace('\\','/')
        if 统一.startswith('/') or 统一.startswith('~'):
            continue
        if len(统一)>2 and 统一[0].isalpha() and 统一[1]==':' and 统一[2]=='/':
            continue
        留下.append(词)
    说明=' '.join(留下).strip()
    if 说明!='':
        return 说明
    if isinstance(错误,BaseException):
        return type(错误).__name__
    return '失败'

__all__=['条带','节点']

def 取色(值):
    '终端色名；grey 收成 gray'
    if not isinstance(值,str) or 值 not in 颜色表:
        return None
    return 'gray' if 值=='grey' else 值

def 旗标(值):
    '只有真才留下'
    return True if 值 is True else None

def 文本属性(属性):
    'Text 的 data 属性'
    return {
        'data-color':取色(属性.get('color')),
        'data-bold':旗标(属性.get('bold')),
        'data-dim':旗标(属性.get('dimColor')),
        'data-italic':旗标(属性.get('italic')),
        'data-underline':旗标(属性.get('underline')),
    }

def 单位(值):
    '数字按 4 像素一档'
    if isinstance(值,bool) or not isinstance(值,(int,float)):
        return None
    return str(值*4)+'px'

def 盒子样式(属性):
    'Box 的方向、边框和间距'
    样式={}
    水平=单位(属性['paddingX'] if 'paddingX' in 属性 else 属性.get('padding'))
    垂直=单位(属性['paddingY'] if 'paddingY' in 属性 else 属性.get('padding'))
    if 水平 is not None:
        样式['paddingLeft']=水平
        样式['paddingRight']=水平
    if 垂直 is not None:
        样式['paddingTop']=垂直
        样式['paddingBottom']=垂直
    间距=单位(属性.get('gap'))
    if 间距 is not None:
        样式['gap']=间距
    有边框=属性.get('border') is not None and 属性.get('border') is not False
    return {
        'attributes':{
            'data-direction':'row' if 属性.get('flexDirection')=='row' else 'column',
            'data-border':True if 有边框 else None,
            'data-color':取色(属性.get('borderColor')) if 有边框 else None,
        },
        'style':样式,
    }

class 节点:
    '序列化树的一个节点'
    def __init__(自身,属性):
        '记下节点、路径和按下回调'
        自身.属性=属性

    def 视图(自身):
        '字符串、Text、Button 或 Box'
        节点值=自身.属性['node']
        if isinstance(节点值,str):
            return {'种类':'文本','文本':节点值}
        子项=[]
        序号=0
        for 子 in 节点值.get('children') or []:
            子项.append(节点({
                'node':子,
                'path':自身.属性['path']+'.'+str(序号),
                'generation':自身.属性['generation'],
                'pending':自身.属性['pending'],
                'onPress':自身.属性['onPress'],
                'hotkeyLabel':自身.属性['hotkeyLabel'],
            }).视图())
            序号+=1
        if 节点值.get('type')=='Text':
            return {'种类':'文本节点','属性':文本属性(节点值.get('props') or {}),'子项':子项}
        if 节点值.get('type')=='Button':
            道具=节点值.get('props') or {}
            标签=str(道具.get('label'))
            热键=道具.get('hotkey') if isinstance(道具.get('hotkey'),str) else None
            动作号=节点值.get('actionId') or ''
            禁用=道具.get('disabled') is True or 动作号=='' or 自身.属性['pending'] is not None
            return {
                '种类':'按钮',
                '标签':标签,
                '热键':None if 热键 is None else 自身.属性['hotkeyLabel'](热键),
                '禁用':禁用,
                '忙':自身.属性['pending']==动作号,
                '按下':None if 禁用 else (lambda 动作=动作号:自身.属性['onPress'](动作)),
                '子项':子项,
            }
        盒子=盒子样式(节点值.get('props') or {})
        return {'种类':'盒子','属性':盒子['attributes'],'样式':盒子['style'],'子项':子项}

    def 渲染(自身):
        '父级在列里调用；构造时不画'
        画视图(自身.视图(),界面)

class 条带:
    '提示上方的当前模组绘制'
    def __init__(自身,属性):
        '记下按下和条带快照'
        自身.属性=属性
        自身.进行中=None
        自身.提示=None
        自身.渲染()

    def 画面(自身):
        'useBand 或 hooks.band；没有树时不画'
        取=自身.属性.get('useBand')
        if 取 is None:
            存储=(自身.属性.get('hooks') or {}).get('band')
            if 存储 is None:
                return None
            画面=存储.getSnapshot()
        else:
            画面=取(lambda 值:值)
        return 画面

    def 快照(自身):
        '没有树时不画'
        画面=自身.画面()
        if 画面 is None or 画面.get('tree') is None:
            return None
        def 按下(动作号):
            '按下后换成新画面；失败则显示文案'
            自身.进行中=动作号
            自身.提示=None
            def 成功(值=None):
                '结束进行中'
                自身.进行中=None
            def 失败(错误):
                '条带下方显示失败'
                自身.进行中=None
                if isinstance(错误,BaseException) and hasattr(错误,'message'):
                    原文=错误.message
                else:
                    原文=错误
                自身.提示=自身.属性['t']('press.failed',{'message':失败说明(原文)})
            结果=自身.属性['press'](画面['generation'],动作号)
            if hasattr(结果,'然后'):
                结果.然后(成功,失败)
            else:
                成功()
        节点表=[]
        序号=0
        for 项 in 画面['tree']:
            节点表.append(节点({
                'node':项,
                'path':str(序号),
                'generation':画面['generation'],
                'pending':自身.进行中,
                'onPress':按下,
                'hotkeyLabel':lambda 热键:'['+热键+']',
            }))
            序号+=1
        return {
            '标签':自身.属性['t']('band'),
            '代数':画面['generation'],
            '节点':节点表,
            '提示':自身.提示,
        }

    def 渲染(自身):
        '把当前绘制画在输入停靠上；按钮点击发回宿主'
        画面=自身.快照()
        if 画面 is None:
            return
        根=界面.column().classes('模组条带')
        根.props(f'role=group aria-label="{画面["标签"]}" data-generation={画面["代数"]}')
        with 根:
            for 项 in 画面.get('节点') or []:
                项.渲染()
            if 画面.get('提示'):
                界面.label(画面['提示']).classes('模组提示')

    def __call__(自身,属性=None):
        '对齐调用'
        if 属性 is not None:
            自身.属性=属性
        return 自身.渲染()

def 画视图(节点值,界面):
    '文本、按钮或盒子'
    if not isinstance(节点值,dict):
        return
    种类=节点值.get('种类')
    if 种类=='文本':
        界面.label(str(节点值.get('文本') or '')).classes('模组文本')
        return
    if 种类=='文本节点':
        跨=界面.element('span').classes('模组文本')
        for 键,值 in (节点值.get('属性') or {}).items():
            if 值 is None:
                continue
            跨.props(键 if 值 is True else f'{键}={值}')
        with 跨:
            for 子 in 节点值.get('子项') or []:
                画视图(子,界面)
        return
    if 种类=='按钮':
        按下=节点值.get('按下')
        钮=界面.button(节点值.get('标签') or '', on_click=按下 or (lambda:None)).props('flat no-caps').classes('模组钮')
        if 节点值.get('禁用') or 按下 is None:
            钮.disable()
        if 节点值.get('忙'):
            钮.props('loading')
        if 节点值.get('热键'):
            界面.label(str(节点值['热键'])).classes('模组热键')
        for 子 in 节点值.get('子项') or []:
            画视图(子,界面)
        return
    if 种类=='盒子':
        属性=节点值.get('属性') or {}
        容器=界面.row() if 属性.get('data-direction')=='row' else 界面.column()
        容器.classes('模组盒')
        for 键,值 in 属性.items():
            if 值 is None:
                continue
            容器.props(键 if 值 is True else f'{键}={值}')
        样式=节点值.get('样式') or {}
        if 样式:
            容器.style(';'.join(键+':'+str(值) for 键,值 in 样式.items()))
        with 容器:
            for 子 in 节点值.get('子项') or []:
                画视图(子,界面)
