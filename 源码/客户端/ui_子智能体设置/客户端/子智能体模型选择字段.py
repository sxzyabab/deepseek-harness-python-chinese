import os
from ...ui_对话.异常 import 注入模块样式文件,标样式模块
from ...ui_基础界面组件.开关 import 开关
from .文案 import 中文

__all__=['子智能体模型选择字段']

样式模块='subagentModels'

class 子智能体模型选择字段:
    '默认关闭。打开后按提供方列出可勾选的精确路由'
    def __init__(自身,属性):
        '记下 props'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.节点=[]

    def 更新(自身,属性):
        '换成新的 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '开关、目录状态、按提供方分组的模型和冲突提示'
        for 旧 in list(自身.节点):
            if 旧.parentNode is not None:
                旧.remove()
        自身.节点=[]
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        注入模块样式文件(
            文档,
            '子智能体模型选择字段样式',
            os.path.join(os.path.dirname(__file__),'子智能体模型选择字段.module.css'),
            样式模块,
        )
        状态=属性['state']
        父=属性['parent'] if 'parent' in 属性 else None
        禁用=(not 状态['writable']) or 状态['saving'] is True
        def 造(标签,类名=None):
            '建节点。有类名就挂上本模块'
            节点=文档.createElement(标签)
            if isinstance(类名,str) and 类名!='':
                节点.className=类名
                标样式模块(节点,样式模块)
            return 节点
        def 加上(节点):
            '挂到本节，下次重画先拆掉'
            if 父 is not None:
                父.appendChild(节点)
            自身.节点.append(节点)
            return 节点
        def 画候选(候选):
            '一条模型：勾选、名称、路由。当前没有这条路由时再标不可用'
            行=造('label','model')
            框=文档.createElement('input')
            框.type='checkbox'
            框.checked=候选['selected'] is True
            框.disabled=禁用
            框.setAttribute('data-key',候选['key'])
            def 改勾(事件,键=候选['key']):
                '勾选或取消这一条精确路由'
                属性['toggleModel'](键)
            框.addEventListener('change',改勾)
            行.appendChild(框)
            文=文档.createElement('span')
            名=造('span','modelName')
            名.textContent=候选['modelName']
            路由文=造('span','route')
            路由文.textContent=候选['providerName']+' · '+候选['provider']+'/'+候选['model']
            文.appendChild(名)
            文.appendChild(路由文)
            行.appendChild(文)
            if not 候选['available']:
                缺=造('span','unavailable')
                缺.textContent=中文['subagentModelSelectionUnavailable']
                行.appendChild(缺)
            return 行
        可用组={}
        不可用=[]
        for 候选 in 状态['candidates']:
            if not 候选['available']:
                不可用.append(候选)
                continue
            组=可用组.get(候选['provider'])
            if 组 is None:
                可用组[候选['provider']]={
                    'providerName':候选['providerName'],
                    'candidates':[候选],
                }
            else:
                组['candidates'].append(候选)
        许可=造('div','permission')
        行=造('div','toggleRow')
        签=造('span','toggleLabel')
        签.textContent=中文['subagentModelSelectionToggle']
        行.appendChild(签)
        开关钮=开关({
            'checked':状态['enabled'] is True,
            'label':中文['subagentModelSelectionToggle'],
            'disabled':禁用,
            'onChange':属性['toggleEnabled'],
            'window':窗口,
        }).渲染()
        开关钮.id='plugin-config-subagent-model-toggle'
        行.appendChild(开关钮)
        许可.appendChild(行)
        提示=造('p','hint')
        if 状态['enabled']:
            提示.textContent=中文['subagentModelSelectionChoose']
        else:
            提示.textContent=中文['subagentModelSelectionOff']
        许可.appendChild(提示)
        加上(许可)
        if 状态['enabled']:
            选择=造('div','selection')
            if 状态['catalogStatus']=='loading':
                载=造('p','notice')
                载.setAttribute('role','status')
                载.textContent=中文['subagentModelSelectionLoading']
                选择.appendChild(载)
            if 状态['catalogStatus']=='error':
                错=造('div','catalogError')
                错.setAttribute('role','alert')
                错文=文档.createElement('span')
                错文.textContent=中文['subagentModelSelectionLoadFailed']
                错.appendChild(错文)
                重试=文档.createElement('button')
                重试.type='button'
                重试.id='plugin-config-subagent-model-retry'
                重试.disabled=状态['saving'] is True
                重试.textContent=中文['subagentModelSelectionRetry']
                def 点重试(事件):
                    '再拉一次目录'
                    属性['retryCatalog']()
                重试.addEventListener('click',点重试)
                错.appendChild(重试)
                选择.appendChild(错)
            if 状态['catalogPartial']:
                部分=造('p','notice')
                部分.textContent=中文['subagentModelSelectionPartial']
                选择.appendChild(部分)
            if len(状态['candidates'])>0:
                域=造('fieldset','models')
                题=文档.createElement('legend')
                题.textContent=中文['subagentModelSelectionAllowed']
                域.appendChild(题)
                for 组 in 可用组.values():
                    块=造('div','modelGroup')
                    提供名=造('div','providerName')
                    提供名.textContent=组['providerName']
                    块.appendChild(提供名)
                    for 候选 in 组['candidates']:
                        块.appendChild(画候选(候选))
                    域.appendChild(块)
                if len(不可用)>0:
                    块=造('div','modelGroup')
                    提供名=造('div','providerName')
                    提供名.textContent=中文['subagentModelSelectionUnavailableGroup']
                    块.appendChild(提供名)
                    for 候选 in 不可用:
                        块.appendChild(画候选(候选))
                    域.appendChild(块)
                选择.appendChild(域)
            elif 状态['catalogStatus']=='ready':
                空=造('p','notice')
                空.textContent=中文['subagentModelSelectionEmpty']
                选择.appendChild(空)
            if 状态['invalid']:
                非法=造('p','invalid')
                非法.textContent=中文['subagentModelSelectionRequired']
                选择.appendChild(非法)
            加上(选择)
        if 状态['conflicted']:
            冲突=造('p','conflict')
            冲突.setAttribute('role','status')
            冲突.textContent=中文['subagentModelSelectionConflict']
            加上(冲突)
        return 自身.节点
