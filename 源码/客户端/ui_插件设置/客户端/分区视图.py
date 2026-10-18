import os
from ...ui_对话.异常 import 注入模块样式文件,模块节点
from ..字段 import 跳过离开丢弃
from .文案 import 中文

__all__=['分区视图']

样式模块='pluginsSettings'
页签计数=0

class 分区视图:
    '内置插件页。一个页签时直接显示，多个页签时已打开的页留着'
    def __init__(自身,属性):
        '记下 props。键齐了就画'
        global 页签计数
        页签计数=页签计数+1
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.活动标识=None
        自身.已访问=set()
        自身.根=None
        自身.页签标识='plugins-tabs-'+str(页签计数)
        自身.钮表={}
        自身.面板表={}
        自身.行标识=None
        自身.模式=None
        自身.已订=False
        自身.退订=None
        if 'window' in 自身.属性 and 'renderSlot' in 自身.属性 and 'useTabs' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '换成新的 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 切换(自身,标识,聚焦):
        '选中页签。已经打开过的页留在文档里'
        自身.活动标识=标识
        if 标识 is not None:
            自身.已访问.add(标识)
        自身.渲染()
        if 聚焦:
            钮=自身.钮表.get(标识)
            if 钮 is not None:
                钮.focus()

    def 摆面板(自身,行表,活动,单页):
        '按页签顺序摆面板。单页不带页签角色。当前页和已打开的页才挂上'
        文档=自身.属性['window'].document
        渲染槽=自身.属性['renderSlot']
        for 行 in 行表:
            标识=行['id']
            if not 单页 and 标识!=活动 and 标识 not in 自身.已访问:
                continue
            面板=自身.面板表.get(标识)
            if 面板 is None:
                面板=模块节点(文档,'div',样式模块,'panel')
                if not 单页:
                    面板.id=自身.页签标识+'-panel-'+str(标识)
                    面板.setAttribute('role','tabpanel')
                    面板.setAttribute('aria-labelledby',自身.页签标识+'-tab-'+str(标识))
                渲染槽(
                    'settings.plugins.tab',
                    {'window':自身.属性['window'],'parent':面板},
                    {'only':标识},
                )
                自身.面板表[标识]=面板
            if not 单页:
                面板.hidden=标识!=活动
            自身.根.appendChild(面板)

    def 渲染(自身):
        '标题、导语，以及空态、单页或页签'
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        注入模块样式文件(
            文档,
            '插件设置分区样式',
            os.path.join(os.path.dirname(__file__),'分区视图.module.css'),
            样式模块,
        )
        def 全量(值):
            '整份页签表'
            return 值
        行表=属性['useTabs'](全量)
        活动=None
        请求=自身.活动标识
        for 行 in 行表:
            if 行['id']==请求:
                活动=请求
                break
        if 活动 is None and len(行表)>0:
            活动=行表[0]['id']
        if 活动 is not None:
            自身.已访问.add(活动)
        数量=len(行表)
        if 数量==0:
            模式='empty'
        elif 数量==1:
            模式='single'
        else:
            模式='tabs'
        标识组=tuple(行['id'] for 行 in 行表)
        if (
            自身.根 is not None and 自身.根.parentNode is not None
            and 自身.模式==模式 and 自身.行标识==标识组
        ):
            if 模式=='tabs':
                for 行 in 行表:
                    标识=行['id']
                    钮=自身.钮表.get(标识)
                    if 钮 is None:
                        continue
                    选中=标识==活动
                    钮.setAttribute('aria-selected','true' if 选中 else 'false')
                    钮.setAttribute('tabindex','0' if 选中 else '-1')
                    if 选中:
                        钮.setAttribute('data-active','true')
                    else:
                        钮.removeAttribute('data-active')
                    标签文=行['label']
                    钮.textContent='' if 标签文 is None else 标签文
            if 模式!='empty':
                自身.摆面板(行表,活动,模式=='single')
            return 自身.根
        父=None
        if 自身.根 is not None:
            父=自身.根.parentNode
            def 卸(节点,跳过):
                '卸掉一棵节点。跳过为真时，表单不把这次删除当成离开页面'
                if 跳过:
                    跳过离开丢弃(节点)
                子=节点.firstElementChild
                while 子 is not None:
                    下一=子.nextElementSibling
                    卸(子,跳过)
                    子=下一
                节点.remove()
            卸(自身.根,True)
        if 父 is None and 'parent' in 属性:
            父=属性['parent']
        自身.钮表={}
        自身.面板表={}
        自身.模式=模式
        自身.行标识=标识组
        根=模块节点(文档,'div',样式模块,'section')
        题=模块节点(文档,'h2',样式模块,'heading')
        题.textContent=中文['title']
        根.appendChild(题)
        导语=模块节点(文档,'p',样式模块,'intro')
        导语.textContent=中文['intro']
        根.appendChild(导语)
        自身.根=根
        if 模式=='empty':
            空=模块节点(文档,'p',样式模块,'empty')
            空.textContent=中文['empty']
            根.appendChild(空)
        elif 模式=='single':
            自身.摆面板(行表,活动,True)
        else:
            条=模块节点(文档,'div',样式模块,'tabs')
            条.setAttribute('role','tablist')
            条.setAttribute('aria-label',中文['tabs'])
            for 序号,行 in enumerate(行表):
                标识=行['id']
                选中=标识==活动
                钮=模块节点(文档,'button',样式模块,'tab')
                钮.type='button'
                钮.setAttribute('role','tab')
                钮.id=自身.页签标识+'-tab-'+str(标识)
                钮.setAttribute('aria-controls',自身.页签标识+'-panel-'+str(标识))
                钮.setAttribute('aria-selected','true' if 选中 else 'false')
                钮.setAttribute('tabindex','0' if 选中 else '-1')
                if 选中:
                    钮.setAttribute('data-active','true')
                标签文=行['label']
                钮.textContent='' if 标签文 is None else 标签文
                def 点页(事件,钉=标识):
                    '切到这一页'
                    自身.切换(钉,False)
                def 按键(事件,下标=序号,行们=tuple(行表)):
                    '左右与首尾移动页签'
                    键=事件.key
                    总数=len(行们)
                    if 键=='ArrowRight':
                        下一=(下标+1)%总数
                    elif 键=='ArrowLeft':
                        下一=(下标-1+总数)%总数
                    elif 键=='Home':
                        下一=0
                    elif 键=='End':
                        下一=总数-1
                    else:
                        return
                    事件.preventDefault()
                    自身.切换(行们[下一]['id'],True)
                钮.addEventListener('click',点页)
                钮.addEventListener('keydown',按键)
                自身.钮表[标识]=钮
                条.appendChild(钮)
            根.appendChild(条)
            自身.摆面板(行表,活动,False)
        if 父 is not None:
            父.appendChild(根)
        if 自身.已订 is not True:
            订=getattr(属性['useTabs'],'_subscribe',None)
            if callable(订):
                def 变更():
                    '页签变了就重画。根已经离开页面就退订'
                    if 自身.根 is None or 自身.根.parentNode is None:
                        退=自身.退订
                        自身.退订=None
                        自身.已订=False
                        if 退 is not None:
                            退()
                        return
                    自身.渲染()
                自身.退订=订(变更)
                自身.已订=True
        return 根

    def __call__(自身,属性=None):
        '再画一次'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
