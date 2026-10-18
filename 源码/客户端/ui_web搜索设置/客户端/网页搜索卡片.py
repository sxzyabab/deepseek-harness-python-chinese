from ...ui_插件设置.字段 import 取值字段,密钥字段,画出设置表单,跳过离开丢弃
from .文案 import 中文

__all__=['网页搜索卡片']

class 网页搜索卡片:
    '网页搜索提供方的设置页：密钥、接口地址、单次请求最多搜索次数'
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
            状态=属性['useWebSearchCard'](全量)
            是表单=属性['view']!='summary'
            活动=文档.activeElement
            焦点标识=None
            选起=None
            选止=None
            if 活动 is not None and isinstance(活动.id,str) and 活动.id!='':
                焦点标识=活动.id
                if 焦点标识 in (
                    'plugin-config-web-search-key',
                    'plugin-config-web-search-endpoint',
                    'plugin-config-web-search-max-uses',
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
                def 改密钥(文):
                    '把这次从输入框读到的密钥草稿交给暂存'
                    属性['edit']('apiKey',文)
                def 改地址(文):
                    '把这次从输入框读到的接口地址交给暂存'
                    属性['edit']('baseURL',文)
                def 复地址():
                    '恢复接口地址默认'
                    属性['resetField']('baseURL')
                def 改次数(文):
                    '把这次从输入框读到的搜索次数交给暂存'
                    属性['edit']('maxUses',文)
                def 复次数():
                    '恢复搜索次数默认'
                    属性['resetField']('maxUses')
                已配=状态['apiKeyConfigured']
                def 画控件(容器):
                    '密钥、接口地址、单次搜索次数'
                    容器.appendChild(密钥字段({
                        'id':'plugin-config-web-search-key',
                        'label':中文['apiKey'],
                        'hint':中文['apiKeyHint'],
                        'disabled':not 状态['apiKeyWritable'],
                        'text':状态['apiKey']['text'],
                        'configured':已配,
                        'stateLabel':中文['apiKeySet'] if 已配 else 中文['apiKeyUnset'],
                        'onEdit':改密钥,
                        'window':窗口,
                    }).渲染())
                    容器.appendChild(取值字段({
                        'id':'plugin-config-web-search-endpoint',
                        'label':中文['baseUrl'],
                        'hint':中文['baseUrlHint'],
                        'overriddenLabel':中文['overridden'],
                        'resetLabel':中文['reset'],
                        'invalidLabel':中文['invalidNumber'],
                        'disabled':禁用,
                        **状态['baseURL'],
                        'onEdit':改地址,
                        'onReset':复地址,
                        'window':窗口,
                    }).渲染())
                    容器.appendChild(取值字段({
                        'id':'plugin-config-web-search-max-uses',
                        'label':中文['maxUses'],
                        'hint':中文['maxUsesHint'],
                        'overriddenLabel':中文['overridden'],
                        'resetLabel':中文['reset'],
                        'invalidLabel':中文['invalidNumber'],
                        'numeric':True,
                        'disabled':禁用,
                        **状态['maxUses'],
                        'onEdit':改次数,
                        'onReset':复次数,
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
            钩=属性['useWebSearchCard']
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
