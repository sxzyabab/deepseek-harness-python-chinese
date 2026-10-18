from ...ui_插件设置.字段 import 取值字段,画出设置表单,跳过离开丢弃
from .文案 import 中文

__all__=['终端卡片']

class 终端卡片:
    '终端执行器的设置页：命令超时与单流输出上限'
    def __init__(自身,属性):
        '记下渲染器交来的 props，并画出这一页'
        自身.属性=属性
        自身.根=None
        自身.已订=False
        自身.退订=None
        自身.绘制中=False
        自身.待重画=False
        自身.上次是表单=False
        自身.渲染()

    def 渲染(自身):
        '摘要是一行说明。其余视图画设置表单。快照变了重画，仍停在表单上时不把重画当成离开页面'
        if 自身.绘制中:
            自身.待重画=True
            return 自身.根
        自身.绘制中=True
        try:
            属性=自身.属性
            窗口=属性['window']
            文档=窗口.document
            def 全量(快照):
                '整份卡片快照'
                return 快照
            状态=属性['useShellCard'](全量)
            是表单=属性['view']!='summary'
            活动=文档.activeElement
            焦点标识=None
            选起=None
            选止=None
            if 活动 is not None and isinstance(活动.id,str) and 活动.id!='':
                焦点标识=活动.id
                if 焦点标识 in (
                    'plugin-config-shell-timeout',
                    'plugin-config-shell-output',
                ):
                    选起=活动['selectionStart']
                    选止=活动['selectionEnd']
            父=None
            if 自身.根 is not None:
                if 是表单 and 自身.上次是表单:
                    跳过离开丢弃(自身.根)
                父=自身.根.parentNode
                自身.根.remove()
                自身.根=None
            elif 'parent' in 属性:
                父=属性['parent']
            if not 是表单:
                说明=文档.createElement('div')
                说明.textContent=中文['description']
                自身.根=说明
                自身.上次是表单=False
            else:
                禁用=not 状态['writable']
                def 改超时(文):
                    '把这次从输入框读到的超时草稿交给暂存'
                    属性['edit']('timeoutMs',文)
                def 复超时():
                    '恢复超时默认'
                    属性['resetField']('timeoutMs')
                def 改上限(文):
                    '把这次从输入框读到的输出上限交给暂存'
                    属性['edit']('maxOutputBytes',文)
                def 复上限():
                    '恢复输出上限默认'
                    属性['resetField']('maxOutputBytes')
                def 画控件(容器):
                    '命令超时与单流输出上限'
                    容器.appendChild(取值字段({
                        'id':'plugin-config-shell-timeout',
                        'label':中文['timeoutMs'],
                        'hint':中文['timeoutMsHint'],
                        'overriddenLabel':中文['overridden'],
                        'resetLabel':中文['reset'],
                        'invalidLabel':中文['invalidNumber'],
                        'numeric':True,
                        'disabled':禁用,
                        **状态['timeoutMs'],
                        'onEdit':改超时,
                        'onReset':复超时,
                        'window':窗口,
                    }).渲染())
                    容器.appendChild(取值字段({
                        'id':'plugin-config-shell-output',
                        'label':中文['maxOutputBytes'],
                        'hint':中文['maxOutputBytesHint'],
                        'overriddenLabel':中文['overridden'],
                        'resetLabel':中文['reset'],
                        'invalidLabel':中文['invalidNumber'],
                        'numeric':True,
                        'disabled':禁用,
                        **状态['maxOutputBytes'],
                        'onEdit':改上限,
                        'onReset':复上限,
                        'window':窗口,
                    }).渲染())
                自身.根=画出设置表单(窗口,{
                    'unavailable':中文['unavailable'],
                    'readOnly':中文['readOnly'],
                    'saveFailed':中文['saveFailed'],
                    'save':中文['save'],
                    'saving':中文['saving'],
                },状态,属性['discard'],属性['save'],画控件)
                自身.上次是表单=True
            if 父 is not None:
                父.appendChild(自身.根)
            if 焦点标识 is not None:
                框=文档.getElementById(焦点标识)
                if 框 is not None:
                    框.focus()
                    if type(选起) in (int,float) and type(选止) in (int,float):
                        框.setSelectionRange(int(选起),int(选止))
            钩=属性['useShellCard']
            if not 自身.已订 and hasattr(钩,'_subscribe') and callable(钩._subscribe):
                def 变更():
                    '快照变了就重画。节点已经不在页面上就退订'
                    if 自身.绘制中:
                        自身.待重画=True
                        return
                    根=自身.根
                    if 根 is None:
                        return
                    if 根.parentNode is None:
                        if 自身.退订 is not None:
                            退=自身.退订
                            自身.退订=None
                            自身.已订=False
                            退()
                        return
                    自身.渲染()
                自身.退订=钩._subscribe(变更)
                自身.已订=True
        finally:
            自身.绘制中=False
        if 自身.待重画:
            自身.待重画=False
            return 自身.渲染()
        return 自身.根
