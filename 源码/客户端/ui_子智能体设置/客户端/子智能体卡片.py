import os
from ...ui_对话.异常 import 注入模块样式文件,标样式模块
from ...ui_插件设置.字段 import 画出设置表单,跳过离开丢弃
from .文案 import 中文
from .子智能体卡片控制器 import 子智能体卡片外壳
from .子智能体限额字段 import 子智能体限额字段
from .子智能体模型选择字段 import 子智能体模型选择字段

__all__=['子智能体卡片']

样式模块='subagentCard'

class 子智能体卡片:
    '限额与模型授权收在同一张设置卡、同一次保存里'
    def __init__(自身,属性):
        '记下渲染器交来的 props，并画出这一页'
        自身.属性=属性
        自身.根=None
        自身.已订=False
        自身.退订=None
        自身.绘制中=False
        自身.待重画=False
        自身.上次是表单=False
        自身.限额件=None
        自身.模型件=None
        自身.渲染()

    def 渲染(自身):
        '摘要是一行说明。其余视图画两节表单。快照变了重画，仍停在表单上时不把重画当成离开页面'
        if 自身.绘制中:
            自身.待重画=True
            return 自身.根
        自身.绘制中=True
        try:
            属性=自身.属性
            窗口=属性['window']
            文档=窗口.document
            注入模块样式文件(
                文档,
                '子智能体卡片样式',
                os.path.join(os.path.dirname(__file__),'子智能体卡片.module.css'),
                样式模块,
            )
            def 全量(快照):
                '整份卡片快照'
                return 快照
            限额=属性['useSubagentLimitsCard'](全量)
            模型=属性['useSubagentModelSelectionCard'](全量)
            是表单=属性['view']!='summary'
            活动=文档.activeElement
            焦点标识=None
            焦点键=None
            选起=None
            选止=None
            if 活动 is not None:
                标识=getattr(活动,'id',None)
                if isinstance(标识,str) and 标识!='':
                    焦点标识=标识
                    if 焦点标识 in (
                        'plugin-config-subagent-depth',
                        'plugin-config-subagent-capacity',
                    ):
                        选起=活动['selectionStart']
                        选止=活动['selectionEnd']
                if getattr(活动,'tagName','') is not None and str(getattr(活动,'tagName','')).upper()=='INPUT':
                    if getattr(活动,'type',None)=='checkbox':
                        焦点键=活动.getAttribute('data-key')
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
                自身.限额件=None
                自身.模型件=None
                说明=文档.createElement('div')
                说明.textContent=中文['subagentDescription']
                自身.根=说明
                自身.上次是表单=False
            else:
                状态=子智能体卡片外壳(限额,模型)
                if not 状态['available']:
                    自身.限额件=None
                    自身.模型件=None
                标题号='subagent-'+str(id(自身))
                def 造(标签,类名):
                    '建节点并挂上本模块类名'
                    节点=文档.createElement(标签)
                    节点.className=类名
                    标样式模块(节点,样式模块)
                    return 节点
                def 画控件(容器):
                    '只画宿主正在服务的节。没在服务的节卸掉，下次再挂时说明是收起的'
                    if 限额['available']:
                        节=造('section','section')
                        节.setAttribute('aria-labelledby',标题号+'-limits')
                        标题=造('h3','heading')
                        标题.id=标题号+'-limits'
                        标题.textContent=中文['subagentLimitsTitle']
                        节.appendChild(标题)
                        限额态=dict(限额)
                        限额态['saving']=状态['saving']
                        限额属性={
                            'state':限额态,
                            'edit':属性['editLimit'],
                            'resetField':属性['resetLimit'],
                            'window':窗口,
                            'parent':节,
                        }
                        if 自身.限额件 is None:
                            自身.限额件=子智能体限额字段(限额属性)
                        else:
                            自身.限额件.更新(限额属性)
                        自身.限额件.渲染()
                        容器.appendChild(节)
                    else:
                        自身.限额件=None
                    if 模型['available']:
                        节=造('section','section')
                        节.setAttribute('aria-labelledby',标题号+'-models')
                        标题=造('h3','heading')
                        标题.id=标题号+'-models'
                        标题.textContent=中文['subagentModelSelectionTitle']
                        节.appendChild(标题)
                        模型态=dict(模型)
                        模型态['saving']=状态['saving']
                        模型属性={
                            'state':模型态,
                            'toggleEnabled':属性['toggleEnabled'],
                            'toggleModel':属性['toggleModel'],
                            'retryCatalog':属性['retryCatalog'],
                            'window':窗口,
                            'parent':节,
                        }
                        if 自身.模型件 is None:
                            自身.模型件=子智能体模型选择字段(模型属性)
                        else:
                            自身.模型件.更新(模型属性)
                        自身.模型件.渲染()
                        容器.appendChild(节)
                    else:
                        自身.模型件=None
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
            def 找回(节点):
                '在新树上按 id 或 data-key 找回刚才的焦点'
                if 节点 is None:
                    return None
                if 焦点标识 is not None and getattr(节点,'id',None)==焦点标识:
                    return 节点
                if 焦点键 is not None and 节点.getAttribute('data-key')==焦点键:
                    return 节点
                子=节点.firstElementChild
                while 子 is not None:
                    命中=找回(子)
                    if 命中 is not None:
                        return 命中
                    子=子.nextElementSibling
                return None
            if 焦点标识 is not None or 焦点键 is not None:
                框=找回(自身.根)
                if 框 is not None:
                    框.focus()
                    if type(选起) in (int,float) and type(选止) in (int,float):
                        框.setSelectionRange(int(选起),int(选止))
            if not 自身.已订:
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
                退订表=[]
                for 钩名 in ('useSubagentLimitsCard','useSubagentModelSelectionCard'):
                    钩=属性[钩名]
                    if hasattr(钩,'_subscribe') and callable(钩._subscribe):
                        退订表.append(钩._subscribe(变更))
                def 全退():
                    '退掉两节快照'
                    for 退 in 退订表:
                        退()
                if len(退订表)>0:
                    自身.退订=全退
                    自身.已订=True
        finally:
            自身.绘制中=False
        if 自身.待重画:
            自身.待重画=False
            return 自身.渲染()
        return 自身.根
