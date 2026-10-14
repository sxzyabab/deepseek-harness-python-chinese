'参数还没齐时的 Cordis 工具前缀，三张卡共用'

from nicegui import ui as 界面

__all__=['准备行']

图标名={
    'IconCodeOutline16':'code',
    'IconTrashOutline16':'delete',
    'IconStopFill16':'stop',
    'IconCheckOutline16':'check',
    'IconCloseOutline16':'close',
    'IconPlayOutline16':'play_arrow',
    'IconInspectOutline12':'search',
    'IconCordisPluginOutline14':'extension',
}

已登记样式=set()

准备样式='''
.cordis准备{display:flex;align-items:center;min-width:0}
.cordis准备行{display:flex;align-items:center;gap:6px;min-width:0;width:100%}
.cordis准备题{font-size:13px;line-height:20px;color:var(--dsw-alias-label-primary)}
'''
界面.add_css(准备样式,shared=True)
已登记样式.add(准备样式)

def 登记样式(样式):
    '同一段样式整个进程只登记一次'
    if not isinstance(样式,str) or 样式=='' or 样式 in 已登记样式:
        return
    界面.add_css(样式)
    已登记样式.add(样式)

def 画出节点(节点,处理器=None):
    '把结构树画成控件'
    if 节点 is None:
        return
    if isinstance(节点,str):
        if 节点!='':
            界面.label(节点)
        return
    if isinstance(节点,(list,tuple)):
        for 项 in 节点:
            画出节点(项,处理器)
        return
    if not isinstance(节点,dict):
        return
    if 节点.get('visible') is False or ('type' in 节点 and 节点.get('type') is None):
        return
    种类=节点.get('type') or 'div'
    if isinstance(种类,str) and 种类.startswith('Icon'):
        界面.icon(图标名.get(种类,'extension'), size='14px')
        return
    if 种类=='StateDot':
        界面.icon('circle', size='8px')
        return
    子=节点.get('children')
    类名=节点.get('class') or 节点.get('className') or ''
    点击=节点.get('onClick')
    def 执行(事件=None):
        '把 onClick 交给 handlers'
        if callable(点击):
            点击()
            return
        if not isinstance(处理器,dict):
            return
        if isinstance(点击,str):
            函=处理器.get(点击)
            if callable(函):
                函()
        elif isinstance(点击,tuple) and len(点击)>0:
            函=处理器.get(点击[0])
            if callable(函):
                函(*点击[1:])
    if 种类=='button':
        钮=界面.button(on_click=执行 if 点击 is not None else None).props('flat no-caps')
        if 节点.get('disabled'):
            钮.disable()
        if 类名:
            钮.classes(str(类名))
        with 钮:
            画出节点(子,处理器)
        return
    if 种类 in ('pre','CodeBlock'):
        文本=节点.get('code') or ''
        if isinstance(子,list):
            文本=''.join(项 if isinstance(项,str) else '' for 项 in 子)
        elif isinstance(子,str):
            文本=子
        界面.label(文本).style('white-space:pre-wrap;font-family:monospace').classes(str(类名))
        return
    if 种类=='select':
        选项={}
        for 项 in 子 or []:
            if isinstance(项,dict):
                孩子=项.get('children') or []
                文=孩子[0] if 孩子 and isinstance(孩子[0],str) else str(项.get('value') or '')
                选项[项.get('value')]=文
        def 改选(事件):
            '把新值交给 selectPackage 一类处理器'
            if isinstance(点击,tuple) and isinstance(处理器,dict):
                函=处理器.get(点击[0])
                if callable(函):
                    函(*点击[1:],事件.value)
        界面.select(选项, value=节点.get('value'), on_change=改选).props('dense options-dense')
        return
    if 种类=='renderSlot':
        槽=None if not isinstance(处理器,dict) else 处理器.get('renderSlot')
        if callable(槽):
            槽(节点.get('name'), 节点.get('props') or {}, {'entryKey':节点.get('entryKey')})
        else:
            画出节点(节点.get('fallback'),处理器)
        return
    if 种类=='DisclosureRow':
        with 界面.column().classes(str(类名)):
            with 界面.row().classes(str(节点.get('rowClassName') or '')):
                画出节点(节点.get('icon'),处理器)
                题=节点.get('title')
                if isinstance(题,str) and 题!='':
                    界面.label(题).classes(str(节点.get('titleClassName') or ''))
                画出节点(节点.get('collapsedContent'),处理器)
                if not 节点.get('open'):
                    界面.button('展开', on_click=执行).props('flat no-caps')
            if 节点.get('open'):
                画出节点(子,处理器)
        return
    if 种类=='Tooltip':
        画出节点(子,处理器)
        return
    块=界面.column() if 种类 in ('div','section','ul','li','header','label','h3','p','fragment') else 界面.row()
    if 类名:
        块.classes(str(类名))
    with 块:
        文案=节点.get('text')
        if isinstance(文案,str) and 文案!='':
            界面.label(文案)
        画出节点(子,处理器)

def 画出根(树):
    '先写入样式，再画根节点'
    if isinstance(树,dict):
        登记样式(树.get('css'))
    画出节点(树, 树.get('handlers') if isinstance(树,dict) else None)
    return 树

class 准备行:
    '不可展开的准备行：图标、标题，以及进行中标记'
    def __init__(自身,属性=None):
        '记下 props'
        自身.属性={} if 属性 is None else 属性

    def 更新(自身,属性):
        '刷新 props'
        自身.属性={} if 属性 is None else 属性

    def 渲染(自身):
        'data-state 固定为 preparing'
        属性=自身.属性
        翻译=属性['t'] if 属性.get('t') is not None else (lambda 键:键)
        工具名=属性.get('toolName') or ''
        图标=属性.get('icon') or {}
        种类=图标.get('type') if isinstance(图标,dict) else None
        材料=图标名.get(种类,'code')
        卡片类=属性.get('className') or ''
        行类=属性.get('rowClassName') or ''
        题类=属性.get('titleClassName') or ''
        根=界面.element('div').classes('cordis准备 '+卡片类)
        根.props(f'data-tool={工具名} data-state=preparing aria-label="{翻译("a11y.preparing")}"')
        with 根:
            with 界面.row().classes('cordis准备行 '+行类):
                界面.icon(材料, size='14px')
                界面.label(属性.get('title') or '').classes('cordis准备题 '+题类)
                界面.spinner(size='14px')

    def __call__(自身,属性=None):
        '对齐调用'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
