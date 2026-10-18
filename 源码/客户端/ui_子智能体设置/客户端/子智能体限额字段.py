import os
from ...ui_对话.异常 import 注入模块样式文件,标样式模块
from ...ui_基础界面组件.icons import 图标信息描边常规
from ...ui_插件设置.字段 import 取值字段
from .文案 import 中文

__all__=['子智能体限额字段']

样式模块='subagentLimits'

class 子智能体限额字段:
    '深度与并行容量。说明收在字段旁的按钮里，表格只在展开时出现'
    def __init__(自身,属性):
        '记下 props。说明开关留在实例上，重画不把它关掉'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.说明开={}

    def 更新(自身,属性):
        '换成新的 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '两列限额。深度说明里有 0 和 1 的对照表'
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        注入模块样式文件(
            文档,
            '子智能体限额字段样式',
            os.path.join(os.path.dirname(__file__),'子智能体限额字段.module.css'),
            样式模块,
        )
        状态=属性['state']
        禁用=(not 状态['writable']) or 状态['saving'] is True
        活动=文档.activeElement
        焦点标识=None
        if 活动 is not None and isinstance(getattr(活动,'id',None),str) and 活动.id!='':
            焦点标识=活动.id
        if 'parent' in 属性 and 属性['parent'] is not None:
            父=属性['parent']
        elif 自身.根 is not None:
            父=自身.根.parentNode
        else:
            父=None
        if 自身.根 is not None:
            自身.根.remove()
            自身.根=None
        def 造(标签,类名=None):
            '建节点。有类名就挂上本模块'
            节点=文档.createElement(标签)
            if isinstance(类名,str) and 类名!='':
                节点.className=类名
                标样式模块(节点,样式模块)
            return 节点
        def 挂说明(列,标识,说明标签,内容):
            '在标签旁放说明按钮。开着时把内容挂到字段末尾'
            开=自身.说明开.get(标识) is True
            头=列.firstElementChild
            签=头.firstElementChild
            钮=文档.createElement('button')
            钮.type='button'
            钮.id=标识+'-help-button'
            钮.setAttribute('aria-label',说明标签)
            钮.setAttribute('aria-expanded','true' if 开 else 'false')
            钮.setAttribute('aria-controls',标识+'-help')
            if 开:
                背景='var(--dsw-alias-bg-layer-4)'
                字色='var(--dsw-alias-label-secondary)'
            else:
                背景='none'
                字色='var(--dsw-alias-label-tertiary)'
            钮.style.cssText=(
                'display:inline-flex;align-items:center;justify-content:center;flex:none;'
                +'width:24px;height:24px;padding:0;border:0;border-radius:var(--dsw-radius-sm);'
                +'background:'+背景+';color:'+字色+';cursor:pointer'
            )
            钮.appendChild(图标信息描边常规({'size':12,'window':窗口}))
            def 点说明(事件,本标识=标识):
                '展开或收起这段说明'
                自身.说明开[本标识]=自身.说明开.get(本标识) is not True
                自身.渲染()
            钮.addEventListener('click',点说明)
            签.appendChild(钮)
            if not 开:
                return
            区=文档.createElement('div')
            区.id=标识+'-help'
            区.setAttribute('role','region')
            区.setAttribute('aria-label',说明标签)
            区.style.cssText='padding:10px 0 0;font-size:12px;line-height:1.6;color:var(--dsw-alias-label-secondary)'
            for 节点 in 内容:
                区.appendChild(节点)
            列.appendChild(区)
        def 改深度(文):
            '把这次读到的深度草稿交给暂存'
            属性['edit']('maxDepth',文)
        def 复深度():
            '恢复深度默认'
            属性['resetField']('maxDepth')
        def 改容量(文):
            '把这次读到的并行上限交给暂存'
            属性['edit']('maxActiveSubagents',文)
        def 复容量():
            '恢复并行上限默认'
            属性['resetField']('maxActiveSubagents')
        列=造('div','limits')
        深度格=造('div','limit')
        深度字段=取值字段({
            'id':'plugin-config-subagent-depth',
            'label':中文['subagentMaxDepth'],
            'overriddenLabel':中文['overridden'],
            'resetLabel':中文['reset'],
            'invalidLabel':中文['subagentDepthInvalid'],
            'numeric':True,
            'disabled':禁用,
            **状态['maxDepth'],
            'onEdit':改深度,
            'onReset':复深度,
            'window':窗口,
        }).渲染()
        深度格.appendChild(深度字段)
        深度说明=文档.createElement('p')
        深度说明.textContent=中文['subagentDepthHelp']
        深度说明.style.cssText='margin:0'
        深度段=[深度说明]
        表=造('table','depthTable')
        表.setAttribute('aria-label',中文['subagentDepthHelpLabel'])
        体=文档.createElement('tbody')
        for 数字,键 in ((0,'subagentDepthZero'),(1,'subagentDepthOne')):
            行=文档.createElement('tr')
            头格=文档.createElement('th')
            头格.setAttribute('scope','row')
            头格.textContent=str(数字)
            格=文档.createElement('td')
            格.textContent=中文[键]
            行.appendChild(头格)
            行.appendChild(格)
            体.appendChild(行)
        表.appendChild(体)
        深度段.append(表)
        覆盖段=文档.createElement('p')
        覆盖段.textContent=中文['subagentDepthOverride']
        覆盖段.style.cssText='margin:0'
        深度段.append(覆盖段)
        挂说明(深度字段,'plugin-config-subagent-depth',中文['subagentDepthHelpLabel'],深度段)
        列.appendChild(深度格)
        容量格=造('div','limit')
        容量字段=取值字段({
            'id':'plugin-config-subagent-capacity',
            'label':中文['subagentMaxActive'],
            'overriddenLabel':中文['overridden'],
            'resetLabel':中文['reset'],
            'invalidLabel':中文['subagentCapacityInvalid'],
            'numeric':True,
            'disabled':禁用,
            **状态['maxActiveSubagents'],
            'onEdit':改容量,
            'onReset':复容量,
            'window':窗口,
        }).渲染()
        容量格.appendChild(容量字段)
        容量段=文档.createElement('p')
        容量段.textContent=中文['subagentCapacityHelp']
        容量段.style.cssText='margin:0'
        挂说明(容量字段,'plugin-config-subagent-capacity',中文['subagentCapacityHelpLabel'],[容量段])
        列.appendChild(容量格)
        自身.根=列
        if 父 is not None:
            父.appendChild(自身.根)
        if 焦点标识 is not None:
            框=文档.getElementById(焦点标识)
            if 框 is not None:
                框.focus()
        return 自身.根
